#!/usr/bin/env python3
"""Assert Plex's 16:9 video surface uses the full 1920x720 height."""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")
TARGET_ID = "com.plexapp.android:id/video_surface_view"


def parse_bounds(value: str) -> tuple[int, int, int, int]:
    match = BOUNDS.fullmatch(value)
    if not match:
        raise AssertionError(f"invalid bounds: {value!r}")
    return tuple(map(int, match.groups()))  # type: ignore[return-value]


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} UI_XML")
    root = ET.parse(sys.argv[1]).getroot()
    node = next(
        (n for n in root.iter("node") if n.attrib.get("resource-id") == TARGET_ID),
        None,
    )
    assert node is not None, f"{TARGET_ID} not found"
    left, top, right, bottom = parse_bounds(node.attrib["bounds"])
    width, height = right - left, bottom - top
    assert (top, bottom, height) == (0, 720, 720), (
        f"video is vertically inset: bounds={(left, top, right, bottom)}; "
        "expected full 720px physical height"
    )
    assert abs(width - 1280) <= 2, (
        f"16:9 video width at 720px should be 1280px, got {width}px"
    )
    print(f"PASS: video surface bounds={(left, top, right, bottom)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
