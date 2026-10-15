#!/usr/bin/env bash
set -euo pipefail

SIGNING_DIR="${NHE_SIGNING_DIR:-$HOME/.config/nhe-enga}"
export OFFLINE_SIGNING_KEY="${OFFLINE_SIGNING_KEY:-$SIGNING_DIR/content-private.pem}"
export APK_KEYSTORE="${APK_KEYSTORE:-$SIGNING_DIR/android-release.p12}"
export APK_KEY_ALIAS="${APK_KEY_ALIAS:-nheenga}"

if [[ ! -f "$OFFLINE_SIGNING_KEY" || ! -f "$APK_KEYSTORE" ]]; then
  printf '%s\n' 'Permanent content/APK signing keys are missing. Configure them outside the repository.' >&2
  exit 1
fi
if [[ -z "${APK_STORE_PASSWORD:-}" ]]; then
  if [[ ! -r "$SIGNING_DIR/android-keystore-password" ]]; then
    printf '%s\n' 'Set APK_STORE_PASSWORD locally or provide the private signing password file.' >&2
    exit 1
  fi
  APK_STORE_PASSWORD="$(<"$SIGNING_DIR/android-keystore-password")"
fi
export APK_STORE_PASSWORD
export APK_KEY_PASSWORD="${APK_KEY_PASSWORD:-$APK_STORE_PASSWORD}"
export OFFLINE_PUBLIC_KEY="$(openssl pkey -in "$OFFLINE_SIGNING_KEY" -pubout -outform DER 2>/dev/null | openssl base64 -A)"

if [[ "$#" -eq 0 ]]; then
  printf '%s\n' 'Usage: scripts/with_android_signing.sh COMMAND [ARGUMENT ...]' >&2
  exit 1
fi
exec "$@"