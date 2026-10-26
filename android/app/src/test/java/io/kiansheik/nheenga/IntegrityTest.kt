package io.kiansheik.nheenga

import org.junit.Assert.*
import org.junit.Test

class IntegrityTest {
    @Test fun pathsNeverEscapeTheirOrigin() {
        for (value in listOf("../secret", "/root", "a//b", "a/./b", "a%2fb", "a?b", "a\\b")) {
            assertTrue(value, runCatching { Integrity.path(value) }.isFailure)
        }
        assertEquals("docs/primary_sources/vlb/1.jpg", Integrity.path("docs/primary_sources/vlb/1.jpg"))
    }
    @Test fun sha256UsesActualBytes() {
        assertEquals("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", Integrity.sha256(byteArrayOf()))
    }
    @Test fun pathsAreUrlEncodedButCannotChangeAuthority() {
        assertEquals("https://example.org/nhe-enga/fonte%20um/1.jpg", Integrity.url("https://example.org/nhe-enga/", "fonte um/1.jpg").toString())
    }
}
