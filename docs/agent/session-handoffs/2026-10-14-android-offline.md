# Local-agent handoff — Android/offline Nhe'enga

## Goal and boundaries

Finish and validate the thin Android wrapper and unified offline website introduced
on `codex/android-offline-library`, based on main `92df177e2fd431a1aa15d8162dcfc46a65b1ab11`.
The user requested an implementation PR plus an emulator handoff, not a production
deployment. **Keep the PR draft until the release gates below have evidence.**
Commit fixes and evidence to the same PR; do not merge, publish an APK, upload keys,
or deploy `gh-pages` without the user's review.

Read root `AGENTS.md` and `offline/README.md`. Do not touch morphology, lexicon,
source pagination, corpus ground truth, or regenerate dictionary data as part of
this task. Preserve existing local changes. Prefer a separate worktree if necessary:

```sh
git status --short
git fetch origin codex/android-offline-library
git worktree add ../nhe-enga-offline-review origin/codex/android-offline-library
```

The Makefile/build script retain their original operations; only an offline target
include/help entry and final artifact postprocessing were added. There are no raw
media, APK binaries, or signing keys committed by this PR.

## What was actually verified in the authoring environment

| Check | Result |
| --- | --- |
| `make offline-test`: eight Python catalog/preparation/signature tests | PASS |
| `make offline-test`: Node SW protocol smoke with standard Web APIs | PASS: offline core, selective sources, query route, pinned update, unchanged-file reuse, corrupted update rollback safety |
| `make offline-native-test` against the actual `VerifiedFiles.kt` | PASS: verified streaming, hash reuse, interruption, Range resume, ignored Range, invalid Range/hash, old-file retention, path checks, RSA tampering |
| Python compilation; JavaScript syntax; shell syntax | PASS |
| Reconstruct originals after removing inserted Makefile/build-script lines | Original Git blob hashes match main |
| Real Chromium smoke | ATTEMPTED, blocked by environment policy: `ERR_BLOCKED_BY_ADMINISTRATOR` on localhost |
| Android APK compilation/lint, instrumented/emulator tests | NOT RUN: no Android SDK, Gradle distribution or emulator available |
| Full real-data Pages/VuePress/vendor build | NOT RUN: full repository/media and outbound container networking unavailable |
| Signed release APK size/install/update | NOT RUN; no production keys created or used |

Node protocol smoke is **not** a substitute for Chromium. Host JVM downloader
smoke is **not** a substitute for Android compilation, WorkManager or WebView tests.
The PR contains GitHub Actions jobs for Android compilation/lint and real Chromium,
but their results must be checked rather than assumed.

## First run: build and tiny fixture

Use JDK 17+, Android Studio/SDK, SDK platform 35 and build-tools 35.0.0. The checked-in
text bootstrap downloads/checks Gradle; Kotlin/Android dependencies come from their
normal Maven repositories. Use the emulator's **actual** image API/WebView version
in the report. Test at least API 35/36 and one older supported configuration; the
manifest's minimum API is 23, not a guarantee that every old WebView executes the
existing site's modern JavaScript.

```sh
make offline-test
make offline-native-test
python3 -m pip install playwright==1.55.0
python3 -m playwright install chromium
make offline-browser-test
./android/gradlew :app:assembleDebug :app:testDebugUnitTest :app:lintDebug

make offline-fixture
python3 -m http.server 8000 --directory dist/offline-fixture
# Separate terminal, with a running Android emulator:
OFFLINE_CONTENT_BASE=http://10.0.2.2:8000/nhe-enga/ make apk
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
adb shell am start -n io.kiansheik.nheenga.debug/io.kiansheik.nheenga.MainActivity
```

The fixture is synthetic and tiny. Do not commit generated fixture content. Reset
debug application data between independently numbered test catalogs when needed;
anti-rollback rejects a lower sequence. Never clear the user's release application
data to make a test pass.

If a UI/compile defect appears, fix it before moving on; no Android build has been
claimed in this PR. Use the native toolbar to manage downloads. It intentionally
avoids exposing a JavaScript-to-native filesystem bridge.

## Acceptance matrix: record pass/fail and evidence, not just a checkbox

| Scenario | Expected invariant |
| --- | --- |
| Fresh install, airplane mode | Native setup opens; explains first download is needed. No Chrome network-error page or crash. |
| Core only | Three dictionaries/search, quiz and citation metadata work after force-stop and offline relaunch; no bulk scans/tool runtime downloaded. |
| Initial core + sources | Core becomes usable before every scan finishes. Exact pack byte totals shown. |
| Single source pack | VLB readable offline; unselected source books do not silently bulk-download. Include `cartas_portiguara` (underscore ID) in testing. |
| Source citation routing | `book_name`, `page_number`, recto/verso mapping, back/forward, zoom, image-open and internal `target=_blank` stay correct. |
| Viewed-only persistence | Open one page in an unselected book online, disconnect, force-stop, reopen: that page remains; an unseen page gets a clear missing-download state. |
| All-source subscription | Add a synthetic new book and deploy a higher-sequence catalog: subscribed users receive it; individual-book users do not. |
| Core/content update, no APK change | Change fixture v1 to v2 and a JSON file; hash changes downloaded, unchanged scans not fetched. Current document remains coherent; reopening adopts v2. |
| Interrupted file | Kill process/disconnect mid-transfer; completed blobs remain. Range resume is validated; ignored Range restarts only that file. |
| Interrupted pack / storage full | Last installed set still usable; staged files reusable; no eviction of downloaded library. Test actual filesystem/storage failure. |
| Corrupt file/manifest/signature | Reject it; preserve working data. Test unsigned release, wrong key, changed payload, lower sequence and missing file/404. |
| Pause/cancel | Native settings and notification pause stop work; pause survives process restart. Explicit resume continues rather than discarding completed files. |
| Mobile-data policy | Unmetered default respected; user override works on a mobile-only connection. Changes apply to already pending jobs. |
| Background constraints | With app closed, reconnect, reboot, Doze and constrained battery: work resumes when allowed, with no promise of immediate scheduling. |
| Foreground lifecycle | Notification permission denied/granted, activity backgrounded, constraints delayed, worker retry and service timeout never crash the app. |
| Pack removal | Installed pack removed without dictionary loss; selected/future-subscription state updated; obsolete files reclaimed; re-download works. |
| Rollback | Previous installed version opens and auto-updates pause. Verify subsequent manual resume. |
| External boundaries | Bibliography links open externally; no CDN/analytics traffic from native renderer; internal downloads not opened outside the local origin. |
| APK content/size | Inspect APK ZIP/Analyze APK: no HTML site, JSON dictionaries, scans or bundled browser/runtime. Record actual debug and release sizes. |
| Native update | Install versionCode N+1 with the same signing key; library survives. Different key is not silently treated as a valid update. |
| Website offline | Run real Chromium smoke, then real site installed as PWA: offline cold launch, query routes, updates, removal, quota/persistence behavior. |
| Deployment independence | Publish/prepare a release once; subsequent site-only build preserves same APK checksum without Gradle. Wrong/missing content key fails safely. |

### Important hardening/edge cases to resolve before declaring this finished

- The current background implementation uses bounded WorkManager batches even for
  explicit downloads. Test Android 16 job quotas and deferred foreground starts.
  If a large real collection stalls under quota, use API 34+ **user-initiated data
  transfer jobs** for explicit bulk requests and keep WorkManager for background
  checks/older APIs. Do not work around OS restrictions by promising continuous
  background execution or asking for broad storage/battery permissions.
- Audit concurrent settings changes, cancellation vs commit, removal while work is
  ending, and process death during AtomicFile state writes. Keep the last working
  installation reachable in every failure case.
- Complete storage UX for saved-only/retired packs: currently explicit removal is
  centered on installed packs present in the current catalog. Ensure saved-only
  pages and retired installations can be removed intentionally without requiring
  application-data clearing. Do not silently evict them instead.
- Source-image misses currently use the existing viewer's error UI. Verify that the
  message clearly distinguishes “not downloaded” from a genuinely missing source.
- Browser per-client snapshots must remain coherent across reload/worker restart;
  audit stale-pin cleanup and real storage reclamation after closing old tabs.
- Validate current site's dynamic dependencies, not just hard-coded CDN tags. The
  build preparation mirrors known dependencies but has not been run on the entire
  real VuePress output here. Review vendor licensing and lock reproducible hashes
  for versioned loader/library downloads before release.
- Check gzip data actually used by each dictionary, Pyodide stdlib/micropip/wheel
  closure, generated source `image-formats.json`, accented filenames and old/new
  WebViews. No dictionary schema changes should be necessary for this task.
- Keep release/debug trust boundaries intact. A test-only unsigned/HTTP allowance
  must not accidentally enter a signed release. Do not disable TLS/signatures to
  make emulator networking easier.

## Real-data build and offline network audit

Use the user's existing complete repository checkout/worktree (not the tiny CI
sparse checkout). Avoid downloading or checking in new raw source PDFs.

```sh
OFFLINE_SKIP_APK=1 make pages-build
mkdir -p dist/offline-preview
ln -s "$(pwd)/.pages-build" dist/offline-preview/nhe-enga
python3 -m http.server 8000 --directory dist/offline-preview
```

Inspect `offline/catalog.json` and `offline/packs/*.json` under `.pages-build`.
Decode the base64 payload to inspect pack sizes; compare SHA-256 against **deployed
JPEGs**, not repository PNG inputs. Use WebView remote inspection and a server
request log to prove that offline searches and downloaded scans do not need a CDN,
Google Sheets, PyPI or the internet. Grammar/tools should be tested separately from
core dictionaries so an optional heavy runtime is never made a hidden core download.

## Signed integration test, then release gate

Follow `offline/README.md` with **temporary external test keys**, or production keys
only when the user explicitly provides their existing secure setup. No key material
belongs in this PR. Verify `apksigner`, APK size, content key fingerprint, replay
protection and website-only installer preservation. Do not deploy as part of tests.

Capture a short Markdown report in this handoff directory: machine/SDK/emulator and
WebView versions; commands; actual sizes; pass/fail per acceptance row; screenshots
or short logs for failures; fixes committed; remaining limitations. Attach small
screenshots/logs to the PR if useful. Do not commit emulators, Gradle caches, APKs,
downloaded books or large network traces.

## Suggested local-agent starting prompt

> Continue the existing draft PR on `codex/android-offline-library`. Read
> `AGENTS.md`, `offline/README.md`, and this handoff first. Inspect the diff, build
> the Android debug shell, run the provided protocol/browser/JVM tests, and execute
> the emulator acceptance matrix with synthetic fixtures then the real Pages build.
> Fix compile/runtime/race/UX defects in this branch and record reproducible test
> evidence. Preserve dictionary content and citation mappings. Do not merge,
> publish an APK, deploy gh-pages, or commit private keys/media. Report honestly
> which cases passed and which still block release.
