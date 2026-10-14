import io.kiansheik.nheenga.*
import com.sun.net.httpserver.HttpServer
import java.net.InetSocketAddress
import java.nio.file.Files
import java.security.KeyPairGenerator
import java.security.Signature
import java.util.concurrent.atomic.AtomicInteger

fun main() {
    val directory = Files.createTempDirectory("nhe-native-test").toFile()
    val server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
    val requests = AtomicInteger(); val ranges = AtomicInteger()
    val content = ByteArray(512 * 1024) { (it % 251).toByte() }
    var badRange = false
    server.createContext("/nhe-enga/") { exchange ->
        requests.incrementAndGet()
        val range = exchange.requestHeaders.getFirst("Range")
        val start = range?.substringAfter("bytes=")?.substringBefore('-')?.toInt() ?: 0
        val rangeSupported = !exchange.requestURI.path.endsWith("ignore-range")
        val offset = if (rangeSupported) start else 0
        if (range != null && rangeSupported) {
            ranges.incrementAndGet()
            exchange.responseHeaders.add("Content-Range", "bytes ${if (badRange) offset + 1 else offset}-${content.size - 1}/${content.size}")
        }
        exchange.sendResponseHeaders(if (offset > 0) 206 else 200, (content.size - offset).toLong())
        try { exchange.responseBody.use { it.write(content, offset, content.size - offset) } } catch (_: Exception) {}
        exchange.close()
    }
    server.start()
    try {
        val files = VerifiedFiles(directory, "http://127.0.0.1:${server.address.port}/nhe-enga/")
        val a = Asset("asset", Integrity.sha256(content), content.size.toLong(), "application/octet-stream")
        check(files.download(a).readBytes().contentEquals(content))
        val count = requests.get(); files.download(a); check(requests.get() == count) { "Unchanged blob was re-downloaded" }
        println("PASS verified streaming + hash deduplication")
        files.file(a).delete()
        var stop = false
        try { files.download(a, { stop }) { if (it >= 65536) stop = true }; error("Expected interruption") } catch (_: TransferInterrupted) {}
        check(directory.resolve(a.sha256 + ".part").length() in 1 until a.bytes)
        check(files.download(a).readBytes().contentEquals(content)); check(ranges.get() > 0)
        println("PASS partial download survives interruption and resumes with Range")
        files.file(a).delete()
        directory.resolve(a.sha256 + ".part").writeBytes(content.copyOf(4096))
        check(files.download(a.copy(path = "ignore-range")).readBytes().contentEquals(content))
        println("PASS server ignoring Range restarts only the current file")
        files.file(a).delete(); directory.resolve(a.sha256 + ".part").writeBytes(content.copyOf(4096)); badRange = true
        check(runCatching { files.download(a) }.isFailure); check(!files.present(a)); badRange = false
        files.download(a)
        val invalid = a.copy(sha256 = "0".repeat(64))
        check(runCatching { files.download(invalid) }.isFailure)
        check(!files.present(invalid) && files.present(a))
        println("PASS invalid ranges and hashes rejected; previous verified content retained")
        for (p in listOf("../secret", "/absolute", "a%2fb", "a\\b", "a/./b", "a//b")) check(runCatching { Integrity.path(p) }.isFailure)
        val pair = KeyPairGenerator.getInstance("RSA").apply { initialize(2048) }.generateKeyPair()
        val sig = Signature.getInstance("SHA256withRSA").run { initSign(pair.private); update(content); sign() }
        check(Integrity.signature(content, sig, pair.public.encoded))
        check(!Integrity.signature(byteArrayOf(0), sig, pair.public.encoded))
        println("PASS path validation + RSA manifest signature/tamper checks")
    } finally { server.stop(0); directory.deleteRecursively() }
}
