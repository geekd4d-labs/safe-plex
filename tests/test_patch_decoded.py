#!/usr/bin/env python3
"""Tests for the deterministic decoded-APK patcher."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from patch_decoded import patch_tree  # noqa: E402


MANIFEST = """<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.plexapp.android">
    <uses-permission android:name="android.permission.WAKE_LOCK"/>
    <application/>
</manifest>
"""

MOBILE = """.class public Lcom/plexapp/plex/activities/mobile/MobileVideoPlayerActivity;
.super Lcom/plexapp/plex/activities/n;

.method public onCreateOptionsMenu(Landroid/view/Menu;)Z
    .locals 1
    const/4 v0, 0x1
    return v0
.end method
"""

PLAYER2 = """.class public Lcom/plexapp/plex/videoplayer/ui/VideoPlayerActivity2;
.super Lcom/plexapp/plex/activities/d;

.method protected onCreate(Landroid/os/Bundle;)V
    .locals 1

    .prologue
    .line 41
    invoke-super {p0, p1}, Lcom/plexapp/plex/activities/d;->onCreate(Landroid/os/Bundle;)V

    .line 42
    const v0, 0x7f0d0032
    invoke-virtual {p0, v0}, Lcom/plexapp/plex/videoplayer/ui/VideoPlayerActivity2;->setContentView(I)V
    return-void
.end method
"""

FOCUS = """.class public Lcom/plexapp/plex/audioplayer/a;
.super Ljava/lang/Object;
.implements Landroid/media/AudioManager$OnAudioFocusChangeListener;

.field a:Landroid/media/AudioManager;

.field b:Lcom/plexapp/plex/audioplayer/b;

.method public a()Z
    .locals 3

    .prologue
    const/4 v0, 0x1

    .line 46
    iget-object v1, p0, Lcom/plexapp/plex/audioplayer/a;->a:Landroid/media/AudioManager;
    const/4 v2, 0x3
    invoke-virtual {v1, p0, v2, v0}, Landroid/media/AudioManager;->requestAudioFocus(Landroid/media/AudioManager$OnAudioFocusChangeListener;II)I
    move-result v1
    return v1
.end method

.method public b()Z
    .locals 2

    .prologue
    const/4 v0, 0x1

    .line 54
    iget-object v1, p0, Lcom/plexapp/plex/audioplayer/a;->a:Landroid/media/AudioManager;

    invoke-virtual {v1, p0}, Landroid/media/AudioManager;->abandonAudioFocus(Landroid/media/AudioManager$OnAudioFocusChangeListener;)I

    move-result v1
    return v1
.end method

.method public onAudioFocusChange(I)V
    .locals 2

    .prologue
    .line 63
    iget-object v0, p0, Lcom/plexapp/plex/audioplayer/a;->b:Lcom/plexapp/plex/audioplayer/b;
    return-void
.end method
"""

FOCUS_REL = "smali_classes2/com/plexapp/plex/audioplayer/a.smali"
HOLDER_REL = "smali_classes2/com/plexapp/plex/audioplayer/EV6FocusHolder.smali"
ALL_TRUE = {"get_tasks_permission": True, "mobile_fullscreen": True,
            "player2_fullscreen": True, "ca_bundle": True, "keep_audio_source": True}


class PatchTreeTests(unittest.TestCase):
    def make_tree(self, root: Path) -> tuple[Path, Path]:
        decoded = root / "decoded"
        manifest = decoded / "AndroidManifest.xml"
        mobile = decoded / "smali/com/plexapp/plex/activities/mobile/MobileVideoPlayerActivity.smali"
        player2 = decoded / "smali/com/plexapp/plex/videoplayer/ui/VideoPlayerActivity2.smali"
        focus = decoded / FOCUS_REL
        ca = root / "cacert.pem"
        old_ca = decoded / "assets/Resources/cacert.pem"
        for path in (manifest, mobile, player2, focus, old_ca):
            path.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(MANIFEST, encoding="utf-8")
        mobile.write_text(MOBILE, encoding="utf-8")
        player2.write_text(PLAYER2, encoding="utf-8")
        focus.write_text(FOCUS, encoding="utf-8")
        old_ca.write_text("STALE TEST CA\n", encoding="ascii")
        ca.write_text("CURRENT TEST CA\n", encoding="ascii")
        return decoded, ca

    def test_applies_all_required_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decoded, ca = self.make_tree(Path(tmp))
            changed = patch_tree(decoded, ca)

            self.assertEqual(changed, ALL_TRUE)
            manifest = (decoded / "AndroidManifest.xml").read_text(encoding="utf-8")
            self.assertIn("android.permission.GET_TASKS", manifest)
            for relative in (
                "smali/com/plexapp/plex/activities/mobile/MobileVideoPlayerActivity.smali",
                "smali/com/plexapp/plex/videoplayer/ui/VideoPlayerActivity2.smali",
            ):
                smali = (decoded / relative).read_text(encoding="utf-8")
                self.assertIn("const/16 v1, 0x400", smali)
                self.assertIn("Landroid/view/Window;->addFlags(I)V", smali)
            self.assertEqual(
                (decoded / "assets/Resources/cacert.pem").read_text(encoding="ascii"),
                "CURRENT TEST CA\n",
            )

    def test_stop_hands_focus_to_holder_instead_of_reverting_to_radio(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decoded, ca = self.make_tree(Path(tmp))
            patch_tree(decoded, ca)
            focus = (decoded / FOCUS_REL).read_text(encoding="utf-8")
            holder = (decoded / HOLDER_REL).read_text(encoding="utf-8")

            self.assertIn(".field ev6Released:Z", focus)
            b_method = focus[focus.index(".method public b()Z"):]
            b_method = b_method[:b_method.index(".end method")]
            hold = b_method.index("EV6FocusHolder;->hold(Landroid/media/AudioManager;)V")
            abandon = b_method.index("->abandonAudioFocus(")
            self.assertLess(hold, abandon, "holder must take focus before the player abandons it")
            self.assertIn("iput-boolean v0, p0, Lcom/plexapp/plex/audioplayer/a;->ev6Released:Z", b_method)

            a_method = focus[focus.index(".method public a()Z"):]
            a_method = a_method[:a_method.index(".end method")]
            self.assertLess(a_method.index("->ev6Released:Z"), a_method.index("->requestAudioFocus("),
                            "a new playback request must re-arm the listener first")

            change = focus[focus.index(".method public onAudioFocusChange(I)V"):]
            self.assertLess(change.index("iget-boolean v0, p0, Lcom/plexapp/plex/audioplayer/a;->ev6Released:Z"),
                            change.index(".line 63"),
                            "a released player must ignore the focus loss caused by the holder")

            self.assertIn(".implements Landroid/media/AudioManager$OnAudioFocusChangeListener;", holder)
            self.assertIn(".method public static hold(Landroid/media/AudioManager;)V", holder)
            self.assertIn("->requestAudioFocus(Landroid/media/AudioManager$OnAudioFocusChangeListener;II)I", holder)
            listener = holder[holder.index(".method public onAudioFocusChange(I)V"):]
            self.assertNotIn("invoke", listener[:listener.index(".end method")], "holder must be a no-op")

    def test_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decoded, ca = self.make_tree(Path(tmp))
            patch_tree(decoded, ca)
            snapshot = {
                path.relative_to(decoded): path.read_bytes()
                for path in decoded.rglob("*") if path.is_file()
            }
            changed = patch_tree(decoded, ca)
            self.assertEqual(changed, {key: False for key in ALL_TRUE})
            self.assertEqual(
                snapshot,
                {path.relative_to(decoded): path.read_bytes()
                 for path in decoded.rglob("*") if path.is_file()},
            )


if __name__ == "__main__":
    unittest.main()
