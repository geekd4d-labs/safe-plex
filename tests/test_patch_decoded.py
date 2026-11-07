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


class PatchTreeTests(unittest.TestCase):
    def make_tree(self, root: Path) -> tuple[Path, Path]:
        decoded = root / "decoded"
        manifest = decoded / "AndroidManifest.xml"
        mobile = decoded / "smali/com/plexapp/plex/activities/mobile/MobileVideoPlayerActivity.smali"
        player2 = decoded / "smali/com/plexapp/plex/videoplayer/ui/VideoPlayerActivity2.smali"
        ca = root / "cacert.pem"
        old_ca = decoded / "assets/Resources/cacert.pem"
        for path in (manifest, mobile, player2, old_ca):
            path.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(MANIFEST, encoding="utf-8")
        mobile.write_text(MOBILE, encoding="utf-8")
        player2.write_text(PLAYER2, encoding="utf-8")
        old_ca.write_text("STALE TEST CA\n", encoding="ascii")
        ca.write_text("CURRENT TEST CA\n", encoding="ascii")
        return decoded, ca

    def test_applies_all_required_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decoded, ca = self.make_tree(Path(tmp))
            changed = patch_tree(decoded, ca)

            self.assertEqual(
                changed,
                {"get_tasks_permission": True, "mobile_fullscreen": True,
                 "player2_fullscreen": True, "ca_bundle": True},
            )
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

    def test_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            decoded, ca = self.make_tree(Path(tmp))
            patch_tree(decoded, ca)
            snapshot = {
                path.relative_to(decoded): path.read_bytes()
                for path in decoded.rglob("*") if path.is_file()
            }
            changed = patch_tree(decoded, ca)
            self.assertEqual(
                changed,
                {"get_tasks_permission": False, "mobile_fullscreen": False,
                 "player2_fullscreen": False, "ca_bundle": False},
            )
            self.assertEqual(
                snapshot,
                {path.relative_to(decoded): path.read_bytes()
                 for path in decoded.rglob("*") if path.is_file()},
            )


if __name__ == "__main__":
    unittest.main()
