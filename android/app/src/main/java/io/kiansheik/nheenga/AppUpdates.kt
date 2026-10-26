package io.kiansheik.nheenga

import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URI

data class AppRelease(val versionCode: Int, val versionName: String, val bytes: Long, val sha256: String)

class AppUpdates(private val base: String = BuildConfig.CONTENT_BASE) {
    init {
        val uri = URI(base)
        require(uri.userInfo == null && uri.query == null && uri.fragment == null && uri.path == "/nhe-enga/")
        require(uri.scheme == "https" || (BuildConfig.DEBUG && uri.scheme == "http" && uri.host in setOf("10.0.2.2", "localhost", "127.0.0.1")))
    }

    val downloadUrl: String get() = Integrity.url(base, "downloads/nhe-enga.apk").toString()

    fun latest(): AppRelease? {
        val connection = (Integrity.url(base, "downloads/android.json").openConnection() as HttpURLConnection).apply {
            instanceFollowRedirects = false; connectTimeout = 15_000; readTimeout = 20_000
            setRequestProperty("Accept-Encoding", "identity")
            setRequestProperty("Cache-Control", "no-cache")
        }
        try {
            if (connection.responseCode == 404) return null
            if (connection.responseCode != 200) throw IOException("Não foi possível verificar o aplicativo (HTTP ${connection.responseCode})")
            val output = ByteArrayOutputStream()
            connection.inputStream.use { input ->
                val buffer = ByteArray(8192)
                while (true) {
                    val count = input.read(buffer); if (count < 0) break
                    require(output.size() + count <= 65536) { "Metadados do aplicativo inválidos" }
                    output.write(buffer, 0, count)
                }
            }
            val metadata = JSONObject(output.toString("UTF-8"))
            val version = metadata.getLong("versionCode")
            val name = metadata.getString("versionName")
            val bytes = metadata.getLong("bytes")
            require(version in 1..Int.MAX_VALUE.toLong() && name.isNotBlank() && name.length <= 80)
            require(bytes in 1..15 * 1024 * 1024L && metadata.getString("url") == "nhe-enga.apk")
            return AppRelease(version.toInt(), name, bytes, Integrity.hash(metadata.getString("sha256")))
        } finally { connection.disconnect() }
    }
}