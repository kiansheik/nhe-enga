# Offline website and Android library

One website; two storage adapters. The Android APK contains native controls and
sync code, **not** dictionary JSON, scans, a bundled website, Chromium, Python,
Flutter, or a second dictionary UI. New website/data releases do not require a
native rebuild. Native capabilities, security fixes and OS compatibility still do.

**Status: implementation for emulator validation, not a signed production release.**
Start with [the local-agent handoff](../docs/agent/session-handoffs/2026-10-14-android-offline.md).

## Components

| Path | Responsibility |
| --- | --- |
| `scripts/build_offline.py` | Postprocess the final Pages artifact, mirror runtime dependencies, generate per-pack SHA-256 manifests and the signed catalog. |
| `offline/sw.js` | Browser Cache Storage adapter; published as `/nhe-enga/sw.js` for root scope. |
| `offline/register.js`, `offline/index.html`, `offline/ui.js` | Shared browser registration/download management; the Android local origin skips service-worker registration. |
| `android/.../VerifiedFiles.kt` | Stream to app-owned hash-addressed files, resume valid HTTP ranges, verify before committing. Pure JVM tests exercise this exact implementation. |
| `android/.../Library.kt` | Signature verification, conditional catalog checks, manifests, durable state, subscriptions, coherent activation, saved pages and rollback. |
| `android/.../MainActivity.kt` | Native setup/settings and a local HTTPS WebViewAssetLoader. No JavaScript-to-native bridge is exposed. |
| `android/.../SyncWorker.kt` | Constrained background batches, retry, visible user-requested progress and durable pause. |
| `scripts/stage_android.py` | Verify/package a release APK and preserve it across subsequent website-only deployments. |

## Development

```sh
make offline-test
make offline-native-test         # JDK + kotlinc on PATH, or set KOTLINC
make offline-fixture
python3 -m http.server 8000 --directory dist/offline-fixture
# Another terminal; SDK 35, build-tools 35.0.0 and JDK 17+ must be installed:
OFFLINE_CONTENT_BASE=http://10.0.2.2:8000/nhe-enga/ make apk
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

The debug package is `io.kiansheik.nheenga.debug`, separate from the release app.
Unsigned catalogs are accepted **only by debug builds without a pinned public
key**. HTTP is restricted to emulator/loopback hosts in native configuration and
is disabled in release. A debug build with a public key verifies signatures too.
The text-only Gradle bootstrap downloads Gradle 8.11.1 and checks the pinned
checksum against the official distribution checksum. It does not install the SDK.

For actual dictionaries and sources, use the existing full checkout:

```sh
OFFLINE_SKIP_APK=1 make pages-build  # Local preview ONLY; no installer preservation.
mkdir -p dist/offline-preview
ln -s "$(pwd)/.pages-build" dist/offline-preview/nhe-enga
python3 -m http.server 8000 --directory dist/offline-preview
```

Use a free test port and update `OFFLINE_CONTENT_BASE` accordingly. The Android
server URL is native configuration; changing it requires rebuilding that test
shell. Content at the configured server does not. Never serve the source tree as
an offline-ready release: registration and CDN rewriting occur after the build.

## Pack and update contract

`core` contains the dictionary interfaces, essential compressed data, quiz,
source viewer, citation metadata and local supporting JS/CSS. `source-<directory>`
contains a single source's optimized images. `tools` contains the other published
assets, including the grammar/computational tools and self-hosted Pyodide runtime.
The local-only `/translate/` Gradio client is explicitly not advertised offline.
APK downloads and deployment metadata are excluded from all content packs.

The root catalog envelope contains a base64 `payload` and a base64 `signature`.
The signature is RSA PKCS#1 v1.5 with SHA-256 over the **exact decoded payload
bytes**. The payload identifies protocol version, minimum shell protocol, a
monotonically increasing `sequence`, and a small list of packs. Each pack points
to a hash-addressed manifest with file paths, byte lengths, MIME types and SHA-256s.
The bytes hashed are the final optimized/re-written published bytes. `.gz` data
is served as binary gzip **without** an HTTP `Content-Encoding` header; existing
Pako callers still decompress it themselves.

Downloads are file-level, not binary patches. A changed compressed dictionary is
redownloaded; an unchanged book is not. Content blobs are named by SHA-256, so
identical files are reusable. Downloads use `.part` files, validate `Content-Range`
when resuming, restart only the current file if Range is ignored, and verify
length/hash before renaming. Completed files survive process death and retries.
Insufficient space pauses progress without deleting the existing library.

The first core install activates before optional books finish. Subsequent updated
subscribed packs stage before the installed-set pointer changes. Open documents
use pinned snapshots rather than switching JavaScript/data versions underneath
users. Android retains the previous installed set for explicit rollback and pauses
auto-updates after rollback. Saved individual pages subscribe to updates without
implicitly downloading their whole books. Selected retired packs are retained,
not treated as permission to delete the user's content.

A user chooses individual books or explicitly subscribes to all current/future
sources. Mobile-data permission is a visible choice in Android; otherwise bulk
work waits for an unmetered connection. WorkManager checks periodically (12 hours)
and when the application opens, with resume checks throttled after successful
checks. Background batches stop/retry before seven minutes; completed files remain.
Android scheduling is best-effort, not continuous connectivity monitoring.

The browser requests persistent storage when a user saves a selection, but browser
quotas/eviction and service-worker lifetimes still apply. Keep a browser page open
for large downloads. The Android files live under `filesDir/library`, not cache;
uninstalling/clearing app data still removes them. No storage permission is needed.

## Signing and publishing

There are **two distinct identities**: the APK signing keystore (Android installation
updates) and the content manifest signing key (website/data updates). Keep both
private keys outside the repository. Back them up securely. Do not generate new
keys for each build. Key rotation requires a reviewed migration/native release.

One-time content-key setup, only when the target file does not already exist:

```sh
mkdir -p "$HOME/.config/nhe-enga"
# STOP if this file exists: reuse the existing production key.
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 \
  -out "$HOME/.config/nhe-enga/content-private.pem"
chmod 600 "$HOME/.config/nhe-enga/content-private.pem"
export OFFLINE_SIGNING_KEY="$HOME/.config/nhe-enga/content-private.pem"
export OFFLINE_PUBLIC_KEY="$(openssl pkey -in "$OFFLINE_SIGNING_KEY" -pubout -outform DER | openssl base64 -A)"
```

Set `APK_KEYSTORE`, `APK_STORE_PASSWORD`, `APK_KEY_ALIAS`, `APK_KEY_PASSWORD`
from your own stable keystore/secret store. Optional `APK_VERSION_CODE` (increment
for native updates) and `APK_VERSION_NAME` default to `1` and `0.1.0`.

```sh
make apk-release
# Only after device/emulator validation and permission to publish:
OFFLINE_SEQUENCE="$(date +%s)" make deploy-gh-pages
```

`make apk-release` verifies the APK with SDK `apksigner`, enforces a 15 MiB shell
budget, and stages it in ignored `dist/android/`. The Pages build copies this
installer to `/nhe-enga/downloads/nhe-enga.apk`, plus checksum and release metadata.
The website shows the link only when release metadata is available.

A fresh checkout can recover the existing installer from the project's own HTTPS
site without Gradle. A non-404 recovery failure fails the build rather than silently
removing an existing download. Once an APK is included, the Pages build requires
its matching content-signing key. The signing key is never included in an artifact.
`OFFLINE_SKIP_APK=1` is only for local previews; **never set it for deployment**.

## Dependency preparation

Pako/PapaParse use existing local files. The final build mirrors the versioned
JSZip/FileSaver references and Pyodide 0.25.0 runtime, stdlib and micropip dependency
closure; it does not upgrade Pyodide during the offline migration. Vendor cache is
ignored `.cache/offline-vendor/`. `offline/vendor-report.json` records deployed
vendor paths/hashes. Pyodide wheels are verified against its upstream lockfile.
Versioned CDN loader/library files currently rely on HTTPS and record their resulting
hashes; pin/review those vendor hashes and required license notices before release.
Known remaining CDN script/link references fail the preparation step. A full network
audit of the real generated VuePress site remains a release gate (dynamic URLs and
online-only integrations are not proven by a text scan).

## Verification references

- Android local content: https://developer.android.com/develop/ui/views/layout/webapps/load-local-content
- WorkManager foreground workers and Android 16 quota caveat: https://developer.android.com/develop/background-work/background-tasks/persistent/how-to/long-running
- User-initiated transfers: https://developer.android.com/develop/background-work/background-tasks/uidt
- App-owned files: https://developer.android.com/training/data-storage/app-specific
- AGP 8.9.2 / Gradle 8.11.1 / SDK 35 / JDK 17: https://developer.android.com/build/releases/agp-8-9-0-release-notes
- Distribution checksum: https://gradle.org/release-checksums/

These are pinned compatibility baselines, not a claim that every dependency is the
newest available release. Before raising `minSdk` or changing WebView libraries,
consider older phones and test the actual JavaScript/runtime capabilities.
