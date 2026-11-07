#!/usr/bin/env bash
set -euo pipefail

APK=
OUT=
BUILD_TOOLS=
KEYSTORE=
ALIAS=
STORE_PASS_FILE=
KEY_PASS_FILE=

usage() {
  echo "usage: $0 --apk unsigned.apk --out signed.apk --build-tools DIR --keystore FILE --alias NAME --store-pass-file FILE --key-pass-file FILE" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apk) APK=$2; shift 2 ;;
    --out) OUT=$2; shift 2 ;;
    --build-tools) BUILD_TOOLS=$2; shift 2 ;;
    --keystore) KEYSTORE=$2; shift 2 ;;
    --alias) ALIAS=$2; shift 2 ;;
    --store-pass-file) STORE_PASS_FILE=$2; shift 2 ;;
    --key-pass-file) KEY_PASS_FILE=$2; shift 2 ;;
    *) usage ;;
  esac
done

for file in "$APK" "$KEYSTORE" "$STORE_PASS_FILE" "$KEY_PASS_FILE"; do
  [[ -n "$file" && -f "$file" ]] || usage
done
[[ -n "$OUT" && -n "$ALIAS" ]] || usage
[[ -x "$BUILD_TOOLS/zipalign" && -x "$BUILD_TOOLS/apksigner" ]] || {
  echo "zipalign/apksigner missing from --build-tools" >&2; exit 1;
}

mkdir -p "$(dirname "$OUT")"
ALIGNED="${OUT%.apk}.aligned.apk"
trap 'rm -f "$ALIGNED"' EXIT

"$BUILD_TOOLS/zipalign" -f -p 4 "$APK" "$ALIGNED"
"$BUILD_TOOLS/apksigner" sign \
  --ks "$KEYSTORE" \
  --ks-key-alias "$ALIAS" \
  --ks-pass "file:$STORE_PASS_FILE" \
  --key-pass "file:$KEY_PASS_FILE" \
  --min-sdk-version 16 \
  --v1-signing-enabled true \
  --v2-signing-enabled false \
  --v3-signing-enabled false \
  --out "$OUT" "$ALIGNED"
"$BUILD_TOOLS/apksigner" verify --min-sdk-version 16 --verbose --print-certs "$OUT"
python3 - "$OUT" <<'PY'
import hashlib, pathlib, sys
p = pathlib.Path(sys.argv[1])
print(f"signed_apk={p}")
print(f"sha256={hashlib.sha256(p.read_bytes()).hexdigest()}")
PY
