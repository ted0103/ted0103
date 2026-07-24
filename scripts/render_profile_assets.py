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


def hero(fonts: dict[str, TTFont]) -> str:
    style = """
      .scan,.pulse{transform-box:fill-box;transform-origin:center}.scan{animation:scan 7s ease-in-out infinite}.pulse{animation:pulse 4.5s ease-in-out infinite}
      @keyframes scan{0%,100%{transform:translateX(-180px);opacity:.05}50%{transform:translateX(1180px);opacity:.48}}
      @keyframes pulse{0%,100%{opacity:.35}50%{opacity:1}}
      @media (prefers-reduced-motion:reduce){.scan,.pulse{animation:none}}
    """
    grid = "".join(f'<path d="M0 {y}H1200" stroke="#00A4FF" opacity=".08"/>' for y in range(40, 401, 40))
    grid += "".join(f'<path d="M{x} 0V420" stroke="#00A4FF" opacity=".06"/>' for x in range(40, 1200, 40))
    body = (
        '<defs><linearGradient id="horizon" x1="0" x2="1"><stop stop-color="#00E7F5"/>'
        '<stop offset=".48" stop-color="#00A4FF"/><stop offset="1" stop-color="#000675"/></linearGradient>'
        '<linearGradient id="hero-name-fill" x1="0" x2="1"><stop stop-color="#FFFFFF"/>'
        '<stop offset=".5" stop-color="#00A4FF"/><stop offset="1" stop-color="#00E7F5"/></linearGradient>'
        '<filter id="hero-name-glow" x="35" y="125" width="620" height="125" filterUnits="userSpaceOnUse">'
        '<feGaussianBlur stdDeviation="4.5" result="blur"/><feMerge><feMergeNode in="blur"/>'
        '<feMergeNode in="SourceGraphic"/></feMerge></filter>'
        '<radialGradient id="glow"><stop stop-color="#00E7F5" stop-opacity=".28"/>'
        '<stop offset="1" stop-color="#04044A" stop-opacity="0"/></radialGradient></defs>'
        '<rect width="1200" height="420" rx="8" fill="#020217"/>'
        '<circle cx="870" cy="192" r="320" fill="url(#glow)"/>'
        + grid
        + '<path d="M-40 354C280 182 710 125 1240 238" fill="none" stroke="url(#horizon)" stroke-width="2"/>'
        '<path d="M70 354C335 230 720 186 1138 232" fill="none" stroke="#00A4FF" opacity=".35"/>'
        '<ellipse cx="875" cy="202" rx="255" ry="112" fill="none" stroke="#00E7F5" opacity=".28" transform="rotate(-10 875 202)"/>'
        '<ellipse cx="875" cy="202" rx="330" ry="145" fill="none" stroke="#00A4FF" opacity=".15" transform="rotate(-10 875 202)"/>'
        '<g class="pulse"><circle cx="1080" cy="139" r="5" fill="#00E7F5"/><circle cx="1080" cy="139" r="14" fill="none" stroke="#00E7F5" opacity=".4"/></g>'
        '<g class="scan"><rect x="0" width="150" height="420" fill="#00E7F5" opacity=".08"/></g>'
        '<path d="M52 54H176M52 54V106M1024 54H1148M1148 54V106M52 314V366M52 366H176M1148 314V366M1024 366H1148" stroke="#00E7F5" opacity=".65"/>'
        + outlined(fonts["mono"], "TTH / 0103", 58, 98, 18, "#00E7F5")
        + outlined(
            fonts["display"],
            "TAN TED HANG",
            58,
            223,
            78,
            "url(#hero-name-fill)",
            path_attrs=' stroke="#000675" stroke-width="1.8" paint-order="stroke fill" vector-effect="non-scaling-stroke"',
            group_attrs=' filter="url(#hero-name-glow)"',
        )
        + outlined(fonts["mono"], "INFORMATION SYSTEMS + ARTIFICIAL INTELLIGENCE", 62, 264, 18, "#00A4FF")
        + outlined(fonts["mono"], "MALAYSIA  /  SIGNAL ONLINE", 62, 337, 15, "#FFFFFF")
        + outlined(fonts["mono"], "BUILDING CLEAR SYSTEMS FOR REAL PEOPLE", 1142, 337, 13, "#00E7F5", "end")
    )
    return svg("Tan Ted Hang — signal horizon", "A futuristic cyan and navy signal horizon introducing Tan Ted Hang.", 1200, 420, body, style)


def project(fonts: dict[str, TTFont]) -> str:
    body = (
        '<defs><linearGradient id="projectGlow"><stop stop-color="#00E7F5" stop-opacity=".24"/>'
        '<stop offset="1" stop-color="#04044A" stop-opacity="0"/></linearGradient></defs>'
        '<rect width="1200" height="470" rx="8" fill="#020217"/>'
        '<rect x="24" y="24" width="1152" height="422" fill="none" stroke="#000675"/>'
        '<circle cx="955" cy="228" r="178" fill="url(#projectGlow)"/>'
        '<circle cx="955" cy="228" r="116" fill="none" stroke="#00E7F5"/>'
        '<ellipse cx="955" cy="228" rx="195" ry="70" fill="none" stroke="#00A4FF" transform="rotate(-18 955 228)"/>'
        '<ellipse cx="955" cy="228" rx="155" ry="48" fill="none" stroke="#00A4FF" opacity=".5" transform="rotate(32 955 228)"/>'
        '<circle cx="1121" cy="177" r="7" fill="#00E7F5"/><circle cx="803" cy="278" r="5" fill="#00A4FF"/>'
        '<path d="M63 71H150M63 71V158M63 399H360" stroke="#00E7F5"/>'
        + outlined(fonts["mono"], "FEATURED SYSTEM / 01", 64, 103, 16, "#00E7F5")
        + outlined(fonts["display"], "THE CELESTIAL", 62, 196, 54, "#FFFFFF")
        + outlined(fonts["display"], "ARCHIVE", 62, 255, 54, "#FFFFFF")
        + outlined(fonts["mono"], "A PRIVATE SPACE FOR REFLECTION", 64, 300, 17, "#00A4FF")
        + outlined(fonts["mono"], "78-CARD SYSTEM", 64, 360, 15, "#FFFFFF")
        + outlined(fonts["mono"], "BILINGUAL", 246, 360, 15, "#FFFFFF")
        + outlined(fonts["mono"], "LOCAL-FIRST", 381, 360, 15, "#FFFFFF")
        + outlined(fonts["mono"], "MOBILE + DESKTOP", 542, 360, 15, "#FFFFFF")
        + outlined(fonts["mono"], "CELESTIAL-ARCHIVE / LIVE", 1136, 408, 13, "#00E7F5", "end")
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
        "hero-signal.svg": hero(fonts),
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
