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

# --- Keep Plex as the head-unit audio source after playback stops ----------
# When Plex abandons audio focus, the Gen5W AudioServiceHelper immediately
# auto-restores the previous AV source (FM radio). Instead, a stopping player
# hands focus to a process-wide no-op holder, then abandons its own listener.
# The released player ignores the resulting focus loss. A force-stop by the
# Park Guard kills the process, so the system drops the holder normally.
FOCUS_REL = "smali_classes2/com/plexapp/plex/audioplayer/a.smali"
HOLDER_REL = "smali_classes2/com/plexapp/plex/audioplayer/EV6FocusHolder.smali"
FOCUS_CLASS = "Lcom/plexapp/plex/audioplayer/a;"
HOLDER_CLASS = "Lcom/plexapp/plex/audioplayer/EV6FocusHolder;"
RELEASED = f"{FOCUS_CLASS}->ev6Released:Z"

FOCUS_FIELD_ANCHOR = f".field b:Lcom/plexapp/plex/audioplayer/b;\n"
FOCUS_FIELD = "\n.field ev6Released:Z\n"

FOCUS_REQUEST_ANCHOR = ".method public a()Z\n    .locals 3\n\n    .prologue\n"
FOCUS_REQUEST_INJECTION = f"""    # EV6: a new playback request re-arms this listener.
    const/4 v0, 0x0

    iput-boolean v0, p0, {RELEASED}

"""

FOCUS_ABANDON_ANCHOR = f"""    .line 54
    iget-object v1, p0, {FOCUS_CLASS}->a:Landroid/media/AudioManager;

    invoke-virtual {{v1, p0}}, Landroid/media/AudioManager;->abandonAudioFocus("""
FOCUS_ABANDON_INJECTION = f"""    # EV6: keep Plex as the AV source so the head unit does not revert to radio.
    iput-boolean v0, p0, {RELEASED}

    iget-object v1, p0, {FOCUS_CLASS}->a:Landroid/media/AudioManager;

    invoke-static {{v1}}, {HOLDER_CLASS}->hold(Landroid/media/AudioManager;)V

"""

FOCUS_CHANGE_ANCHOR = ".method public onAudioFocusChange(I)V\n    .locals 2\n\n    .prologue\n"
FOCUS_CHANGE_INJECTION = f"""    # EV6: a released player ignores the loss caused by the focus holder.
    iget-boolean v0, p0, {RELEASED}

    if-eqz v0, :ev6_listener_active

    return-void

    :ev6_listener_active
"""

HOLDER_SMALI = f""".class public final {HOLDER_CLASS}
.super Ljava/lang/Object;
.source "EV6FocusHolder.java"

# interfaces
.implements Landroid/media/AudioManager$OnAudioFocusChangeListener;


# Process-wide no-op focus owner. Keeps Plex as the Gen5W AV source after a
# player stops; released automatically when the Plex process dies.
.field private static final INSTANCE:{HOLDER_CLASS}


.method static constructor <clinit>()V
    .locals 1

    new-instance v0, {HOLDER_CLASS}

    invoke-direct {{v0}}, {HOLDER_CLASS}-><init>()V

    sput-object v0, {HOLDER_CLASS}->INSTANCE:{HOLDER_CLASS}

    return-void
.end method

.method private constructor <init>()V
    .locals 0

    invoke-direct {{p0}}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static hold(Landroid/media/AudioManager;)V
    .locals 3

    if-nez p0, :cond_0

    return-void

    :cond_0
    sget-object v0, {HOLDER_CLASS}->INSTANCE:{HOLDER_CLASS}

    const/4 v1, 0x3

    const/4 v2, 0x1

    invoke-virtual {{p0, v0, v1, v2}}, Landroid/media/AudioManager;->requestAudioFocus(Landroid/media/AudioManager$OnAudioFocusChangeListener;II)I

    return-void
.end method

.method public onAudioFocusChange(I)V
    .locals 0

    return-void
.end method
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


def _replace_once(text: str, anchor: str, replacement: str, label: str, path: Path) -> str:
    if text.count(anchor) != 1:
        raise RuntimeError(f"{label} anchor not found exactly once in {path}")
    return text.replace(anchor, replacement, 1)


def keep_audio_source(decoded: Path) -> bool:
    focus = decoded / FOCUS_REL
    holder = decoded / HOLDER_REL
    text = focus.read_text(encoding="utf-8")
    patched_focus = RELEASED in text
    current_holder = holder.is_file() and holder.read_text(encoding="utf-8") == HOLDER_SMALI
    if patched_focus and current_holder:
        return False
    if not patched_focus:
        text = _replace_once(text, FOCUS_FIELD_ANCHOR, FOCUS_FIELD_ANCHOR + FOCUS_FIELD,
                             "focus field", focus)
        text = _replace_once(text, FOCUS_REQUEST_ANCHOR,
                             FOCUS_REQUEST_ANCHOR + FOCUS_REQUEST_INJECTION, "focus request", focus)
        text = _replace_once(text, FOCUS_ABANDON_ANCHOR,
                             FOCUS_ABANDON_INJECTION + FOCUS_ABANDON_ANCHOR, "focus abandon", focus)
        text = _replace_once(text, FOCUS_CHANGE_ANCHOR,
                             FOCUS_CHANGE_ANCHOR + FOCUS_CHANGE_INJECTION, "focus change", focus)
        focus.write_text(text, encoding="utf-8")
    holder.write_text(HOLDER_SMALI, encoding="utf-8")
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
        "keep_audio_source": keep_audio_source(decoded),
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
