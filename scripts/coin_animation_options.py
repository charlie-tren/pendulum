"""Render the coin mark's candidate hover animations as an animated GIF.

An animation cannot be judged from a description, so this captures frames of
every option running side by side and writes one GIF. Six ideas, all built on
the same mark, all cheap enough to run on a hover.

    python scripts/coin_animation_options.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "site" / "_coin_animations.gif"

FRAMES, STEP_MS = 30, 60          # 1.8s of motion, which covers the longest loop

# Same geometry the real mark uses, inlined so this file stands alone
RX, RY, STEP, BASE = 6.6, 2.6, 4.2, 51.0
STACKS = [("bronze", 13.0, 2), ("silver", 29.0, 3), ("gold", 45.0, 9)]
METAL = {
    "bronze": ("#b06a28", "#d98f45", "#f0b982"),
    "silver": ("#98a2ac", "#c6ced7", "#e3e9ef"),
    "gold": ("#c69a22", "#ecc457", "#f7e2a4"),
}


def stack_svg(metal: str, cx: float, n: int) -> str:
    body, face, edge = METAL[metal]
    top = BASE - (n - 1) * STEP
    coins = "".join(
        f'<g class="coin" style="--i:{i}">'
        f'<path d="M{cx - RX:.2f} {BASE - i * STEP:.2f} L{cx - RX:.2f} {BASE - i * STEP + STEP:.2f} '
        f'A{RX:.2f} {RY:.2f} 0 0 0 {cx + RX:.2f} {BASE - i * STEP + STEP:.2f} '
        f'L{cx + RX:.2f} {BASE - i * STEP:.2f} Z" fill="{body}"/>'
        f'<ellipse cx="{cx:.2f}" cy="{BASE - i * STEP:.2f}" rx="{RX:.2f}" ry="{RY:.2f}" fill="{face}"/>'
        f"</g>"
        for i in range(n)
    )
    return (f'<g class="stack s-{metal}">{coins}'
            f'<ellipse cx="{cx:.2f}" cy="{top:.2f}" rx="{RX - 1.9:.2f}" ry="{RY - 0.8:.2f}" '
            f'fill="none" stroke="{edge}" stroke-width=".5" opacity=".8"/></g>')


MARK = ('<svg viewBox="0 8 58 48">'
        + "".join(stack_svg(m, cx, n) for m, cx, n in STACKS)
        + "</svg>")

OPTIONS = {
    "Lift": """
      .o1 .stack { animation: lift 1.5s ease-in-out infinite; }
      .o1 .s-silver { animation-delay: .12s; } .o1 .s-gold { animation-delay: .24s; }
      @keyframes lift { 0%,100%{transform:translateY(0)} 45%{transform:translateY(-3px)} }""",

    "Stack up": """
      .o2 .coin { animation: rise 1.8s ease-out infinite; animation-delay: calc(var(--i) * .07s); }
      @keyframes rise { 0%{transform:translateY(10px);opacity:0} 22%,100%{transform:none;opacity:1} }""",

    "Topple": """
      .o3 .s-gold { animation: topple 1.9s ease-in-out infinite; transform-origin: 45px 53px; }
      @keyframes topple { 0%,55%{transform:rotate(0)} 72%{transform:rotate(7deg)} 100%{transform:rotate(0)} }""",

    "Shimmer": """
      .o4 .coin ellipse { animation: shine 1.6s ease-in-out infinite;
                          animation-delay: calc(var(--i) * .06s); }
      @keyframes shine { 0%,100%{filter:brightness(1)} 40%{filter:brightness(1.55)} }""",

    "Spin the top": """
      .o5 .s-gold .coin:last-of-type ellipse,
      .o5 .s-silver .coin:last-of-type ellipse,
      .o5 .s-bronze .coin:last-of-type ellipse {
        animation: spin 1.5s ease-in-out infinite; transform-box: fill-box;
        transform-origin: 50% 50%; }
      @keyframes spin { 0%,100%{transform:scaleX(1)} 50%{transform:scaleX(.15)} }""",

    "Grow apart": """
      .o6 .s-bronze { animation: shrink 2s ease-in-out infinite; }
      .o6 .s-gold { animation: grow 2s ease-in-out infinite; }
      .o6 .stack { transform-origin: 50% 53px; }
      @keyframes grow { 0%,100%{transform:scaleY(1)} 50%{transform:scaleY(1.14)} }
      @keyframes shrink { 0%,100%{transform:scaleY(1)} 50%{transform:scaleY(.86)} }""",
}

HTML = """<!doctype html><meta charset="utf-8">
<style>
  * {{ margin:0; box-sizing:border-box; }}
  body {{ background:#131519; color:#e9ecf0; padding:26px 24px;
         font:14px/1.4 -apple-system,"Segoe UI",Roboto,sans-serif; width:940px; }}
  .grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:18px; }}
  .cell {{ border:1px solid #2b2f36; border-radius:12px; background:#1a1d22; padding:14px 16px 11px; }}
  .row {{ display:flex; align-items:center; gap:16px; height:56px; }}
  svg {{ height:46px; width:auto; overflow:visible; flex:none; }}
  .word {{ font:400 29px/1 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif; }}
  .name {{ margin-top:9px; font-size:12px; color:#98a0aa; text-transform:uppercase;
          letter-spacing:.07em; }}
  .coin, .stack {{ transform-box: view-box; }}
  {css}
</style>
<div class="grid">{cells}</div>
"""

CELL = ('<div class="cell"><div class="row {cls}">{mark}<span class="word">Inequality</span></div>'
        '<div class="name">{n}. {name}</div></div>')


def main() -> int:
    css = "".join(OPTIONS.values())
    cells = "".join(
        CELL.format(cls=f"o{i + 1}", mark=MARK, name=name, n=i + 1)
        for i, name in enumerate(OPTIONS)
    )
    tmp = ROOT / "site" / "_anim.html"
    tmp.write_text(HTML.format(css=css, cells=cells), encoding="utf-8")

    shots = []
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": 940, "height": 330}, device_scale_factor=1)
        pg.goto(tmp.as_uri())
        pg.wait_for_timeout(200)
        for i in range(FRAMES):
            path = ROOT / "site" / f"_f{i:02d}.png"
            pg.screenshot(path=str(path))
            shots.append(path)
            pg.wait_for_timeout(STEP_MS)
        br.close()
    tmp.unlink()

    frames = [Image.open(p).convert("P", palette=Image.ADAPTIVE, colors=128) for p in shots]
    frames[0].save(OUT, save_all=True, append_images=frames[1:],
                   duration=STEP_MS, loop=0, optimize=True)
    for p in shots:
        p.unlink()
    print(f"wrote {OUT.relative_to(ROOT)}  {OUT.stat().st_size:,} bytes, {FRAMES} frames")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
