# Nhe'enga Android shell

See [offline architecture/build instructions](../offline/README.md) and the
[local-agent emulator handoff](../docs/agent/session-handoffs/2026-10-14-android-offline.md).

From the repository root: `make apk`. JDK 17+, Android SDK platform 35 and build-tools
35.0.0 are required. Gradle is bootstrapped with a pinned distribution checksum.
The APK contains no site content; the first successful download is required for
lookup. Debug and test-signed release builds, lint, Android 16 device regressions,
and real-content offline WebView checks pass. See the
[validation report](../docs/agent/session-handoffs/2026-10-15-android-validation.md)
for evidence and remaining production release gates.
