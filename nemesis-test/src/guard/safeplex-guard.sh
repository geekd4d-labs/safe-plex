#!/system/bin/sh
# SAFE PLEX standalone guard service (NEMESIS-launched, root).
#
# Runs the Java guard under app_process. The guard reads the head unit's own
# factory vehicle services and force-stops Plex unless the car is confirmed
# parked. It never modifies any vehicle state and exits only when NEMESIS
# stops it (or on a fatal preflight failure).

export PATH=/system/bin:/system/xbin:/sbin:/vendor/bin
umask 022

PKG=com.plexapp.android
DIR=/data/local/safe-plex
APP_PROCESS=/system/bin/app_process
AUTOMOTIVE_JAR=/system/framework/automotive.jar
HCAN_JAR=/system/framework/com.hkmc.ext.hcan.jar

HERE="${0%/*}"
case "$HERE" in
    /*) ;;
    *) HERE="$PWD/$HERE" ;;
esac
cd "$HERE/.." || exit 1
GUARD_JAR="guard/safeplex-guard.jar"

[ -r "$GUARD_JAR" ] || { echo "SAFE PLEX guard jar missing: $GUARD_JAR"; exit 1; }
[ -x "$APP_PROCESS" ] || { echo "SAFE PLEX app_process missing: $APP_PROCESS"; exit 1; }
read -r CURRENT_BOOT < /proc/sys/kernel/random/boot_id || exit 1
mkdir -p "$DIR" || exit 1
chmod 755 "$DIR" || exit 1

write_state() {
    read -r UP REST < /proc/uptime || return 1
    {
        echo "version=1"
        echo "boot_id=$CURRENT_BOOT"
        echo "ready=$1"
        echo "uptime=$UP"
        echo "pid=$GUARD_PID"
    } > "$DIR/state.new" || return 1
    chmod 644 "$DIR/state.new" || return 1
    mv "$DIR/state.new" "$DIR/state"
}

case "${1:-daemon}" in
    cleanup)
        am force-stop "$PKG" >/dev/null 2>&1
        rm -f "$DIR/state" "$DIR/lock/pid" "$DIR/lock/boot"
        rmdir "$DIR/lock" 2>/dev/null
        exit 0 ;;
    daemon) ;;
    *) echo "Use daemon or cleanup"; exit 1 ;;
esac

case "$(getprop ro.build.version.sdk)" in
    19) ;;
    *) echo "SAFE PLEX requires the validated API 19 head unit; found $(getprop ro.build.version.sdk)."
    exit 1 ;;
esac
[ -r "$AUTOMOTIVE_JAR" ] || { echo "SAFE PLEX missing $AUTOMOTIVE_JAR"; exit 1; }
[ -r "$HCAN_JAR" ] || { echo "SAFE PLEX missing $HCAN_JAR"; exit 1; }

if ! mkdir "$DIR/lock" 2>/dev/null; then
    LOCK_PID=
    LOCK_BOOT=
    [ -r "$DIR/lock/pid" ] && read -r LOCK_PID < "$DIR/lock/pid"
    [ -r "$DIR/lock/boot" ] && read -r LOCK_BOOT < "$DIR/lock/boot"
    case "$LOCK_PID" in
        ''|*[!0-9]*) echo "SAFE PLEX guard lock is unreadable; refusing to double-start"
        exit 1 ;;
    esac
    if { [ -z "$LOCK_BOOT" ] || [ "$LOCK_BOOT" = "$CURRENT_BOOT" ]; } \
            && kill -0 "$LOCK_PID" 2>/dev/null; then
        exit 1
    fi
    rm -f "$DIR/lock/pid" "$DIR/lock/boot"
    rmdir "$DIR/lock" && mkdir "$DIR/lock" || exit 1
fi
echo $$ > "$DIR/lock/pid" || exit 1
echo "$CURRENT_BOOT" > "$DIR/lock/boot" || exit 1

"$APP_PROCESS" -Djava.class.path="$GUARD_JAR" /system/bin \
    dev.geekd4dlabs.safeplex.StandaloneGuard &
GUARD_PID=$!
kill -0 "$GUARD_PID" 2>/dev/null || { echo "SAFE PLEX guard exited immediately"
exit 1; }
write_state 1 || exit 1

trap 'kill "$GUARD_PID" 2>/dev/null; rm -f "$DIR/lock/pid" "$DIR/lock/boot"; rmdir "$DIR/lock" 2>/dev/null; exit 0' TERM INT HUP

while kill -0 "$GUARD_PID" 2>/dev/null; do
    sleep 1
done
wait "$GUARD_PID"
EXIT=$?
rm -f "$DIR/lock/pid" "$DIR/lock/boot"
rmdir "$DIR/lock" 2>/dev/null
exit "$EXIT"
