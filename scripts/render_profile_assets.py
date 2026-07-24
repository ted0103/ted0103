#!/usr/bin/env python3
"""Render the profile's self-contained SVG identity assets."""

from __future__ import annotations

import argparse
import hashlib
import html
import tempfile
import urllib.request
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "profile"
FONT_COMMIT = "9fab8b6cc7b2f20376914fd765d918c698c66d75"
FONTS = {
    "display": (
        f"https://raw.githubusercontent.com/google/fonts/{FONT_COMMIT}/ofl/spacegrotesk/SpaceGrotesk%5Bwght%5D.ttf",
        "acad6de1fc93436f5c0f1f4137751ef04f1aea3063e7036535970ffcfbd79f72",
    ),
    "mono": (
        f"https://raw.githubusercontent.com/google/fonts/{FONT_COMMIT}/ofl/ibmplexmono/IBMPlexMono-Regular.ttf",
        "6a3412f058c7d8dfd9170c41e85ade48e5156ecb89356110ca57a0a27734af46",
    ),
}


def fetch_fonts(directory: Path) -> dict[str, TTFont]:
    fonts = {}
    for name, (url, expected) in FONTS.items():
        path = directory / f"{name}.ttf"
        urllib.request.urlretrieve(url, path)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"{name} font checksum mismatch: {actual}")
        font = TTFont(path)
        if name == "display":
            font = instantiateVariableFont(font, {"wght": 650}, inplace=False)
        fonts[name] = font
    return fonts


def outlined(
    font: TTFont,
    value: str,
    x: float,
    y: float,
    size: float,
    fill: str,
    anchor: str = "start",
    path_attrs: str = "",
    group_attrs: str = "",
) -> str:
    cmap = font.getBestCmap()
    glyphs = font.getGlyphSet()
    metrics = font["hmtx"].metrics
    units = font["head"].unitsPerEm
    scale = size / units
    names = [cmap.get(ord(char), ".notdef") for char in value]
    width = sum(metrics[name][0] for name in names) * scale
    cursor = x - (width / 2 if anchor == "middle" else width if anchor == "end" else 0)
    paths = []
    for name in names:
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(pen)
        data = pen.getCommands()
        if data:
            paths.append(
                f'<path d="{data}" transform="translate({cursor:.2f} {y:.2f}) scale({scale:.6f} {-scale:.6f})" fill="{fill}"{path_attrs}/>'
            )
        cursor += metrics[name][0] * scale
    content = "".join(paths)
    return f"<g{group_attrs}>{content}</g>" if group_attrs else content


def svg(title: str, desc: str, width: int, height: int, body: str, style: str = "") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc" '
        f'viewBox="0 0 {width} {height}"><title id="title">{html.escape(title)}</title>'
        f'<desc id="desc">{html.escape(desc)}</desc>'
        f'{f"<style>{style}</style>" if style else ""}{body}</svg>\n'
    )


def label(fonts: dict[str, TTFont], number: str, title: str, meta: str) -> str:
    body = (
        '<defs><linearGradient id="label-title-fill" x1="0" x2="1">'
        '<stop stop-color="#FFFFFF"/><stop offset=".48" stop-color="#00A4FF"/>'
        '<stop offset="1" stop-color="#00E7F5"/></linearGradient>'
        '<filter id="label-title-glow" x="100" y="0" width="760" height="88" filterUnits="userSpaceOnUse">'
        '<feGaussianBlur stdDeviation="2.2" result="blur"/><feMerge><feMergeNode in="blur"/>'
        '<feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'
        '<rect width="1200" height="88" rx="2" fill="#04044A"/>'
        '<path d="M0 87.5H1200" stroke="#00E7F5"/>'
        '<path d="M102 18V70" stroke="#00A4FF" stroke-width="2"/>'
        + outlined(fonts["mono"], number, 28, 59, 34, "#00E7F5")
        + outlined(
            fonts["display"],
            title,
            132,
            61,
            42,
            "url(#label-title-fill)",
            path_attrs=' stroke="#000675" stroke-width="1.1" paint-order="stroke fill" vector-effect="non-scaling-stroke"',
            group_attrs=' filter="url(#label-title-glow)"',
        )
        + outlined(fonts["mono"], meta, 1168, 55, 13, "#00A4FF", "end")
    )
    return svg(f"{number} / {title}", f"Section heading: {title}", 1200, 88, body)


def project(fonts: dict[str, TTFont]) -> str:
    body = (
        '<defs><filter id="project-paper" x="0" y="0" width="100%" height="100%">'
        '<feTurbulence type="fractalNoise" baseFrequency=".75" numOctaves="3" seed="10" result="noise"/>'
        '<feColorMatrix in="noise" type="saturate" values="0" result="grain"/>'
        '<feBlend in="SourceGraphic" in2="grain" mode="multiply"/></filter></defs>'
        '<rect width="1200" height="470" rx="8" fill="#F1EBDD"/>'
        '<g filter="url(#project-paper)" opacity=".16"><rect width="1200" height="470" fill="#F1EBDD"/></g>'
        '<path d="M0 0H282V470H0ZM282 0H510A118 118 0 0 1 628 118V470H282Z" fill="#020217"/>'
        '<path d="M628 0H884V470H628Z" fill="#A38345"/>'
        '<path d="M884 0H1200V470H884Z" fill="#F1EBDD"/>'
        '<path d="M282 0H510A118 118 0 0 1 628 118V178H282Z" fill="#F1EBDD"/>'
        '<circle cx="455" cy="245" r="116" fill="#F1EBDD"/>'
        '<circle cx="455" cy="245" r="82" fill="#020217"/>'
        '<path d="M392 282Q455 185 518 282M406 270Q455 208 504 270M421 259Q455 228 489 259" fill="none" stroke="#A38345" stroke-width="3"/>'
        '<path d="M455 164V326M374 245H536" stroke="#F1EBDD" opacity=".28"/>'
        '<path d="M628 0H884V470H628C720 392 720 78 628 0Z" fill="#04044A"/>'
        '<path d="M834 74l11 28 28 11-28 11-11 28-11-28-28-11 28-11Z" fill="#F1EBDD"/>'
        '<path d="M919 72V194M948 72V194M977 72V194" stroke="#A38345" opacity=".75"/>'
        '<path d="M1062 55l8 20 20 8-20 8-8 20-8-20-20-8 20-8Z" fill="#020217"/>'
        '<path d="M1110 91l5 13 13 5-13 5-5 13-5-13-13-5 13-5Z" fill="#A38345"/>'
        '<path d="M64 72H184M64 400H238" stroke="#A38345" stroke-width="2"/>'
        '<path d="M52 108h12m8 0h12m8 0h12m8 0h12m8 0h12" stroke="#F1EBDD" stroke-width="3"/>'
        + outlined(fonts["mono"], "FEATURED / 01", 62, 58, 15, "#A38345")
        + outlined(fonts["display"], "CELESTIAL", 60, 204, 40, "#F1EBDD")
        + outlined(fonts["display"], "ARCHIVE", 60, 248, 40, "#F1EBDD")
        + outlined(fonts["mono"], "PRIVATE REFLECTION SYSTEM", 61, 294, 13, "#A38345")
        + outlined(fonts["mono"], "78 CARDS  /  BILINGUAL", 62, 355, 13, "#F1EBDD")
        + outlined(fonts["mono"], "LOCAL-FIRST  /  MOBILE + DESKTOP", 62, 382, 13, "#F1EBDD")
        + outlined(fonts["display"], "INNER", 926, 248, 28, "#020217")
        + outlined(fonts["display"], "ORBIT", 926, 282, 28, "#020217")
        + outlined(fonts["mono"], "A QUIET SPACE TO", 927, 333, 13, "#A38345")
        + outlined(fonts["mono"], "READ BETWEEN SIGNALS", 927, 356, 13, "#A38345")
        + outlined(fonts["mono"], "CELESTIAL-ARCHIVE / LIVE", 1146, 422, 12, "#04044A", "end")
    )
    return svg("The Celestial Archive", "Editorial poster for a bilingual, local-first, 78-card reflection experience.", 1200, 470, body)


def typing_static(fonts: dict[str, TTFont]) -> str:
    body = (
        '<rect width="1000" height="64" fill="#04044A"/>'
        '<path d="M0 63.5H1000" stroke="#000675"/>'
        + outlined(fonts["mono"], "INFORMATION SYSTEMS + ARTIFICIAL INTELLIGENCE", 500, 41, 18, "#00E7F5", "middle")
    )
    return svg("Professional introduction", "Information Systems and Artificial Intelligence.", 1000, 64, body)


def tech_stack(fonts: dict[str, TTFont]) -> str:
    style = """
      .cursor{animation:cursor 1.3s steps(1,end) infinite}
      @keyframes cursor{50%{opacity:.25}}
      @media (prefers-reduced-motion:reduce){.cursor{animation:none}}
    """
    body = (
        '<defs><linearGradient id="stack-title-fill" x1="0" x2="1">'
        '<stop stop-color="#00A4FF"/><stop offset="1" stop-color="#00E7F5"/></linearGradient></defs>'
        '<rect width="1200" height="76" fill="#020217"/>'
        '<path d="M24 75.5H1176" stroke="#000675"/>'
        + outlined(fonts["mono"], ">TECH.STACK", 42, 50, 27, "url(#stack-title-fill)")
        + '<rect class="cursor" x="232" y="24" width="4" height="29" fill="#00E7F5"/>'
        + outlined(fonts["mono"], "TOOLS / CURRENT SIGNAL", 1158, 48, 13, "#00A4FF", "end")
    )
    return svg("Tech Stack", "Current languages, development tools, and creative tools.", 1200, 76, body, style)


def render(fonts: dict[str, TTFont]) -> dict[str, str]:
    return {
        "label-profile.svg": label(fonts, "01", "PROFILE", "HUMAN / SYSTEM / PURPOSE"),
        "label-featured.svg": label(fonts, "02", "FEATURED SYSTEM", "CELESTIAL ARCHIVE"),
        "label-capabilities.svg": label(fonts, "03", "CAPABILITIES", "BUILD / LEAD / CREATE"),
        "label-signal.svg": label(fonts, "04", "SIGNAL", "ACTIVITY / CONTACT"),
        "celestial-archive.svg": project(fonts),
        "typing-static.svg": typing_static(fonts),
        "tech-stack.svg": tech_stack(fonts),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if committed assets differ")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="profile-fonts-") as tmp:
        assets = render(fetch_fonts(Path(tmp)))
    if args.check:
        changed = [name for name, content in assets.items() if not (OUT / name).exists() or (OUT / name).read_text() != content]
        if changed:
            raise SystemExit("stale assets: " + ", ".join(changed))
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for name, content in assets.items():
        (OUT / name).write_text(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
