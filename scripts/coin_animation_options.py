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

FRAMES, STEP_MS = 40, 60          # 1.8s of motion, which covers the longest loop

# Same geometry the real mark uses, inlined so this file stands alone
RX, RY, STEP, BASE = 6.6, 2.6, 4.2, 51.0
STACKS = [("bronze", 13.0, 2), ("silver", 29.0, 3), ("gold", 45.0, 9)]
METAL = {
    "bronze": ("#b06a28", "#d98f45", "#f0b982"),
    "silver": ("#98a2ac", "#c6ced7", "#e3e9ef"),
    "gold": ("#c69a22", "#ecc457", "#f7e2a4"),
}


def stack_svg(metal: str, cx: float, n: int) -> str:
    """One stack, each coin its own group so it can move on its own.

    The body of every coin runs STEP + RY tall rather than STEP. At exactly
    STEP it stopped level with the CENTRE of the coin below, leaving the lower
    half of that coin's face sticking out, and a stack of nine rendered as a
    stack of nine visible rings rather than a pile with one face on top. The
    extra RY is the ellipse's own half-height, which is exactly what it takes
    to cover it.
    """
    body, face, edge = METAL[metal]
    top = BASE - (n - 1) * STEP
    coins = "".join(
        f'<g class="coin" style="--i:{i}">'
        f'<path d="M{cx - RX:.2f} {BASE - i * STEP:.2f} '
        f'L{cx - RX:.2f} {BASE - i * STEP + STEP + RY:.2f} '
        f'A{RX:.2f} {RY:.2f} 0 0 0 {cx + RX:.2f} {BASE - i * STEP + STEP + RY:.2f} '
        f'L{cx + RX:.2f} {BASE - i * STEP:.2f} Z" fill="{body}" '
        # the body is outlined, which puts a seam on its BOTTOM arc. That arc is
        # the only part of a buried coin that stays visible once the coin above
        # covers its face, and it is what makes a pile read as coins rather than
        # as one smooth cylinder.
        f'stroke="{edge}" stroke-width=".4" stroke-opacity=".5"/>'
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

# Ten ways of moving a coin between the stacks. The subject of the page is
# wealth changing hands, so every one of these is some version of a coin
# leaving one pile and arriving in another. `--i` is the coin's index up its
# own stack, set on each group, which is what lets a whole stack move in
# sequence rather than as a block.
OPTIONS = {
    "Bronze to gold": """
      .o1 .s-bronze .coin:last-of-type { animation: fly-bg 2s ease-in-out infinite; }
      @keyframes fly-bg { 0%,10%{transform:none} 45%,100%{transform:translate(32px,-22px)} }""",

    "Both to the gold": """
      .o2 .s-bronze .coin:last-of-type { animation: fly-bg 2.2s ease-in-out infinite; }
      .o2 .s-silver .coin:last-of-type { animation: fly-sg 2.2s ease-in-out infinite .2s; }
      @keyframes fly-sg { 0%,10%{transform:none} 45%,100%{transform:translate(16px,-17px)} }""",

    "Round trip": """
      .o3 .s-bronze .coin:last-of-type { animation: trip 2.4s ease-in-out infinite; }
      @keyframes trip { 0%,8%{transform:none} 40%,60%{transform:translate(32px,-22px)}
                        92%,100%{transform:none} }""",

    "Arc over the top": """
      .o4 .s-silver .coin:last-of-type { animation: arc 2s ease-in-out infinite; }
      @keyframes arc { 0%{transform:none} 50%{transform:translate(8px,-26px)}
                       100%{transform:translate(16px,-17px)} }""",

    "Siphon": """
      .o5 .s-bronze .coin, .o5 .s-silver .coin {
        animation: siphon 2.6s ease-in-out infinite;
        animation-delay: calc(var(--i) * .18s); }
      @keyframes siphon { 0%,14%{transform:none;opacity:1}
                          55%{transform:translate(24px,-20px);opacity:.25}
                          70%,100%{transform:none;opacity:1} }""",

    "One at a time, forever": """
      .o6 .s-bronze .coin:last-of-type { animation: fly-bg 1.4s ease-in infinite; }
      .o6 .s-silver .coin:last-of-type { animation: fly-sg 1.4s ease-in infinite .35s; }""",

    "Tipping point": """
      .o7 .s-bronze { animation: drain 2.6s ease-in-out infinite; transform-origin:13px 53px; }
      .o7 .s-gold { animation: swell 2.6s ease-in-out infinite; transform-origin:45px 53px; }
      @keyframes drain { 0%,100%{transform:scaleY(1)} 50%{transform:scaleY(.5)} }
      @keyframes swell { 0%,100%{transform:scaleY(1)} 50%{transform:scaleY(1.18)} }""",

    "Slide along the base": """
      .o8 .s-bronze .coin:first-of-type { animation: slide 2.2s ease-in-out infinite; }
      @keyframes slide { 0%,12%{transform:none} 50%,100%{transform:translateX(32px)} }""",

    "Cascade": """
      .o9 .coin { animation: cascade 2.8s ease-in-out infinite;
                  animation-delay: calc(var(--i) * .1s); }
      @keyframes cascade { 0%,20%{transform:none} 55%{transform:translate(10px,-8px)}
                           85%,100%{transform:none} }""",

    "Poached from the top": """
      .o10 .s-gold .coin:last-of-type { animation: poach 2.4s ease-in-out infinite; }
      @keyframes poach { 0%,10%{transform:none} 45%{transform:translate(-32px,10px)}
                         80%,100%{transform:none} }""",
}

# shared by more than one option above
SHARED = """
  @keyframes fly-bg { 0%,10%{transform:none} 45%,100%{transform:translate(32px,-22px)} }
  @keyframes fly-sg { 0%,10%{transform:none} 45%,100%{transform:translate(16px,-17px)} }
"""

HTML = """<!doctype html><meta charset="utf-8">
<style>
  * {{ margin:0; box-sizing:border-box; }}
  body {{ background:#131519; color:#e9ecf0; padding:26px 24px;
         font:14px/1.4 -apple-system,"Segoe UI",Roboto,sans-serif; width:760px; }}
  .grid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:18px; }}
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


def capture(pg, w, h, out):
    shots = []
    for i in range(FRAMES):
        path = ROOT / "site" / f"_f{i:02d}.png"
        pg.screenshot(path=str(path))
        shots.append(path)
        pg.wait_for_timeout(STEP_MS)
    frames = [Image.open(x).convert("P", palette=Image.ADAPTIVE, colors=96) for x in shots]
    frames[0].save(out, save_all=True, append_images=frames[1:],
                   duration=STEP_MS, loop=0, optimize=True)
    for x in shots:
        x.unlink()
    return out


def main() -> int:
    css = "".join(OPTIONS.values()) + SHARED
    names = list(OPTIONS)

    with sync_playwright() as pw:
        br = pw.chromium.launch()

        # the grid, all six at once
        cells = "".join(CELL.format(cls=f"o{i + 1}", mark=MARK, name=n, n=i + 1)
                        for i, n in enumerate(names))
        tmp = ROOT / "site" / "_anim.html"
        tmp.write_text(HTML.format(css=css, cells=cells), encoding="utf-8")
        pg = br.new_page(viewport={"width": 760, "height": 1100}, device_scale_factor=1)
        pg.goto(tmp.as_uri()); pg.wait_for_timeout(200)
        capture(pg, 760, 1100, OUT)
        pg.close()
        print(f"wrote {OUT.relative_to(ROOT)}  {OUT.stat().st_size:,} bytes")

        # and one file each, larger, because a six-up grid is small to judge
        for i, name in enumerate(names):
            one = CELL.format(cls=f"o{i + 1}", mark=MARK, name=name, n=i + 1)
            tmp.write_text(
                HTML.format(css=css, cells=one).replace("width:760px", "width:430px")
                    .replace("repeat(3,1fr)", "1fr")
                    .replace("height:46px", "height:74px")
                    .replace("font:400 29px/1", "font:400 44px/1")
                    .replace("height:56px", "height:88px"),
                encoding="utf-8")
            pg = br.new_page(viewport={"width": 430, "height": 148}, device_scale_factor=2)
            pg.goto(tmp.as_uri()); pg.wait_for_timeout(200)
            out = ROOT / "site" / f"_coin_anim_{i + 1}.gif"
            capture(pg, 430, 148, out)
            pg.close()
            print(f"  {out.name}  {out.stat().st_size:,} bytes  ({name})")
        br.close()
    tmp.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
