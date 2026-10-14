package io.kiansheik.nheenga

import android.content.Context
import android.util.AtomicFile
import android.util.Base64
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URI

private fun JSONArray.objects(): List<JSONObject> = (0 until length()).map { getJSONObject(it) }
private fun JSONArray.strings(): List<String> = (0 until length()).map { getString(it) }
private fun JSONObject.keysList(): List<String> = keys().asSequence().toList()
private fun Asset.json() = JSONObject().put("path", path).put("sha256", sha256).put("bytes", bytes).put("mime", mime)
private fun asset(j: JSONObject) = Asset(j.getString("path"), j.getString("sha256"), j.getLong("bytes"), j.getString("mime"))

data class Pack(val id: String, val title: String, val kind: String, val descriptor: JSONObject) {
    val hash: String get() = descriptor.getString("sha256")
    val bytes: Long get() = descriptor.getLong("downloadBytes")
}
data class Catalog(val sequence: Long, val packs: List<Pack>)
data class LibrarySession(val catalog: Catalog?, val files: MutableMap<String, Asset>)

/** One instance per process. Network IO never holds the state lock. */
class Library private constructor(context: Context) {
    val context: Context = context.applicationContext
    private val root = File(this.context.filesDir, "library").apply { mkdirs() }
    private val manifests = File(root, "manifests").apply { mkdirs() }
    private val stateFile = AtomicFile(File(root, "state.json"))
    private val catalogFile = AtomicFile(File(root, "catalog.json"))
    private val stateLock = Any()
    val preferences = this.context.getSharedPreferences("offline", Context.MODE_PRIVATE)
    private val base = BuildConfig.CONTENT_BASE
    private val blobs = VerifiedFiles(File(root, "blobs"), base)
    private val catalogLock = Any()
    @Volatile private var activeSession: LibrarySession? = null

    init {
        val uri = URI(base)
        require(uri.userInfo == null && uri.query == null && uri.fragment == null && uri.path == "/nhe-enga/")
        require(uri.scheme == "https" || (BuildConfig.DEBUG && uri.scheme == "http" && uri.host in setOf("10.0.2.2", "localhost", "127.0.0.1")))
    }
    private fun initial() = JSONObject().put("installed", JSONObject()).put("saved", JSONObject())
        .put("selected", JSONArray(listOf("core"))).put("allSources", false)
    fun state(): JSONObject = synchronized(stateLock) {
        if (!stateFile.baseFile.exists() && !File(stateFile.baseFile.path + ".bak").exists()) return@synchronized initial()
        JSONObject(String(stateFile.openRead().use { it.readBytes() }, Charsets.UTF_8))
    }
    private fun atomic(file: AtomicFile, bytes: ByteArray) {
        val stream = file.startWrite()
        try { stream.write(bytes); file.finishWrite(stream) } catch (e: Exception) { file.failWrite(stream); throw e }
    }
    private fun mutate(change: (JSONObject) -> Unit) = synchronized(stateLock) {
        val s = state(); change(s); atomic(stateFile, s.toString().toByteArray(Charsets.UTF_8))
    }
    fun paused() = preferences.getBoolean("paused", false)
    fun status(text: String) { preferences.edit().putString("status", text).apply() }
    fun status() = preferences.getString("status", "") ?: ""
    fun coreReady() = state().getJSONObject("installed").has("core")
    fun configure(ids: Set<String>, allSources: Boolean, metered: Boolean) {
        preferences.edit().putLong("generation", preferences.getLong("generation", 0) + 1).apply()
        mutate { it.put("selected", JSONArray((ids + "core").sorted())).put("allSources", allSources) }
        preferences.edit().putBoolean("metered", metered).putBoolean("paused", false).apply()
    }
    fun pause() { preferences.edit().putBoolean("paused", true).apply(); status("Downloads pausados") }

    private fun decodeCatalog(bytes: ByteArray): Catalog {
        require(bytes.size <= 1024 * 1024) { "Catalog too large" }
        val envelope = JSONObject(String(bytes, Charsets.UTF_8))
        val payload = Base64.decode(envelope.getString("payload"), Base64.DEFAULT)
        val signature = Base64.decode(envelope.getString("signature"), Base64.DEFAULT)
        if (!(BuildConfig.DEBUG && signature.isEmpty() && BuildConfig.CONTENT_PUBLIC_KEY.isEmpty())) {
            require(BuildConfig.CONTENT_PUBLIC_KEY.isNotEmpty() && Integrity.signature(payload, signature,
                Base64.decode(BuildConfig.CONTENT_PUBLIC_KEY, Base64.DEFAULT))) { "Assinatura do catálogo inválida" }
        }
        val j = JSONObject(String(payload, Charsets.UTF_8))
        require(j.getInt("schema") == 1 && j.getInt("minShell") <= BuildConfig.SHELL_PROTOCOL && j.getString("base") == "/nhe-enga/") { "Atualize o aplicativo para usar este catálogo" }
        val sequence = j.getLong("sequence")
        require(sequence > 0) { "Sequência inválida" }
        val packs = j.getJSONArray("packs").objects().map {
            Integrity.path(it.getString("url")); Integrity.hash(it.getString("sha256"))
            require(it.getString("id").matches(Regex("[a-z0-9_-]+")))
            require(it.getLong("bytes") in 1..8_388_608L)
            require(it.getLong("downloadBytes") >= 0)
            Pack(it.getString("id"), it.getString("title"), it.getString("kind"), it)
        }
        require(packs.map { it.id }.distinct().size == packs.size && packs.any { it.id == "core" })
        return Catalog(sequence, packs)
    }
    fun cachedCatalog(): Catalog? = synchronized(catalogLock) {
        try { decodeCatalog(catalogFile.openRead().use { it.readBytes() }) } catch (_: Exception) { null }
    }
    fun refreshCatalog(): Catalog = synchronized(catalogLock) {
        val old = cachedCatalog()
        val connection = (Integrity.url(base, "offline/catalog.json").openConnection() as HttpURLConnection).apply {
            instanceFollowRedirects = false; connectTimeout = 15_000; readTimeout = 20_000
            setRequestProperty("Accept-Encoding", "identity")
            if (old != null) preferences.getString("etag", null)?.let { setRequestProperty("If-None-Match", it) }
        }
        try {
            if (connection.responseCode == 304 && old != null) return@synchronized old
            if (connection.responseCode != 200) throw IOException("Catálogo indisponível (HTTP ${connection.responseCode})")
            val bytes = connection.inputStream.use { input ->
                val output = java.io.ByteArrayOutputStream(); val buffer = ByteArray(8192)
                while (true) { val n = input.read(buffer); if (n < 0) break; if (output.size() + n > 1024 * 1024) throw IOException("Catálogo muito grande"); output.write(buffer, 0, n) }
                output.toByteArray()
            }
            val c = decodeCatalog(bytes)
            require(c.sequence >= maxOf(preferences.getLong("sequence", 0), old?.sequence ?: 0L)) { "Catálogo antigo recusado" }
            atomic(catalogFile, bytes)
            preferences.edit().putLong("sequence", c.sequence).putString("etag", connection.getHeaderField("ETag")).apply()
            c
        } finally { connection.disconnect() }
    }
    private fun manifest(pack: Pack, network: Boolean = true): List<Asset> {
        val file = File(manifests, pack.hash + ".json")
        val size = pack.descriptor.getLong("bytes")
        if (!file.isFile || file.length() != size || Integrity.sha256(file) != pack.hash) {
            if (!network) throw IOException("Manifesto local indisponível")
            val downloaded = blobs.download(Asset(pack.descriptor.getString("url"), pack.hash, size, "application/json"))
            val temporary = File(manifests, pack.hash + ".tmp")
            downloaded.copyTo(temporary, overwrite = true)
            check(temporary.renameTo(file))
        }
        val j = JSONObject(file.readText())
        require(j.getString("id") == pack.id)
        val files = j.getJSONArray("files").objects().map(::asset)
        require(files.map { it.path }.distinct().size == files.size) { "Duplicate manifest paths" }
        return files
    }
    private fun pack(j: JSONObject) = Pack(j.getString("id"), j.getString("title"), j.getString("kind"), j)
    fun session(): LibrarySession {
        val s = state(); val files = mutableMapOf<String, Asset>()
        val saved = s.getJSONObject("saved")
        for (path in saved.keysList()) files[path] = asset(saved.getJSONObject(path))
        val installed = s.getJSONObject("installed")
        for (id in installed.keysList()) for (f in manifest(pack(installed.getJSONObject(id)), false)) files[f.path] = f
        return LibrarySession(cachedCatalog(), files).also { activeSession = it }
    }
    private fun find(path: String, session: LibrarySession): Asset? {
        synchronized(session.files) { session.files[path]?.let { return it } }
        val c = session.catalog ?: return null
        val book = Regex("^docs/primary_sources/([^/]+)/").find(path)?.groupValues?.get(1)
        val candidates = if (book == null) c.packs.filter { it.kind != "source" }
            else c.packs.filter { it.id == "source-$book" || it.id == "core" }
        for (p in candidates) {
            val found = manifest(p).firstOrNull { it.path == path }
            if (found != null) return found
        }
        return null
    }
    fun open(path: String, session: LibrarySession): Pair<Asset, File>? {
        Integrity.path(path)
        val f = find(path, session) ?: return null
        val file = blobs.download(f) // Viewing one page is explicit, even on mobile data.
        synchronized(session.files) { session.files[path] = f }
        mutate { s -> val saved = s.getJSONObject("saved"); if (!saved.has(path)) saved.put(path, f.json()) }
        return f to file
    }
    /** All updated subscribed packs commit together; bootstrap core is an exception. */
    @Synchronized
    fun sync(stop: () -> Boolean, progress: (String, Long, Long) -> Unit) {
        if (paused()) return
        val generation = preferences.getLong("generation", 0)
        fun interrupted() = stop() || paused() || preferences.getLong("generation", 0) != generation
        val c = refreshCatalog(); val before = state(); val installed = before.getJSONObject("installed")
        val selected = before.getJSONArray("selected").strings().toSet() + "core"
        val subscribed = c.packs.filter { it.id in selected || (before.optBoolean("allSources") && it.kind == "source") }
            .sortedBy { if (it.id == "core") "" else it.id }
        val next = JSONObject(installed.toString())
        for (p in subscribed) {
            val files = manifest(p); var done = 0L
            for (f in files) {
                if (interrupted()) throw TransferInterrupted()
                blobs.download(f, { interrupted() }) { current -> progress(p.title, done + current, p.bytes) }
                done += f.bytes; progress(p.title, done, p.bytes)
            }
            next.put(p.id, p.descriptor)
            if (p.id == "core" && !installed.has("core")) {
                mutate { it.getJSONObject("installed").put("core", p.descriptor) }
            }
        }
        val saved = JSONObject(before.getJSONObject("saved").toString())
        if (saved.length() > 0) for (p in c.packs.filter { candidate ->
            candidate.kind != "source" || saved.keysList().any { it.startsWith("docs/primary_sources/${candidate.id.removePrefix("source-")}/") }
        }) {
            for (f in manifest(p)) if (saved.has(f.path) && saved.getJSONObject(f.path).getString("sha256") != f.sha256) {
                blobs.download(f, { interrupted() }); saved.put(f.path, f.json())
            }
        }
        if (interrupted()) throw TransferInterrupted()
        mutate { s ->
            // Preserve pages viewed while synchronization was in progress.
            val merged = s.getJSONObject("saved")
            for (path in saved.keysList()) merged.put(path, saved.getJSONObject(path))
            val current = s.getJSONObject("installed")
            if (current.toString() != next.toString()) s.put("previous", JSONObject(current.toString()))
            s.put("installed", next).put("saved", merged)
        }
        preferences.edit().putLong("lastCheck", System.currentTimeMillis()).apply()
        status("Downloads concluídos. Reabra os dicionários para aplicar as atualizações.")
    }
    @Synchronized
    fun rollback() {
        mutate { s ->
            val previous = s.optJSONObject("previous") ?: throw IOException("Não há uma versão anterior")
            require(previous.has("core"))
            val current = s.getJSONObject("installed"); s.put("installed", previous).put("previous", current)
        }
        pause(); status("Versão anterior restaurada; atualizações pausadas")
    }
    /** Explicit removal; never automatic eviction of selected/viewed content. */
    @Synchronized
    fun remove(id: String) {
        require(id != "core")
        val old = state().getJSONObject("installed").optJSONObject(id)
        val paths = if (old == null) emptySet() else manifest(pack(old), false).map { it.path }.toSet()
        mutate { s ->
            s.getJSONObject("installed").remove(id); s.optJSONObject("previous")?.remove(id)
            s.put("selected", JSONArray(s.getJSONArray("selected").strings().filter { it != id })).put("allSources", false)
            for (path in paths) s.getJSONObject("saved").remove(path)
        }
        // Settings UI closes the WebView before removal; its file streams close.
        activeSession = null
        val keep = mutableSetOf<String>(); val s = state()
        for (group in listOf("installed", "previous")) {
            val objectMap = s.optJSONObject(group) ?: continue
            for (packId in objectMap.keysList()) for (f in manifest(pack(objectMap.getJSONObject(packId)), false)) keep.add(f.sha256)
        }
        val saved = s.getJSONObject("saved")
        for (path in saved.keysList()) keep.add(saved.getJSONObject(path).getString("sha256"))
        File(root, "blobs").listFiles()?.filter { it.name !in keep }?.forEach { it.delete() }
        status("Pacote removido")
    }
    fun usedBytes(): Long = root.walkTopDown().filter { it.isFile }.sumOf { it.length() }
    companion object {
        @Volatile private var instance: Library? = null
        fun get(context: Context): Library = instance ?: synchronized(this) {
            instance ?: Library(context).also { instance = it }
        }
    }
}
