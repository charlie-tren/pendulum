"""Eight animations for the arrows mark, one looping GIF each.

A still cannot show a mechanic, and the mechanic is the whole choice here: the
same two arrows read completely differently depending on whether they drift,
snap, stagger or overshoot. So each option is captured frame by frame and
assembled into a loop at the size the mark actually appears beside the title.

Frames are taken deterministically rather than by waiting: each option is a CSS
animation held at `animation-play-state: paused` with a negative
`animation-delay`, which freezes it at an exact point in its own timeline. A
screenshot per step, then PIL assembles the loop.

    python scripts/polar_anim_options.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "polarisation"

FRAMES = 30
DUR = 1.8          # seconds per loop, matched across options so they compare
W, H = 300, 150

MARK = """
<svg class="m" viewBox="0 0 64 44">
  <g class="l" stroke="#2f6fb2" stroke-width="5.4" stroke-linecap="round"
     stroke-linejoin="round" fill="none">
    <path d="M37 14 H8"/><path d="M15.2 6.8 L8 14 L15.2 21.2"/></g>
  <g class="r" stroke="#c33c3c" stroke-width="5.4" stroke-linecap="round"
     stroke-linejoin="round" fill="none">
    <path d="M27 30 H56"/><path d="M48.8 22.8 L56 30 L48.8 37.2"/></g>
</svg>"""

# each entry is (slug, label, the @keyframes and the rules that use them)
OPTIONS = [
    ("1-drift", "Drift apart and back, as now", """
@keyframes l { 0%,100% { transform: translateX(0) } 50% { transform: translateX(-2.5px) } }
@keyframes r { 0%,100% { transform: translateX(0) } 50% { transform: translateX(2.5px) } }
.l { animation: l var(--d) ease-in-out infinite }
.r { animation: r var(--d) ease-in-out infinite }"""),

    ("2-stagger", "Left leaves, then right follows", """
@keyframes l { 0%,55%,100% { transform: translateX(0) } 25% { transform: translateX(-3.5px) } }
@keyframes r { 0%,45%,100% { transform: translateX(0) } 72% { transform: translateX(3.5px) } }
.l { animation: l var(--d) ease-in-out infinite }
.r { animation: r var(--d) ease-in-out infinite }"""),

    ("3-snap", "Snap apart, drift back", """
@keyframes l { 0% { transform: translateX(0) } 12% { transform: translateX(-4px) }
               100% { transform: translateX(0) } }
@keyframes r { 0% { transform: translateX(0) } 12% { transform: translateX(4px) }
               100% { transform: translateX(0) } }
.l { animation: l var(--d) cubic-bezier(.2,.9,.3,1) infinite }
.r { animation: r var(--d) cubic-bezier(.2,.9,.3,1) infinite }"""),

    ("4-overshoot", "Spring apart, settle back", """
@keyframes l { 0%,100% { transform: translateX(0) }
               35% { transform: translateX(-5px) } 55% { transform: translateX(-1.4px) }
               70% { transform: translateX(-3px) } }
@keyframes r { 0%,100% { transform: translateX(0) }
               35% { transform: translateX(5px) } 55% { transform: translateX(1.4px) }
               70% { transform: translateX(3px) } }
.l { animation: l var(--d) ease-in-out infinite }
.r { animation: r var(--d) ease-in-out infinite }"""),

    ("5-diverge", "Tilt apart, like a hinge", """
@keyframes l { 0%,100% { transform: rotate(0deg) } 50% { transform: rotate(-5deg) } }
@keyframes r { 0%,100% { transform: rotate(0deg) } 50% { transform: rotate(-5deg) } }
.l { animation: l var(--d) ease-in-out infinite; transform-origin: 37px 14px }
.r { animation: r var(--d) ease-in-out infinite; transform-origin: 27px 30px }"""),

    ("6-stretch", "Arrows grow longer, then shorten", """
@keyframes l { 0%,100% { transform: scaleX(1) } 50% { transform: scaleX(1.16) } }
@keyframes r { 0%,100% { transform: scaleX(1) } 50% { transform: scaleX(1.16) } }
.l { animation: l var(--d) ease-in-out infinite; transform-origin: 37px 14px }
.r { animation: r var(--d) ease-in-out infinite; transform-origin: 27px 30px }"""),

    ("7-pass", "They slide past each other and return", """
@keyframes l { 0%,100% { transform: translate(0,0) } 50% { transform: translate(-3px,1.5px) } }
@keyframes r { 0%,100% { transform: translate(0,0) } 50% { transform: translate(3px,-1.5px) } }
.l { animation: l var(--d) ease-in-out infinite }
.r { animation: r var(--d) ease-in-out infinite }"""),

    ("8-fade", "One fades as the other leaves", """
@keyframes l { 0%,100% { transform: translateX(0); opacity: 1 }
               50% { transform: translateX(-3px); opacity: .45 } }
@keyframes r { 0%,100% { transform: translateX(0); opacity: 1 }
               50% { transform: translateX(3px); opacity: .45 } }
.l { animation: l var(--d) ease-in-out infinite }
.r { animation: r var(--d) ease-in-out infinite }"""),
]


def page(css: str) -> str:
    return f"""<!doctype html><meta charset="utf-8">
<style>
  * {{ margin:0 }}
  body {{ width:{W}px; height:{H}px; background:#fbfbfa;
          display:grid; place-items:center; }}
  .m {{ width:150px; height:auto; --d: {DUR}s;
        animation-play-state: paused }}
  .m .l, .m .r {{ transform-box: view-box; animation-play-state: paused }}
  {css}
</style>{MARK}"""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        for slug, label, css in OPTIONS:
            pg.set_content(page(css))
            frames = []
            for i in range(FRAMES):
                # a negative delay holds a paused animation at that exact point
                # of its own timeline, so the capture is deterministic instead
                # of a race against the compositor
                t = -DUR * i / FRAMES
                pg.add_style_tag(content=f".m .l, .m .r {{ animation-delay: {t:.4f}s }}")
                pg.wait_for_timeout(18)
                raw = pg.screenshot()
                frames.append(Image.open(__import__("io").BytesIO(raw)).convert("P",
                              palette=Image.ADAPTIVE, colors=64))
            dst = OUT / f"_anim_{slug}.gif"
            frames[0].save(dst, save_all=True, append_images=frames[1:],
                           duration=int(DUR * 1000 / FRAMES), loop=0, optimize=True)
            made.append((slug, label, dst.stat().st_size))
        b.close()
    for slug, label, size in made:
        print(f"  {slug:14s} {size:>8,} bytes  {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
