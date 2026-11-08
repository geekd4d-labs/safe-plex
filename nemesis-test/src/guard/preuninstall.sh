#!/system/bin/sh
# NEMESIS stops this package's service before running preuninstall; this is
# the belt-and-braces cleanup if it is running.
HERE="${0%/*}"
case "$HERE" in
    /*) ;;
    *) HERE="$PWD/$HERE" ;;
esac
cd "$HERE/.." || exit 1

am force-stop com.plexapp.android || exit 1
exec /system/bin/sh "$HERE/safeplex-guard.sh" cleanup
