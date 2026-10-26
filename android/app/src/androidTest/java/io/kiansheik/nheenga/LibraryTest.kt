package io.kiansheik.nheenga

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

@RunWith(AndroidJUnit4::class)
class LibraryTest {
    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    private val library = Library.get(context)
    private val root = File(context.filesDir, "library")

    @Before fun resetLibrary() {
        library.pause()
        root.walkTopDown().filter { it.isFile }.forEach { it.delete() }
        library.preferences.edit().clear().commit()
    }

    private fun asset(path: String, content: String): JSONObject {
        val bytes = content.toByteArray()
        val hash = Integrity.sha256(bytes)
        File(root, "blobs/$hash").writeBytes(bytes)
        return JSONObject().put("path", path).put("sha256", hash)
            .put("bytes", bytes.size).put("mime", "text/plain")
    }

    private fun pack(id: String, files: List<JSONObject>): JSONObject {
        val bytes = JSONObject().put("id", id).put("files", JSONArray(files)).toString().toByteArray()
        val hash = Integrity.sha256(bytes)
        File(root, "manifests/$hash.json").writeBytes(bytes)
        return JSONObject().put("id", id).put("title", id).put("kind", if (id == "core") "core" else "source")
            .put("sha256", hash).put("bytes", bytes.size).put("downloadBytes", 0)
            .put("url", "offline/packs/$hash.json")
    }

    private fun seed(installed: List<JSONObject>, saved: List<JSONObject> = emptyList(), previous: List<JSONObject> = emptyList()) {
        fun packs(values: List<JSONObject>) = JSONObject().apply { values.forEach { put(it.getString("id"), it) } }
        val state = JSONObject().put("installed", packs(installed)).put("previous", packs(previous))
            .put("selected", JSONArray(installed.map { it.getString("id") })).put("allSources", false)
            .put("saved", JSONObject().apply { saved.forEach { put(it.getString("path"), it) } })
        File(root, "state.json").writeText(state.toString())
    }

    @Test fun removingSavedOnlySourcePreservesCoreAndOtherPages() {
        val core = asset("index.html", "core")
        val saved = asset("docs/primary_sources/cartas_portiguara/1.jpg", "saved page")
        val other = asset("docs/primary_sources/vlb/1.jpg", "other page")
        seed(listOf(pack("core", listOf(core))), listOf(saved, other))
        assertEquals(setOf("source-cartas_portiguara", "source-vlb"), library.removablePacks().keys)

        library.remove("source-cartas_portiguara")

        assertFalse(library.state().getJSONObject("saved").has(saved.getString("path")))
        assertFalse(File(root, "blobs/${saved.getString("sha256")}").exists())
        assertEquals(setOf("source-vlb"), library.removablePacks().keys)
        assertTrue(library.coreReady())
        assertEquals("core", library.open("index.html", library.session())!!.second.readText())
        assertTrue(library.state().getJSONObject("saved").has(other.getString("path")))
    }

    @Test fun removingRetiredPackPreservesSharedBlobsAndRollbackCore() {
        val core = asset("index.html", "core")
        val shared = asset("docs/primary_sources/retired/1.jpg", "core")
        val book = pack("source-retired", listOf(shared))
        val corePack = pack("core", listOf(core))
        seed(listOf(corePack, book), listOf(shared), listOf(corePack, book))
        assertEquals(setOf("source-retired"), library.removablePacks().keys)

        library.remove("source-retired")

        assertFalse(library.state().getJSONObject("installed").has("source-retired"))
        assertFalse(library.state().getJSONObject("previous").has("source-retired"))
        assertTrue(File(root, "blobs/${core.getString("sha256")}").exists())
        library.rollback()
        assertTrue(library.coreReady())
        assertTrue(library.paused())
    }

    @Test fun installedLibraryOpensWithoutCatalogOrNetwork() {
        val core = asset("index.html", "offline core")
        seed(listOf(pack("core", listOf(core))))
        assertNull(library.cachedCatalog())
        assertEquals("offline core", library.open("index.html", library.session())!!.second.readText())
        assertTrue(runCatching { library.remove("core") }.isFailure)
        assertTrue(library.coreReady())
    }
}