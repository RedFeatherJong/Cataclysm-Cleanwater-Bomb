#!/usr/bin/env python3
"""
generate_icons.py — 从一张 512×512 PNG 生成全平台游戏图标

用法:
    python3 tools/generate_icons.py <源图标.png>

生成:
    data/cataicon.ico           — Windows 图标（多尺寸 ICO）
    build-data/osx/AppIcon.iconset/icon_*.png — macOS 12 尺寸
    android/app/src/main/res/mipmap-*/        — Android launcher 图标
    android/app/src/experimental/res/mipmap-*/ — Android 试验版图标
    android/app/src/experimental/res/drawable/splash.png — 启动画面
"""

import os, sys, struct, shutil
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("需要 Pillow: pip install Pillow")
    sys.exit(1)

REPO = Path(__file__).resolve().parent.parent

SIZES = {
    "windows": [16, 32, 48, 256],
    "macos": {
        16:    "icon_16x16.png",
        32:    "icon_16x16@2x.png",
        32:    "icon_32x32.png",
        64:    "icon_32x32@2x.png",
        128:   "icon_128x128.png",
        256:   "icon_128x128@2x.png",
        256:   "icon_256x256.png",
        512:   "icon_256x256@2x.png",
        512:   "icon_512x512.png",
        1024:  "icon_512x512@2x.png",
    },
    "android": {
        "mdpi":    48,
        "hdpi":    72,
        "xhdpi":   96,
        "xxhdpi":  144,
        "xxxhdpi": 192,
    },
    "splash": 512,
}


def make_ico(src: Image.Image, dst: Path):
    """生成多尺寸 ICO"""
    sizes = [16, 32, 48, 256]
    imgs = [src.resize((s, s), Image.LANCZOS) for s in sizes]

    dst.parent.mkdir(parents=True, exist_ok=True)
    imgs[0].save(
        str(dst), format="ICO", sizes=[(s, s) for s in sizes],
        append_images=imgs[1:], bitmap_format="bmp"
    )
    print(f"  ICO: {dst}")


def make_macos(src: Image.Image, base: Path):
    """生成 macOS iconset"""
    out = base / "build-data" / "osx" / "AppIcon.iconset"
    out.mkdir(parents=True, exist_ok=True)

    done = set()
    for px, fname in SIZES["macos"].items():
        key = (fname, px)
        if key in done:
            continue
        done.add(key)
        img = src.resize((px, px), Image.LANCZOS)
        img.save(str(out / fname), "PNG")
    print(f"  macOS iconset: {out}")


def make_android(src: Image.Image, base: Path):
    """生成 Android mipmap 图标"""
    variants = ["main", "experimental"]

    for var in variants:
        a = base / "android" / "app" / "src" / var / "res"
        for density, px in SIZES["android"].items():
            d = a / f"mipmap-{density}"
            d.mkdir(parents=True, exist_ok=True)

            img = src.resize((px, px), Image.LANCZOS)
            img.save(str(d / "ic_launcher.webp"), "WEBP")
            img.save(str(d / "ic_launcher_foreground.webp"), "WEBP")

    # 启动画面
    splash = base / "android" / "app" / "src" / "experimental" / "res" / "drawable" / "splash.png"
    splash.parent.mkdir(parents=True, exist_ok=True)
    splash_img = src.resize((SIZES["splash"], SIZES["splash"]), Image.LANCZOS)
    splash_img.save(str(splash), "PNG")
    print(f"  Android: {base}/android/app/src/")

    # round launcher
    for var in variants:
        a = base / "android" / "app" / "src" / var / "res"
        for density, px in SIZES["android"].items():
            d = a / f"mipmap-{density}"
            img = src.resize((px, px), Image.LANCZOS)
            img.save(str(d / "ic_launcher_round.webp"), "WEBP")


def main():
    if len(sys.argv) < 2:
        print(__doc__); return

    src_path = Path(sys.argv[1])
    if not src_path.exists():
        print(f"文件不存在: {src_path}"); return

    img = Image.open(str(src_path)).convert("RGBA")
    w, h = img.size
    if w != h:
        img = img.crop((0, 0, min(w, h), min(w, h)))
    if w < 512:
        img = img.resize((512, 512), Image.LANCZOS)

    print(f"源图标: {w}x{h} → {img.size[0]}x{img.size[1]}")
    print()

    make_ico(img, REPO / "data" / "cataicon.ico")
    make_macos(img, REPO)
    make_android(img, REPO)

    print(f"\n完成! 所有图标已生成在 {REPO}/")


if __name__ == "__main__":
    main()
