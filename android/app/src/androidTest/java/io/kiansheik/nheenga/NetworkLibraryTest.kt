package io.kiansheik.nheenga

import android.util.Base64
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import okhttp3.mockwebserver.Dispatcher
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okhttp3.mockwebserver.RecordedRequest
import okio.Buffer
import org.json.JSONArray
import org.json.JSONObject
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CopyOnWriteArrayList

@RunWith(AndroidJUnit4::class)
class NetworkLibraryTest {
    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    private val responses = ConcurrentHashMap<String, ByteArray>()
    private val requests = CopyOnWriteArrayList<String>()
    private val server = MockWebServer()
    private lateinit var library: Library

    @Before fun startServer() {
        File(context.filesDir, "library").deleteRecursively()
        context.getSharedPreferences("offline", 0).edit().clear().commit()
        server.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse {
                val path = request.requestUrl!!.encodedPath.removePrefix("/nhe-enga/")
                requests.add(path)
                val bytes = responses[path] ?: return MockResponse().setResponseCode(404)
                return MockResponse().setBody(Buffer().write(bytes))
            }
        }
        server.start()
        library = Library(context, server.url("/nhe-enga/").toString())
    }

    @After fun stopServer() { server.shutdown() }

    private fun pack(id: String, content: Map<String, String>): JSONObject {
        val files = content.map { (path, text) ->
            val bytes = text.toByteArray()
            responses[path] = bytes
            JSONObject().put("path", path).put("sha256", Integrity.sha256(bytes))
                .put("bytes", bytes.size).put("mime", "text/plain")
        }
        val bytes = JSONObject().put("id", id).put("files", JSONArray(files)).toString().toByteArray()
        val hash = Integrity.sha256(bytes)
        val url = "offline/packs/$hash.json"
        responses[url] = bytes
        return JSONObject().put("id", id).put("title", id).put("kind", if (id == "core") "core" else "source")
            .put("url", url).put("sha256", hash).put("bytes", bytes.size)
            .put("downloadBytes", content.values.sumOf { it.toByteArray().size })
    }

    private fun catalog(sequence: Long, vararg packs: JSONObject) {
        val payload = JSONObject().put("schema", 1).put("minShell", 1).put("base", "/nhe-enga/")
            .put("sequence", sequence).put("packs", JSONArray(packs.toList())).toString().toByteArray()
        responses["offline/catalog.json"] = JSONObject().put("payload", Base64.encodeToString(payload, Base64.NO_WRAP))
            .put("signature", "").toString().toByteArray()
    }

    private fun sync() = library.sync({ false }) { _, _, _ -> }

    @Test fun appUpdatesUseValidatedMetadataAndFixedDownloadOrigin() {
        val updates = AppUpdates(server.url("/nhe-enga/").toString())
        assertNull(updates.latest())
        val metadata = JSONObject().put("versionCode", BuildConfig.VERSION_CODE + 1).put("versionName", "0.2.0")
            .put("bytes", 1024).put("sha256", "a".repeat(64)).put("url", "nhe-enga.apk")
        responses["downloads/android.json"] = metadata.toString().toByteArray()
        assertEquals(BuildConfig.VERSION_CODE + 1, updates.latest()!!.versionCode)
        assertEquals(server.url("/nhe-enga/downloads/nhe-enga.apk").toString(), updates.downloadUrl)
        metadata.put("url", "https://untrusted.example/app.apk")
        responses["downloads/android.json"] = metadata.toString().toByteArray()
        assertTrue(runCatching { updates.latest() }.isFailure)
        metadata.put("url", "nhe-enga.apk").put("sha256", "bad")
        responses["downloads/android.json"] = metadata.toString().toByteArray()
        assertTrue(runCatching { updates.latest() }.isFailure)
        responses["downloads/android.json"] = ByteArray(65537) { 32 }
        assertTrue(runCatching { updates.latest() }.isFailure)
    }

    @Test fun updatesPinOpenDocumentsReuseScansAndRollbackWithoutApk() {
        val core = pack("core", mapOf("index.html" to "v1"))
        val source = pack("source-vlb", mapOf("docs/primary_sources/vlb/1.jpg" to "scan"))
        catalog(1, core, source)
        library.configure(setOf("core", "source-vlb"), false, false)
        sync()
        val oldSession = library.session()
        requests.clear()
        val nextCore = pack("core", mapOf("index.html" to "v2"))
        catalog(2, nextCore, source)
        sync()

        assertEquals("v1", library.open("index.html", oldSession)!!.second.readText())
        assertEquals("v2", library.open("index.html", library.session())!!.second.readText())
        assertFalse(requests.contains("docs/primary_sources/vlb/1.jpg"))
        assertEquals(2, library.cachedCatalog()!!.sequence)
        library.rollback()
        assertTrue(library.paused())
        assertEquals("v1", library.open("index.html", library.session())!!.second.readText())
        library.configure(setOf("core", "source-vlb"), false, false)
        sync()
        assertEquals("v2", library.open("index.html", library.session())!!.second.readText())
    }

    @Test fun allSourcesIncludesFutureBooksButIndividualSelectionDoesNot() {
        val core = pack("core", mapOf("index.html" to "core"))
        val source = pack("source-vlb", mapOf("docs/primary_sources/vlb/1.jpg" to "vlb"))
        catalog(1, core, source)
        library.configure(setOf("core", "source-vlb"), false, false)
        sync()
        val future = pack("source-cartas_portiguara", mapOf("docs/primary_sources/cartas_portiguara/1.jpg" to "new book"))
        catalog(2, core, source, future)
        sync()
        assertFalse(library.state().getJSONObject("installed").has("source-cartas_portiguara"))
        library.configure(setOf("core"), true, true)
        sync()
        assertTrue(library.state().getJSONObject("installed").has("source-cartas_portiguara"))
        assertTrue(library.preferences.getBoolean("metered", false))
        catalog(3, core)
        sync()
        assertTrue(library.removablePacks().containsKey("source-cartas_portiguara"))
    }

    @Test fun corruptFilesManifestsMissingFilesAndReplayPreserveInstalledCore() {
        val core = pack("core", mapOf("index.html" to "v1"))
        catalog(10, core)
        sync()
        val nextCore = pack("core", mapOf("index.html" to "v2"))
        catalog(11, nextCore)
        responses["index.html"] = "corrupt".toByteArray()
        assertTrue(runCatching { sync() }.isFailure)
        assertEquals("v1", library.open("index.html", library.session())!!.second.readText())
        responses.remove("index.html")
        assertTrue(runCatching { sync() }.isFailure)
        val broken = pack("core", mapOf("index.html" to "v3"))
        catalog(12, broken)
        responses[broken.getString("url")] = "bad manifest".toByteArray()
        assertTrue(runCatching { sync() }.isFailure)
        catalog(9, core)
        assertTrue(runCatching { library.refreshCatalog() }.isFailure)
        assertEquals(12, library.cachedCatalog()!!.sequence)
        assertEquals("v1", library.open("index.html", library.session())!!.second.readText())
    }

    @Test fun bootstrapActivatesCoreBeforeSourcesAndPauseKeepsCompletedFiles() {
        val core = pack("core", mapOf("index.html" to "core"))
        val source = pack("source-vlb", mapOf("docs/primary_sources/vlb/1.jpg" to "scan"))
        catalog(1, core, source)
        library.configure(setOf("core", "source-vlb"), false, false)
        var observedCore = false
        library.sync({ false }) { title, _, _ -> if (title == "source-vlb") observedCore = library.coreReady() }
        assertTrue(observedCore)
        val updated = pack("core", mapOf("index.html" to "updated", "extra.txt" to "extra"))
        catalog(2, updated, source)
        assertTrue(runCatching {
            library.sync({ false }) { _, _, _ -> library.pause() }
        }.exceptionOrNull() is TransferInterrupted)
        assertTrue(library.paused())
        assertEquals("core", library.open("index.html", library.session())!!.second.readText())
        requests.clear()
        library.configure(setOf("core", "source-vlb"), false, false)
        sync()
        assertFalse(requests.contains("index.html"))
        assertEquals("updated", library.open("index.html", library.session())!!.second.readText())
    }
}