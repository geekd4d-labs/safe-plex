#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
UPSTREAM=
APKTOOL=
JAVA_BIN=${JAVA_HOME:+$JAVA_HOME/bin/java}
JAVA_BIN=${JAVA_BIN:-java}
OUT="$ROOT/dist/Plex-6.17.1.5294-EV6-unsigned.apk"
WORK="$ROOT/.work/plex-decoded"
EXPECTED_APK_SHA=31b2d5312a0f81627c2831fc1bd376ba149583166d06dab281001a53b068ef0c
CA="$ROOT/vendor/cacert-2026-11-05.pem"
EXPECTED_CA_SHA=427c064216761a1e72a8b30f0d954d08cb6e4435a82091fb865afd20c8497285

usage() {
  echo "usage: $0 --apk UPSTREAM.apk --apktool APKTOOL.jar [--java JAVA] [--out FILE] [--work DIR]" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apk) UPSTREAM=$2; shift 2 ;;
    --apktool) APKTOOL=$2; shift 2 ;;
    --java) JAVA_BIN=$2; shift 2 ;;
    --out) OUT=$2; shift 2 ;;
    --work) WORK=$2; shift 2 ;;
    *) usage ;;
  esac
done
[[ -n "$UPSTREAM" && -f "$UPSTREAM" && -n "$APKTOOL" && -f "$APKTOOL" ]] || usage
[[ -x "$JAVA_BIN" ]] || command -v "$JAVA_BIN" >/dev/null 2>&1 || {
  echo "Java not found; pass --java or set JAVA_HOME" >&2; exit 1;
}

hash_file() {
  python3 - "$1" <<'PY'
import hashlib, pathlib, sys
p = pathlib.Path(sys.argv[1])
h = hashlib.sha256()
with p.open('rb') as f:
    for chunk in iter(lambda: f.read(1024 * 1024), b''):
        h.update(chunk)
print(h.hexdigest())
PY
}

[[ $(hash_file "$UPSTREAM") == "$EXPECTED_APK_SHA" ]] || {
  echo "refusing unreviewed upstream APK: SHA-256 mismatch" >&2; exit 1;
}
[[ $(hash_file "$CA") == "$EXPECTED_CA_SHA" ]] || {
  echo "refusing changed CA bundle: SHA-256 mismatch" >&2; exit 1;
}

case "$WORK" in
  "$ROOT"/.work/*) ;;
  *) echo "--work must stay under $ROOT/.work" >&2; exit 2 ;;
esac

python3 -m unittest discover -s "$ROOT/tests" -v
rm -rf "$WORK"
mkdir -p "$(dirname "$WORK")" "$(dirname "$OUT")"
"$JAVA_BIN" -jar "$APKTOOL" d -f "$UPSTREAM" -o "$WORK"
python3 "$ROOT/scripts/patch_decoded.py" "$WORK" --ca "$CA"
"$JAVA_BIN" -jar "$APKTOOL" b "$WORK" -o "$OUT"

echo "unsigned_apk=$OUT"
echo "sha256=$(hash_file "$OUT")"
