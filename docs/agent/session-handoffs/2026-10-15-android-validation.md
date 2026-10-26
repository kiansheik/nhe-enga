# Android/offline validation, 2026-10-15

Original validation status: Android 16 real-content acceptance passed before
production approval. The user subsequently authorized the first signed production
release; see the publication addendum below. Remaining stress/compatibility gaps
listed here are not claims of completed coverage.

## Environment

- macOS arm64; Homebrew JDK 21; Gradle 8.11.1; SDK/build-tools 35/35.0.0.
- Emulator 37.2.12, Android 16/API 36, Google APIs arm64.
- WebView 133.0.6943.137; Playwright 1.55.0 / Chromium 140.0.7339.16.
- Explicit emulator serial: `emulator-5554`. A connected physical phone was not
  installed, reset, or tested. The smoke harness rejects physical devices.
- Python 3.14's Gradle-download TLS check initially needed `SSL_CERT_FILE` set to
  the installed Certifi CA bundle. TLS verification was never disabled.
- Android Studio's JDK 25 failed Gradle/Kotlin initialization; JDK 21 works.

## Changes and regressions

- Saved-only source pages and retired/previous-only packs can be removed from
  native settings, including without a cached catalog. Preserve core, unrelated
  pages, shared blobs, and rollback core. API-23 lint compatibility retained.
- Browser downloads now expose saved-only and retired sources and clear their
  saved paths on removal. Real Chromium reproduces and verifies the saved-only
  case through the download UI.
- Sentence-builder explicitly inflates its gzip dictionary with Pako. The real
  WebView previously raised a gzip-as-JSON parse error; decoded dictionary data
  and Python execution now pass online and after offline cold launch.
- Browser fixture responses use `Cache-Control: no-store`: second-resolution
  Last-Modified caching otherwise hid rapid synthetic catalog revisions.
- Added seven on-device library/network regressions and an emulator-only native
  UI/WebView harness. Test data and screenshots remain ignored under `dist/`.
- Morphology, lexicon, source pagination, corpus ground truth, and the user's
  pre-existing dictionary/annotation changes were not modified by this work.

## Reproducible checks

Set `JAVA_HOME` to JDK 17/21, `ANDROID_HOME` to the SDK, and ensure Node/adb are
on PATH. Install Python Playwright 1.55.0 and Chromium; Kotlin is needed for the
host downloader harness.

```sh
make offline-test
make offline-native-test
make offline-browser-test
ANDROID_SERIAL=emulator-5554 ./android/gradlew --no-watch-fs --rerun-tasks \
  :app:connectedDebugAndroidTest :app:testDebugUnitTest :app:lintDebug
make offline-android-test
OFFLINE_SKIP_APK=1 make pages-build
OFFLINE_ANDROID_ARGS='--site .pages-build --tools --serial emulator-5554' make offline-android-test
```

`OFFLINE_SKIP_APK=1` is a local preview flag, never a deployment instruction.
The Android smoke clears only the selected emulator's debug package, changes its
network settings temporarily, restores those settings, and runs a local server.

## Evidence

| Gate | Result |
| --- | --- |
| Eight Python catalog/preparation/signature tests | PASS |
| Node service-worker protocol scenarios | PASS |
| Real Chromium cold offline/query route/selective pack/update/corruption/removal | PASS |
| Host JVM verified transfer/Range interruption/resume/ignored Range/hash/RSA checks | PASS |
| Android debug assembly, JVM unit tests, debug lint | PASS; warnings remain |
| Seven Android instrumentation tests | PASS; final run forced all tasks to execute |
| Fresh full Pages/VuePress/vendor/offline build | PASS, nine packs; unsigned local preview |
| Fresh offline native setup | PASS, no core/no crash, native first-download state |
| Real core-only download | PASS, no source images downloaded in bulk |
| Selective real Cartas/tools installation | PASS; no unselected installed books |
| Three real dictionary searches | PASS, actual result cards online and offline |
| Real quiz | PASS, loaded conjugations and a three-part correct answer |
| Cartas named image; VLB viewed-only page/zoom | PASS online and offline |
| Synthetic viewed-only persistence/unseen-page missing state | PASS |
| Local Pyodide/stdlib/micropip/Tupi wheel plus decoded tools dictionary | PASS online and offline |
| Airplane-mode force-stop/relaunch | PASS; all tested content, zero local-server requests |
| Network catalog updates/pinned session/unchanged scan reuse/rollback/resume | PASS on-device |
| Individual vs all-source future-book subscription; retired pack retention | PASS on-device |
| Pause/completed-file reuse/corrupt file/corrupt manifest/404/replay safety | PASS on-device |
| Signed, shrunk release assembly, release lint, apksigner verification | PASS with temporary external test-only keys |
| Release shell size | 313,695 bytes; 73 ZIP entries; no bundled site/dictionary/runtime |
| Debug shell size after final forced build | 2,956,137 bytes |

The test-only release APK was moved outside publishable build outputs to
`/tmp/nhe-release-check.3XEJjT/test-only-apk/`; it is **not** a production installer.
Its temporary keys are outside the repository. Production key continuity and
signed content integration remain separate gates.

Android screenshots: `dist/android-real-online.png`,
`dist/android-real-offline.png`, and `dist/android-fixture-*.png`.

## Remaining Release Gates

- Older supported Android/WebView coverage is BLOCKED by host disk space. An
  API-30 image and `Nheenga_Offline_API30` AVD were prepared, but startup required
  at least 7.2 GiB available; only about 2.2 GiB remained. No user files were deleted.
  API-23 support is lint-checked, not device-proven.
- Use the existing stable production APK/content signing identities. Validate
  release-mode signed catalog acceptance and unsigned/wrong-key rejection over
  trusted HTTPS, then same-key versionCode N+1 install with library retention.
- Actual ENOSPC/process-death/AtomicFile failure, concurrent settings/removal,
  notification denial, notification pause, mobile-only metering policy,
  reboot/Doze/battery constraints, API-36 job-quota and service-timeout stress.
- Full citation recto/verso/back/forward/internal-popup/external-link matrix.
  Cartas has named image files, not a numeric viewer mapping; this work did not
  invent or change its historical pagination.
- Browser real-site PWA/network audit, quota/eviction, worker-restart snapshots,
  stale-pin cleanup and storage reclamation after old tabs close. Chromium smoke
  is synthetic; real-content cold-offline evidence here is Android WebView.
- Vendor licensing and reproducible vendor-hash review; independent website-only
  installer preservation with the final production content key.
- Broad one-letter searches can stall rendering on the small emulator; the
  functional smoke uses the attested narrow query `abacaxi`.

Do not treat passing happy-path smoke as evidence for these untested stress and
production trust/deployment cases. Keep the implementation PR draft pending review.

## Production Publication Addendum

- User explicitly authorized first-release permanent signing-key creation and
  publication. Keys/password live only under `$HOME/.config/nhe-enga/`, mode 0600;
  no private material was committed or published. They require secure backup.
- Released APK 0.1.0, versionCode 1, 321,621 bytes. SHA-256:
  `700f76a1a5e0e1360f386a24b904d9f8d9c3f8f41c51e6e1f2b21580e88581fb`.
- Pages commit `67c2706f85c9458f55a152ea41d897fa81219a63`; GitHub deployment
  run `38749169741` succeeded. Public site: `https://kiansheik.io/nhe-enga/`;
  APK: `https://kiansheik.io/nhe-enga/downloads/nhe-enga.apk`.
- Live APK checksum and production catalog RSA signature were independently
  verified after deployment. All nine packs are signed with the pinned content key.
- Homepage has a compact Android-only icon gated by release metadata. Tested
  real mobile/desktop layouts and consent dialog. Copy correctly states that the
  APK is signed but distributed outside Play Store; it never asks to disable
  Play Protect or uninstall before an update.
- Native menu now separately checks Pages APK metadata, compares versionCode,
  and offers the fixed HTTPS APK URL after confirmation. Android still confirms
  installation and validates APK signing continuity; no silent self-install.
- Actual permanent-key release APK installed and launched on the API-36 emulator,
  downloaded the live signed core with notification permission denied, opened
  the local dictionary, and checked live APK metadata through its menu, correctly
  reporting version 0.1.0 current. Connected physical phone remained untouched.
- Added malformed/oversized/redirected APK metadata device regression: PASS.
  Catalog/image suite now has nine passing Python tests; Chromium includes the
  Android-only icon/consent regression, also PASS.
- Full signed Pages build originally failed from raw-image copy disk exhaustion.
  Direct-output optimization now produces byte-identical JPEGs without changing
  source scans; regression PASS. Fresh signed production build succeeded.
- The unused API-30 SDK image installed during this session was removed to recover
  space; its AVD could not be started, so older-device coverage remains unproven.
- `scripts/with_android_signing.sh` loads external identities without printing
  credentials. Increment `APK_VERSION_CODE` for subsequent APK releases; site-only
  deploys preserve the installer. Source changes remain in the working branch;
  only the generated `gh-pages` deployment was committed and pushed.
- The earlier remaining background/storage/older-device/vendor-audit gates are
  still limitations, not retroactively marked passed by this first publication.