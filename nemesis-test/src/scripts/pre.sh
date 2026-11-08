#!/system/bin/sh
# Install only on the API/ABI/head unit investigated for this package.
SDK=$(getprop ro.build.version.sdk)
ABI=$(getprop ro.product.cpu.abi)
BOOT=$(getprop sys.boot_completed)

if [ "$SDK" != "19" ]; then
    echo "SAFE PLEX: this package requires Android API 19; found $SDK."
    exit 1
fi
case "$ABI" in
    armeabi-v7a|armeabi) ;;
    *) echo "SAFE PLEX: this package requires a 32-bit ARM head unit; found $ABI."
    exit 1 ;;
esac
if [ "$BOOT" != "1" ]; then
    echo "SAFE PLEX: wait for Android to finish booting, then retry the install."
    exit 1
fi
for JAR in /system/framework/automotive.jar /system/framework/com.hkmc.ext.hcan.jar; do
    if [ ! -r "$JAR" ]; then
        echo "SAFE PLEX: missing factory vehicle framework $JAR."
        exit 1
    fi
done

INSTALLED=$(pm path com.plexapp.android 2>/dev/null)
case "$INSTALLED" in
    package:*)
        echo "SAFE PLEX is already installed. Uninstall the previous SAFE PLEX package through NEMESIS first, then install this version."
        echo "(Do not just overwrite: the old guard service must be stopped.)"
        exit 1
        ;;
esac
echo "SAFE PLEX API 19 / ARM preflight passed. Installing Plex and the root guard service."
