#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
"${KOTLINC:-kotlinc}" "$ROOT/android/app/src/main/java/io/kiansheik/nheenga/VerifiedFiles.kt" \
  "$ROOT/tests/offline/NativeTransferSmoke.kt" -include-runtime -d "$TMP/smoke.jar"
java -jar "$TMP/smoke.jar"
