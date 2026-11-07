#!/usr/bin/env python3
"""Apply the reviewed EV6 compatibility patches to a decoded Plex APK."""
from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

GET_TASKS = '    <uses-permission android:name="android.permission.GET_TASKS"/>\n'
WAKE_LOCK = '    <uses-permission android:name="android.permission.WAKE_LOCK"/>\n'

MOBILE_ON_CREATE = """.method protected onCreate(Landroid/os/Bundle;)V
    .locals 2

    .prologue
    # Gen5W requires FLAG_FULLSCREEN to remove the OEM 90px video inset.
    invoke-virtual {p0}, Lcom/plexapp/plex/activities/mobile/MobileVideoPlayerActivity;->getWindow()Landroid/view/Window;

    move-result-object v0

    const/16 v1, 0x400

    invoke-virtual {v0, v1}, Landroid/view/Window;->addFlags(I)V

    invoke-super {p0, p1}, Lcom/plexapp/plex/activities/n;->onCreate(Landroid/os/Bundle;)V

    return-void
.end method

"""

PLAYER2_INJECTION = """    # Gen5W requires FLAG_FULLSCREEN to remove the OEM 90px video inset.
    invoke-virtual {p0}, Lcom/plexapp/plex/videoplayer/ui/VideoPlayerActivity2;->getWindow()Landroid/view/Window;

    move-result-object v0

    const/16 v1, 0x400

    invoke-virtual {v0, v1}, Landroid/view/Window;->addFlags(I)V

"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def patch_manifest(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if "android.permission.GET_TASKS" in text:
        return False
    if WAKE_LOCK not in text:
        raise RuntimeError(f"WAKE_LOCK insertion anchor missing in {path}")
    path.write_text(text.replace(WAKE_LOCK, WAKE_LOCK + GET_TASKS, 1), encoding="utf-8")
    return True


def patch_mobile_player(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if "MobileVideoPlayerActivity;->getWindow()" in text and "->addFlags(I)V" in text:
        return False
    anchor = ".method public onCreateOptionsMenu(Landroid/view/Menu;)Z\n"
    if anchor not in text:
        raise RuntimeError(f"onCreateOptionsMenu insertion anchor missing in {path}")
    path.write_text(text.replace(anchor, MOBILE_ON_CREATE + anchor, 1), encoding="utf-8")
    return True


def patch_player2(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    start = text.find(".method protected onCreate(Landroid/os/Bundle;)V")
    end = text.find(".end method", start)
    if start < 0 or end < 0:
        raise RuntimeError(f"onCreate method missing in {path}")
    method = text[start:end]
    if "VideoPlayerActivity2;->getWindow()" in method and "->addFlags(I)V" in method:
        return False
    if "    .locals 1\n" not in method:
        raise RuntimeError(f"unexpected onCreate register layout in {path}")
    method = method.replace("    .locals 1\n", "    .locals 2\n", 1)
    anchor = "    .prologue\n"
    if anchor not in method:
        raise RuntimeError(f"onCreate prologue missing in {path}")
    method = method.replace(anchor, anchor + PLAYER2_INJECTION, 1)
    path.write_text(text[:start] + method + text[end:], encoding="utf-8")
    return True


def replace_ca_bundle(decoded: Path, ca_bundle: Path) -> bool:
    destination = decoded / "assets/Resources/cacert.pem"
    if not destination.exists():
        raise RuntimeError(f"Plex CA destination missing: {destination}")
    if sha256(destination) == sha256(ca_bundle):
        return False
    shutil.copyfile(ca_bundle, destination)
    return True


def patch_tree(decoded: Path, ca_bundle: Path) -> dict[str, bool]:
    if not decoded.is_dir():
        raise RuntimeError(f"decoded APK directory missing: {decoded}")
    if not ca_bundle.is_file():
        raise RuntimeError(f"CA bundle missing: {ca_bundle}")
    return {
        "get_tasks_permission": patch_manifest(decoded / "AndroidManifest.xml"),
        "mobile_fullscreen": patch_mobile_player(
            decoded / "smali/com/plexapp/plex/activities/mobile/MobileVideoPlayerActivity.smali"
        ),
        "player2_fullscreen": patch_player2(
            decoded / "smali/com/plexapp/plex/videoplayer/ui/VideoPlayerActivity2.smali"
        ),
        "ca_bundle": replace_ca_bundle(decoded, ca_bundle),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("decoded", type=Path, help="apktool-decoded Plex directory")
    parser.add_argument("--ca", type=Path, required=True, help="reviewed Mozilla CA bundle")
    args = parser.parse_args()
    for name, changed in patch_tree(args.decoded, args.ca).items():
        print(f"{name}: {'patched' if changed else 'already current'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
