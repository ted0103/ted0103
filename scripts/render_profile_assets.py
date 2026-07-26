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


def svg(title: str, desc: str, width: int, height: int, body: str, style: str = "", intrinsic: bool = False) -> str:
    dimensions = f' width="{width}" height="{height}"' if intrinsic else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc" '
        f'viewBox="0 0 {width} {height}"{dimensions}><title id="title">{html.escape(title)}</title>'
        f'<desc id="desc">{html.escape(desc)}</desc>'
        f'{f"<style>{style}</style>" if style else ""}{body}</svg>\n'
    )


def label(fonts: dict[str, TTFont], number: str, title: str, meta: str, animated: bool = False) -> str:
    style = """
      .signal-reveal{animation:signal-reveal 650ms cubic-bezier(.23,1,.32,1) both;transform-box:fill-box;transform-origin:left center}
      .signal-line{stroke-dasharray:640;animation:signal-draw 850ms cubic-bezier(.23,1,.32,1) 120ms both}
      .signal-pulse{animation:signal-pulse 2800ms ease-in-out 900ms infinite;transform-box:fill-box;transform-origin:center}
      @keyframes signal-reveal{from{transform:scaleX(0)}}
      @keyframes signal-draw{from{stroke-dashoffset:640}}
      @keyframes signal-pulse{0%,100%{opacity:.38}50%{opacity:1}}
      @media (prefers-reduced-motion:reduce){.signal-reveal,.signal-line,.signal-pulse{animation:none}}
    """ if animated else ""
    motion_defs = (
        '<clipPath id="signal-title-clip"><rect class="signal-reveal" x="132" y="12" width="400" height="56"/></clipPath>'
        if animated else ""
    )
    title_group = ' clip-path="url(#signal-title-clip)"' if animated else ""
    motion = (
        '<path class="signal-line" d="M560 87.5H1200" stroke="#1E90FF" stroke-width="2"/>'
        '<circle class="signal-pulse" cx="544" cy="44" r="4" fill="#1E90FF"/>'
        if animated else ""
    )
    body = (
        '<defs><linearGradient id="label-bg" x1="0" y1="0" x2="1200" y2="88" gradientUnits="userSpaceOnUse">'
        '<stop stop-color="#1E90FF"/><stop offset="1" stop-color="#FFFFFF"/></linearGradient>'
        + motion_defs
        + '</defs>'
        '<rect width="1200" height="88" rx="2" fill="url(#label-bg)"/>'
        '<path d="M0 0H560V88H0Z" fill="#04044A"/>'
        '<path d="M0 87.5H1200" stroke="#04044A"/>'
        '<path d="M102 18V70" stroke="#FFFFFF" stroke-width="2" opacity=".72"/>'
        + outlined(fonts["mono"], number, 28, 59, 34, "#FFFFFF")
        + outlined(fonts["display"], title, 132, 61, 42, "#FFFFFF", group_attrs=title_group)
        + outlined(fonts["mono"], meta, 1168, 55, 13, "#04044A", "end")
        + motion
    )
    return svg(f"{number} / {title}", f"Section heading: {title}", 1200, 88, body, style)


def glass_label(fonts: dict[str, TTFont], number: str, title: str, meta: str, animated: bool = False) -> str:
    style = """
      .signal-line{stroke-dasharray:720;animation:signal-draw 900ms cubic-bezier(.23,1,.32,1) both}
      .signal-pulse{animation:signal-pulse 2800ms ease-in-out infinite;transform-box:fill-box;transform-origin:center}
      @keyframes signal-draw{from{stroke-dashoffset:720}}
      @keyframes signal-pulse{50%{opacity:.35;transform:scale(.78)}}
      @media (prefers-reduced-motion:reduce){.signal-line,.signal-pulse{animation:none}}
    """ if animated else ""
    motion = (
        '<path class="signal-line" d="M650 96H1160" stroke="#67E7FF" stroke-width="1.5" opacity=".65"/>'
        '<circle class="signal-pulse" cx="630" cy="44" r="4" fill="#67E7FF"/>'
        if animated else ""
    )
    body = (
        '<defs>'
        '<linearGradient id="glass-bg" x1="0" y1="0" x2="1200" y2="120" gradientUnits="userSpaceOnUse">'
        '<stop stop-color="#12345B"/><stop offset=".48" stop-color="#071A39"/><stop offset="1" stop-color="#030A1C"/>'
        '</linearGradient>'
        '<linearGradient id="edge" x1="0" x2="1"><stop stop-color="#67E7FF" stop-opacity=".65"/><stop offset="1" stop-color="#168DFF" stop-opacity=".08"/></linearGradient>'
        '</defs>'
        '<rect x="1" y="1" width="1198" height="118" rx="22" fill="url(#glass-bg)" stroke="#FFFFFF" stroke-opacity=".16"/>'
        '<path d="M22 1H1178" stroke="url(#edge)" stroke-width="2" opacity=".65"/>'
        '<circle cx="54" cy="42" r="18" fill="#67E7FF" fill-opacity=".12" stroke="#67E7FF" stroke-opacity=".36"/>'
        + outlined(fonts["mono"], number, 54, 49, 14, "#67E7FF", "middle")
        + outlined(fonts["mono"], f"{number} / {title}", 92, 46, 14, "#67E7FF")
        + outlined(fonts["display"], meta, 92, 91, 30, "#F5F9FF")
        + motion
    )
    return svg(f"{number} / {title}", f"Section heading: {meta}", 1200, 120, body, style)


def hero_glass(fonts: dict[str, TTFont]) -> str:
    chips = [
        (72, 337, 250, "INFORMATION SYSTEMS + AI"),
        (336, 337, 238, "INDEPENDENT DEVELOPER"),
        (588, 337, 244, "CREATIVE TECHNOLOGIST"),
    ]
    chip_body = ""
    for x, y, width, text in chips:
        chip_body += f'<rect x="{x}" y="{y}" width="{width}" height="44" rx="22" fill="#FFFFFF" fill-opacity=".055" stroke="#FFFFFF" stroke-opacity=".14"/>'
        chip_body += outlined(fonts["mono"], text, x + width / 2, y + 28, 12, "#D6E3F5", "middle")
    body = (
        '<defs>'
        '<linearGradient id="hero-bg" x1="0" y1="0" x2="1200" y2="420" gradientUnits="userSpaceOnUse">'
        '<stop stop-color="#10294B"/><stop offset=".42" stop-color="#071A39"/><stop offset="1" stop-color="#030713"/>'
        '</linearGradient>'
        '<linearGradient id="name-fill" x1="80" x2="900"><stop stop-color="#F8F6EE"/><stop offset=".64" stop-color="#E3F1FF"/><stop offset="1" stop-color="#8BC5EE"/></linearGradient>'
        '<radialGradient id="hero-glow"><stop stop-color="#9FD8FF" stop-opacity=".28"/><stop offset="1" stop-color="#168DFF" stop-opacity="0"/></radialGradient>'
        '<filter id="blur"><feGaussianBlur stdDeviation="34"/></filter>'
        '</defs>'
        '<rect x="1" y="1" width="1198" height="418" rx="28" fill="url(#hero-bg)" stroke="#FFFFFF" stroke-opacity=".16"/>'
        '<path d="M30 1H1170" stroke="#D9F0FF" stroke-opacity=".3"/>'
        '<circle cx="1040" cy="32" r="250" fill="url(#hero-glow)" filter="url(#blur)"/>'
        + outlined(fonts["mono"], "PORTFOLIO  /  MALAYSIA", 72, 64, 13, "#9FD8FF")
        + outlined(fonts["display"], "TAN TED HANG", 72, 211, 82, "url(#name-fill)")
        + outlined(fonts["display"], "Technology with a human point of view.", 74, 267, 25, "#D7E3F4")
        + chip_body
        + '<circle cx="938" cy="360" r="4" fill="#D4B06A"/>'
        + outlined(fonts["mono"], "OPEN TO MEANINGFUL COLLABORATIONS", 954, 365, 11, "#A7B7D0")
    )
    return svg("Tan Ted Hang", "Technology with a human point of view.", 1200, 420, body)


def projects_glass(fonts: dict[str, TTFont]) -> str:
    body = (
        '<defs>'
        '<linearGradient id="card-a" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#F1EBDD"/><stop offset=".47" stop-color="#F1EBDD"/><stop offset=".48" stop-color="#08082D"/><stop offset="1" stop-color="#171069"/></linearGradient>'
        '<linearGradient id="card-b" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#09234A"/><stop offset=".55" stop-color="#06152F"/><stop offset="1" stop-color="#0B79C8"/></linearGradient>'
        '</defs>'
        '<rect width="1200" height="520" fill="#020611"/>'
        '<rect x="18" y="18" width="570" height="484" rx="24" fill="#07162F" stroke="#FFFFFF" stroke-opacity=".16"/>'
        '<rect x="612" y="18" width="570" height="484" rx="24" fill="#07162F" stroke="#FFFFFF" stroke-opacity=".16"/>'
        '<path d="M18 42A24 24 0 0 1 42 18H564A24 24 0 0 1 588 42V294H18Z" fill="url(#card-a)"/>'
        '<path d="M612 42A24 24 0 0 1 636 18H1158A24 24 0 0 1 1182 42V294H612Z" fill="url(#card-b)"/>'
        '<circle cx="303" cy="157" r="93" fill="none" stroke="#FFFFFF" stroke-opacity=".24"/>'
        '<circle cx="303" cy="157" r="58" fill="none" stroke="#FFFFFF" stroke-opacity=".3"/>'
        '<rect x="258" y="112" width="90" height="90" rx="27" fill="#030A1C" fill-opacity=".88" stroke="#FFFFFF" stroke-opacity=".2" transform="rotate(-8 303 157)"/>'
        '<path d="M303 132l7 18 18 7-18 7-7 18-7-18-18-7 18-7Z" fill="#FFFFFF"/>'
        '<path d="M662 18V294M712 18V294M762 18V294M812 18V294M862 18V294M912 18V294M962 18V294M1012 18V294M1062 18V294M1112 18V294M612 68H1182M612 118H1182M612 168H1182M612 218H1182M612 268H1182" stroke="#FFFFFF" stroke-opacity=".07"/>'
        '<circle cx="897" cy="157" r="93" fill="none" stroke="#FFFFFF" stroke-opacity=".22"/>'
        '<circle cx="897" cy="157" r="58" fill="none" stroke="#FFFFFF" stroke-opacity=".28"/>'
        '<rect x="852" y="112" width="90" height="90" rx="27" fill="#030A1C" fill-opacity=".72" stroke="#FFFFFF" stroke-opacity=".2" transform="rotate(-8 897 157)"/>'
        + outlined(fonts["display"], "T", 897, 177, 44, "#FFFFFF", "middle")
        + outlined(fonts["mono"], "FLAGSHIP SYSTEM", 48, 333, 12, "#67E7FF")
        + outlined(fonts["display"], "CELESTIAL ARCHIVE", 48, 383, 33, "#F5F9FF")
        + outlined(fonts["display"], "Bilingual / local-first / 78 cards", 48, 420, 17, "#A7B7D0")
        + outlined(fonts["mono"], "LIVE  /  HTML  /  2026", 48, 465, 11, "#7085A7")
        + outlined(fonts["mono"], "DIGITAL IDENTITY", 642, 333, 12, "#67E7FF")
        + outlined(fonts["display"], "TED'S PERSONAL PORTFOLIO", 642, 383, 31, "#F5F9FF")
        + outlined(fonts["display"], "Liquid glass / Astro / GitHub powered", 642, 420, 17, "#A7B7D0")
        + outlined(fonts["mono"], "CURRENT  /  ASTRO  /  2026", 642, 465, 11, "#7085A7")
    )
    return svg("Selected projects", "Celestial Archive and Ted's Personal Portfolio.", 1200, 520, body)


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


TYPING_LINES = (
    "INFORMATION SYSTEMS + AI",
    "INDEPENDENT DEVELOPMENT",
    "CREATIVE TECHNOLOGY",
    "HUMAN-CENTRED PRODUCTS",
)


def typing_static(fonts: dict[str, TTFont]) -> str:
    body = '<rect width="1000" height="132" rx="14" fill="#071A39"/>'
    for index, line in enumerate(TYPING_LINES):
        body += outlined(fonts["mono"], line, 500, 29 + index * 27, 15, "#DDEEFF", "middle")
    return svg("Professional introduction", ". ".join(TYPING_LINES) + ".", 1000, 132, body)


def typing_animated(fonts: dict[str, TTFont]) -> str:
    windows = ((0, 18, 24, 25), (25, 43, 49, 50), (50, 68, 74, 75), (75, 93, 99, 100))
    styles = [
        ".type{transform-box:fill-box;transform-origin:left center}",
        "@media (prefers-reduced-motion:reduce){.type{animation:none!important}.type-1{transform:scaleX(1)}.type-2,.type-3,.type-4{transform:scaleX(.001)}}",
    ]
    defs = []
    lines = []
    for index, (line, window) in enumerate(zip(TYPING_LINES, windows), start=1):
        start, reveal, hold, end = window
        styles.append(
            f'.type-{index}' + '{animation:type-' + str(index) + ' 16s steps(32,end) infinite}'
            f'@keyframes type-{index}' + '{'
            f'0%,{start}%{{transform:scaleX(.001)}}{reveal}%{{transform:scaleX(1)}}{hold}%{{transform:scaleX(1)}}{end}%,100%{{transform:scaleX(.001)}}'
            '}'
        )
        defs.append(f'<clipPath id="type-{index}"><rect class="type type-{index}" x="200" y="0" width="600" height="72"/></clipPath>')
        lines.append(outlined(fonts["mono"], line, 500, 45, 18, "#DDEEFF", "middle", group_attrs=f' clip-path="url(#type-{index})"'))
    body = (
        '<defs>' + "".join(defs) + '</defs>'
        '<rect width="1000" height="72" rx="14" fill="#071A39"/>'
        '<path d="M24 71.5H976" stroke="#9FD8FF" stroke-opacity=".22"/>'
        + "".join(lines)
    )
    return svg("Animated professional introduction", ". ".join(TYPING_LINES) + ".", 1000, 72, body, "".join(styles))


ACTIVITY_LINE = "Quiet momentum, built one useful commit at a time."


def activity_static(fonts: dict[str, TTFont]) -> str:
    body = (
        '<rect width="1000" height="72" rx="14" fill="#071A39"/>'
        '<path d="M24 71.5H976" stroke="#9FD8FF" stroke-opacity=".22"/>'
        + outlined(fonts["mono"], ACTIVITY_LINE, 500, 45, 18, "#DDEEFF", "middle")
    )
    return svg("Quiet momentum", ACTIVITY_LINE, 1000, 72, body, intrinsic=True)


def activity_animated(fonts: dict[str, TTFont]) -> str:
    style = (
        ".activity-type{animation:activity-type 12s steps(50,end) infinite;transform-box:fill-box;transform-origin:left center}"
        "@keyframes activity-type{0%,3.3333333333%{transform:scaleX(.001)}36.6666666667%,93.3333333333%{transform:scaleX(1)}93.3333333334%,100%{transform:scaleX(.001)}}"
    )
    body = (
        '<defs><clipPath id="activity-clip"><rect class="activity-type" x="224" y="0" width="552" height="72"/></clipPath></defs>'
        '<rect width="1000" height="72" rx="14" fill="#071A39"/>'
        '<path d="M24 71.5H976" stroke="#9FD8FF" stroke-opacity=".22"/>'
        + outlined(
            fonts["mono"],
            ACTIVITY_LINE,
            500,
            45,
            18,
            "#DDEEFF",
            "middle",
            group_attrs=' clip-path="url(#activity-clip)"',
        )
    )
    return svg("Animated quiet momentum", ACTIVITY_LINE, 1000, 72, body, style, intrinsic=True)


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
        "hero-glass.svg": hero_glass(fonts),
        "label-profile.svg": glass_label(fonts, "01", "PROFILE", "THE HUMAN LAYER"),
        "label-featured.svg": glass_label(fonts, "02", "PROJECTS", "SELECTED SYSTEMS"),
        "label-capabilities.svg": glass_label(fonts, "03", "CAPABILITIES", "TOOLS CHOSEN FOR THE IDEA"),
        "label-signal.svg": glass_label(fonts, "04", "SIGNAL", "CONSISTENT MOTION / QUIET MOMENTUM", animated=True),
        "projects-glass.svg": projects_glass(fonts),
        "celestial-archive.svg": project(fonts),
        "typing-static.svg": typing_static(fonts),
        "typing-animated.svg": typing_animated(fonts),
        "activity-static.svg": activity_static(fonts),
        "activity-animated.svg": activity_animated(fonts),
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
