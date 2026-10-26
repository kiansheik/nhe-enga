package io.kiansheik.nheenga

import java.io.File
import java.io.FileOutputStream
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.security.KeyFactory
import java.security.MessageDigest
import java.security.Signature
import java.security.spec.X509EncodedKeySpec
import java.util.concurrent.ConcurrentHashMap

/** Pure JVM code: shared by the Android downloader and host-side regression tests. */
object Integrity {
    fun path(value: String): String {
        require(value.isNotEmpty() && !value.startsWith('/') &&
            value.none { it in "\\%?#\u0000" } &&
            value.split('/').none { it.isEmpty() || it == "." || it == ".." }) { "Unsafe path" }
        return value
    }
    fun hash(value: String): String {
        require(value.matches(Regex("[a-f0-9]{64}"))) { "Invalid SHA-256" }
        return value
    }
    fun sha256(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256")
        .digest(bytes).joinToString("") { "%02x".format(it.toInt() and 255) }
    fun sha256(file: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        file.inputStream().use { input ->
            val buffer = ByteArray(64 * 1024)
            while (true) { val n = input.read(buffer); if (n < 0) break; digest.update(buffer, 0, n) }
        }
        return digest.digest().joinToString("") { "%02x".format(it.toInt() and 255) }
    }
    fun signature(payload: ByteArray, signature: ByteArray, publicKey: ByteArray): Boolean {
        val key = KeyFactory.getInstance("RSA").generatePublic(X509EncodedKeySpec(publicKey))
        return Signature.getInstance("SHA256withRSA").run { initVerify(key); update(payload); verify(signature) }
    }
    fun url(base: String, path: String): URL = URL(base + path(path).split('/').joinToString("/") {
        URLEncoder.encode(it, "UTF-8").replace("+", "%20")
    })
}

data class Asset(val path: String, val sha256: String, val bytes: Long, val mime: String) {
    init {
        Integrity.path(path); Integrity.hash(sha256)
        require(bytes in 0..104_857_600L) { "Asset exceeds the static host's file limit" }
        require(!mime.contains('\r') && !mime.contains('\n'))
    }
}

class TransferInterrupted : IOException("Download pausado; arquivos concluídos foram mantidos")

/** Content-addressed, streaming, resumable files. Never deletes a working blob. */
class VerifiedFiles(private val directory: File, private val base: String) {
    private val locks = ConcurrentHashMap<String, Any>()
    init { directory.mkdirs() }
    fun file(asset: Asset) = File(directory, asset.sha256)
    fun present(asset: Asset) = file(asset).isFile && file(asset).length() == asset.bytes

    fun download(asset: Asset, stop: () -> Boolean = { false }, progress: (Long) -> Unit = {}): File =
        synchronized(locks.getOrPut(asset.sha256) { Any() }) {
            val target = file(asset)
            if (present(asset)) return@synchronized target
            val partial = File(directory, asset.sha256 + ".part")
            if (partial.length() > asset.bytes) partial.delete()
            if (partial.isFile && partial.length() == asset.bytes && Integrity.sha256(partial) == asset.sha256) {
                check(partial.renameTo(target)) { "Cannot commit completed file" }
                return@synchronized target
            }
            if (directory.usableSpace < asset.bytes - partial.length() + 8 * 1024 * 1024) {
                throw IOException("Sem espaço livre. Remova um pacote ou libere armazenamento; sua biblioteca foi preservada.")
            }
            if (stop()) throw TransferInterrupted()
            val connection = (Integrity.url(base, asset.path).openConnection() as HttpURLConnection).apply {
                instanceFollowRedirects = false; connectTimeout = 15_000; readTimeout = 20_000
                setRequestProperty("Accept-Encoding", "identity")
                if (partial.length() > 0) setRequestProperty("Range", "bytes=${partial.length()}-")
            }
            try {
                val code = connection.responseCode
                val offset = partial.length()
                val append = code == 206 && offset > 0
                if (code != 200 && !append) {
                    // A stale complete partial is retried from zero next time.
                    if (code == 416) partial.delete()
                    throw IOException("HTTP $code: ${asset.path}")
                }
                if (append) {
                    val range = connection.getHeaderField("Content-Range") ?: ""
                    val expected = Regex("bytes $offset-([0-9]+)/${asset.bytes}").matchEntire(range)
                    if (expected == null || expected.groupValues[1].toLong() != asset.bytes - 1) {
                        partial.delete(); throw IOException("Resposta parcial inválida")
                    }
                }
                var written = if (append) offset else 0L
                connection.inputStream.use { input ->
                    FileOutputStream(partial, append).use { output ->
                        val buffer = ByteArray(64 * 1024)
                        while (true) {
                            if (stop()) throw TransferInterrupted()
                            val n = input.read(buffer); if (n < 0) break
                            if (written + n > asset.bytes) { partial.delete(); throw IOException("Arquivo maior que o manifesto") }
                            output.write(buffer, 0, n); written += n; progress(written)
                        }
                        output.fd.sync()
                    }
                }
                if (partial.length() != asset.bytes) throw IOException("Download incompleto: ${asset.path}")
                if (Integrity.sha256(partial) != asset.sha256) {
                    partial.delete(); throw IOException("SHA-256 incorreto: ${asset.path}")
                }
                check(partial.renameTo(target)) { "Cannot activate verified file" }
                target
            } finally { connection.disconnect() }
        }
}
