"""Export the 53-slide web deck (index.html) to a layered, animated PowerPoint (.pptx).

Each slide is decomposed into:
  1. Background layer (JPEG): slide background color, corner ring, chemistry doodles,
     and full-bleed photo/overlay on photo divider slides.
  2. Individual animated element layers (transparent PNG cutouts) with native PowerPoint
     entrance animations matching styles/animations.css (tin, rowin, pop, fade) and
     horizontal push transitions between slides.
  3. Clickable transparent hyperlink overlays matching <a class="src-link"> regions.
  4. Speaker notes containing the slide title, full plain text, and source URLs.
"""

from __future__ import annotations

import io
import os
import re
import sys
from pathlib import Path

from lxml import etree
from PIL import Image
from playwright.sync_api import sync_playwright
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Emu, Inches

SLIDE_W_PX = 1600
SLIDE_H_PX = 900
SLIDE_W_EMU = Emu(12192000)
SLIDE_H_EMU = Emu(6858000)
PX_TO_EMU_X = SLIDE_W_EMU / SLIDE_W_PX
PX_TO_EMU_Y = SLIDE_H_EMU / SLIDE_H_PX

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]

EXPORT_CSS = """
#progress, .edge, .corner-btn, #toc, #srcModal, #imgZoom { display: none !important; }
html body *, html body *::before, html body *::after,
html body #stage .slide, html body #stage .slide *,
html body #stage .slide.active, html body #stage .slide.active *,
html body #stage .slide.active .hl {
  animation: none !important;
  transition: none !important;
}
html body #stage .slide.active .hl { clip-path: none !important; }
html, body {
  width: 1600px !important;
  height: 900px !important;
  overflow: hidden !important;
  margin: 0 !important;
  padding: 0 !important;
}
#viewport {
  position: fixed !important;
  left: 0 !important;
  top: 0 !important;
  width: 1600px !important;
  height: 900px !important;
  display: block !important;
  overflow: hidden !important;
}
#stage {
  position: relative !important;
  left: 0 !important;
  top: 0 !important;
  width: 1600px !important;
  height: 900px !important;
  transform: none !important;
}
.slide {
  border: 0 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
}
.doodle svg { filter: none !important; }
.doodle svg path, .doodle svg circle, .doodle svg ellipse { stroke-dashoffset: 0 !important; }
.donut .ring { stroke-dashoffset: var(--off, 60) !important; }

body.export-bg-only [data-export-target="1"],
body.export-bg-only [data-export-target="1"] * {
  visibility: hidden !important;
}

body.export-cutout,
body.export-cutout::before,
body.export-cutout #viewport,
body.export-cutout #stage,
body.export-cutout .slide {
  background: transparent !important;
}
body.export-cutout::before,
body.export-cutout .slide-inner::after,
body.export-cutout .doodles {
  display: none !important;
}
body.export-cutout .slide-inner,
body.export-cutout .slide-inner * {
  visibility: hidden !important;
}
body.export-cutout [data-export-active="1"],
body.export-cutout [data-export-active="1"] * {
  visibility: visible !important;
}
"""

EXTRACT_TARGETS_JS = """(slideIdx) => {
  const slides = [...document.querySelectorAll('.slide')];
  slides.forEach((s, i) => {
    s.classList.remove('active', 'before');
    s.style.display = (i === slideIdx) ? 'block' : 'none';
    if (i === slideIdx) {
      s.classList.add('active');
      s.style.opacity = '1';
      s.style.transform = 'none';
      s.style.zIndex = '2';
    }
  });

  // Clear previous markers
  document.querySelectorAll('[data-export-target]').forEach(el => el.removeAttribute('data-export-target'));
  document.querySelectorAll('[data-export-active]').forEach(el => el.removeAttribute('data-export-active'));
  document.querySelectorAll('[data-export-idx]').forEach(el => el.removeAttribute('data-export-idx'));

  const slide = slides[slideIdx];
  const inner = slide.querySelector('.slide-inner');
  const cs = getComputedStyle(inner);
  const firstChild = [...inner.children].find(c => !c.classList.contains('doodles'));
  const isFullBleedDivider = parseFloat(cs.paddingTop) === 0 && firstChild && firstChild.classList.contains('imgbig');

  let candidates = [];
  if (isFullBleedDivider) {
    // Keep background photo & dark gradient on background layer; animate foreground text overlay & slide number
    const overlay = [...firstChild.children].filter(el =>
      el.tagName !== 'IMG' && el.textContent.trim().length > 0
    );
    candidates = overlay;
  } else {
    const sel = [
      '.s-head', '.bigtitle', '.statement', '.scope-head', '.col5-head',
      '.sub', '.pt', '.lrow', '.mtr', '.memrow', '.fstep', '.col', '.mcol',
      '.imgbig', '.imgwhite', '.illus', '.stat', '.box', '.foot', '.ts-lv',
      '.fd-step', '.fd-side', '.fd-nd', '.fd-ln', '.newsfr', '.figcap',
      '.mol', '.s-num', '.scope-pill', '[style*="--d"]',
      '.txtcol > p', '.split > div > p'
    ].join(', ');
    candidates = [...inner.querySelectorAll(sel)];
    // Include chip rows on dividers (slides 10, 24)
    inner.querySelectorAll('div').forEach(div => {
      if ([...div.children].some(ch => ch.classList && ch.classList.contains('chip'))) {
        candidates.push(div);
      }
    });
  }

  // Deduplicate: keep order, drop duplicates, drop elements whose ancestor is already selected,
  // and drop full-slide containers or elements inside .doodles
  const unique = [];
  const seen = new Set();
  for (const el of candidates) {
    if (!el || seen.has(el)) continue;
    if (el.closest('.doodles')) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    if (r.width >= 1560 && r.height >= 860 && !isFullBleedDivider) continue;
    seen.add(el);
    unique.push(el);
  }

  const chosen = unique.filter(el => {
    let p = el.parentElement;
    while (p && p !== inner) {
      if (seen.has(p)) return false;
      p = p.parentElement;
    }
    return true;
  });

  // Sort top-to-bottom, left-to-right for clean Z-order & natural fallback order
  chosen.sort((a, b) => {
    const ra = a.getBoundingClientRect();
    const rb = b.getBoundingClientRect();
    if (Math.abs(ra.top - rb.top) > 12) return ra.top - rb.top;
    return ra.left - rb.left;
  });

  const parseDelayVar = (el) => {
    let cur = el;
    while (cur && cur !== inner) {
      const st = cur.getAttribute('style') || '';
      const m = st.match(/--d\\s*:\\s*([0-9.]+)/);
      if (m) return parseFloat(m[1]);
      cur = cur.parentElement;
    }
    return 0;
  };

  const targets = [];
  chosen.forEach((el, idx) => {
    el.setAttribute('data-export-target', '1');
    el.setAttribute('data-export-idx', String(idx));
    const r = el.getBoundingClientRect();

    // Generous padding so neo-brutalist shadows (10px 10px 0) and .hl shadows (6px 6px 0) never clip
    const x1 = Math.max(0, Math.floor(r.left) - 16);
    const y1 = Math.max(0, Math.floor(r.top) - 16);
    const x2 = Math.min(1600, Math.ceil(r.right) + 24);
    const y2 = Math.min(900, Math.ceil(r.bottom) + 24);

    const d = parseDelayVar(el);
    let anim = 'pop';
    let dur = 580;
    let delay = Math.min(40 + Math.round(d * 65), 750);

    if (el.classList.contains('s-head') || el.classList.contains('bigtitle') || el.classList.contains('statement')) {
      anim = 'tin';
      dur = 620;
      delay = el.classList.contains('statement') ? Math.min(30 + Math.round(d * 55), 400) : 0;
    } else if (el.classList.contains('lrow') || el.classList.contains('mtr') || el.classList.contains('memrow')) {
      anim = 'rowin';
      dur = 520;
      delay = el.classList.contains('head') ? 0 : Math.min(60 + Math.round(d * 80), 850);
    } else if (el.classList.contains('fd-ln')) {
      anim = 'fade';
      dur = 450;
      delay = Math.min(260 + Math.round(d * 70), 800);
    } else if (el.classList.contains('s-num') && isFullBleedDivider) {
      anim = 'pop';
      dur = 450;
      delay = 120;
    }

    targets.push({
      idx,
      x: x1,
      y: y1,
      w: Math.max(1, x2 - x1),
      h: Math.max(1, y2 - y1),
      anim,
      dur,
      delay
    });
  });

  // Collect clickable source links
  const links = [];
  inner.querySelectorAll('a.src-link[href]').forEach(a => {
    const r = a.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return;
    links.push({
      x: Math.max(0, r.left - 2),
      y: Math.max(0, r.top - 2),
      w: Math.min(1600 - Math.max(0, r.left - 2), r.width + 4),
      h: Math.min(900 - Math.max(0, r.top - 2), r.height + 4),
      href: a.getAttribute('href'),
      text: a.textContent.trim()
    });
  });

  // Collect clean speaker notes text
  const noteLines = [];
  const title = slide.dataset.title || '';
  const sec = slide.dataset.sec || '';
  if (title) noteLines.push(title + (sec ? ' (' + sec + ')' : ''));
  const rawText = inner.innerText
    .split(/\\n+/)
    .map(s => s.trim())
    .filter(Boolean);
  if (rawText.length) {
    noteLines.push('');
    noteLines.push(...rawText);
  }
  if (links.length) {
    noteLines.push('');
    noteLines.push('Nguồn trích dẫn:');
    links.forEach(l => noteLines.push('- ' + l.text + ': ' + l.href));
  }

  return {
    title,
    targets,
    links,
    notes: noteLines.join('\\n')
  };
}"""


def find_chrome() -> str:
    for path in CHROME_CANDIDATES:
        if os.path.isfile(path):
            return path
    raise FileNotFoundError("Chrome/Edge executable not found in standard Windows paths.")


def optimize_png(png_bytes: bytes) -> bytes:
    im = Image.open(io.BytesIO(png_bytes))
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True, compress_level=9)
    out = buf.getvalue()
    return out if len(out) < len(png_bytes) else png_bytes


def png_to_jpeg(png_bytes: bytes, quality: int = 92) -> bytes:
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality, optimize=True, subsampling=0)
    return buf.getvalue()


def build_transition_xml() -> etree._Element:
    trans = etree.Element(f"{{{P_NS}}}transition", spd="med")
    etree.SubElement(trans, f"{{{P_NS}}}push", dir="l")
    return trans


def build_timing_xml(animated_shapes: list[dict]) -> etree._Element:
    """Build valid OOXML <p:timing> auto-playing all entrance animations on slide entry."""
    timing = etree.Element(f"{{{P_NS}}}timing")
    tn_lst = etree.SubElement(timing, f"{{{P_NS}}}tnLst")

    next_id = 1

    def get_id() -> str:
        nonlocal next_id
        val = str(next_id)
        next_id += 1
        return val

    root_par = etree.SubElement(tn_lst, f"{{{P_NS}}}par")
    root_ctn = etree.SubElement(root_par, f"{{{P_NS}}}cTn", id=get_id(), dur="indefinite", restart="never", nodeType="tmRoot")
    root_children = etree.SubElement(root_ctn, f"{{{P_NS}}}childTnLst")

    seq = etree.SubElement(root_children, f"{{{P_NS}}}seq", concurrent="1", nextAc="seek")
    seq_ctn = etree.SubElement(seq, f"{{{P_NS}}}cTn", id=get_id(), dur="indefinite", nodeType="mainSeq")
    seq_children = etree.SubElement(seq_ctn, f"{{{P_NS}}}childTnLst")

    outer_par = etree.SubElement(seq_children, f"{{{P_NS}}}par")
    outer_ctn = etree.SubElement(outer_par, f"{{{P_NS}}}cTn", id=get_id(), fill="hold")
    outer_st = etree.SubElement(outer_ctn, f"{{{P_NS}}}stCondLst")
    etree.SubElement(outer_st, f"{{{P_NS}}}cond", delay="0")
    outer_children = etree.SubElement(outer_ctn, f"{{{P_NS}}}childTnLst")

    inner_par = etree.SubElement(outer_children, f"{{{P_NS}}}par")
    inner_ctn = etree.SubElement(inner_par, f"{{{P_NS}}}cTn", id=get_id(), fill="hold")
    inner_st = etree.SubElement(inner_ctn, f"{{{P_NS}}}stCondLst")
    etree.SubElement(inner_st, f"{{{P_NS}}}cond", delay="0")
    inner_children = etree.SubElement(inner_ctn, f"{{{P_NS}}}childTnLst")

    for i, item in enumerate(animated_shapes):
        spid = str(item["spid"])
        anim = item["anim"]
        dur = str(item["dur"])
        delay = str(item["delay"])
        node_type = "afterEffect" if i == 0 else "withEffect"

        eff_par = etree.SubElement(inner_children, f"{{{P_NS}}}par")
        eff_ctn = etree.SubElement(
            eff_par,
            f"{{{P_NS}}}cTn",
            id=get_id(),
            presetID="10",
            presetClass="entr",
            presetSubtype="0",
            fill="hold",
            nodeType=node_type,
        )
        eff_st = etree.SubElement(eff_ctn, f"{{{P_NS}}}stCondLst")
        etree.SubElement(eff_st, f"{{{P_NS}}}cond", delay=delay)
        eff_children = etree.SubElement(eff_ctn, f"{{{P_NS}}}childTnLst")

        # 1. Set visibility to visible at t=0
        set_el = etree.SubElement(eff_children, f"{{{P_NS}}}set")
        set_cbhvr = etree.SubElement(set_el, f"{{{P_NS}}}cBhvr")
        set_ctn = etree.SubElement(set_cbhvr, f"{{{P_NS}}}cTn", id=get_id(), dur="1", fill="hold")
        set_st = etree.SubElement(set_ctn, f"{{{P_NS}}}stCondLst")
        etree.SubElement(set_st, f"{{{P_NS}}}cond", delay="0")
        set_tgt = etree.SubElement(set_cbhvr, f"{{{P_NS}}}tgtEl")
        etree.SubElement(set_tgt, f"{{{P_NS}}}spTgt", spid=spid)
        set_attr = etree.SubElement(set_cbhvr, f"{{{P_NS}}}attrNameLst")
        etree.SubElement(set_attr, f"{{{P_NS}}}attrName").text = "style.visibility"
        set_to = etree.SubElement(set_el, f"{{{P_NS}}}to")
        etree.SubElement(set_to, f"{{{P_NS}}}strVal", val="visible")

        # 2. Fade-in effect
        fade_el = etree.SubElement(eff_children, f"{{{P_NS}}}animEffect", transition="in", filter="fade")
        fade_cbhvr = etree.SubElement(fade_el, f"{{{P_NS}}}cBhvr")
        fade_ctn = etree.SubElement(fade_cbhvr, f"{{{P_NS}}}cTn", id=get_id(), dur=dur, fill="hold")
        fade_tgt = etree.SubElement(fade_cbhvr, f"{{{P_NS}}}tgtEl")
        etree.SubElement(fade_tgt, f"{{{P_NS}}}spTgt", spid=spid)

        # 3. Directional motion matching animations.css (pop / tin / rowin)
        if anim in ("pop", "tin", "rowin"):
            if anim == "pop":
                attr_name, start_expr, end_expr = "ppt_y", "#ppt_y+0.032", "#ppt_y"
            elif anim == "tin":
                attr_name, start_expr, end_expr = "ppt_x", "#ppt_x-0.035", "#ppt_x"
            else:  # rowin
                attr_name, start_expr, end_expr = "ppt_x", "#ppt_x-0.018", "#ppt_x"

            anim_el = etree.SubElement(eff_children, f"{{{P_NS}}}anim", calcmode="lin", valueType="num")
            anim_cbhvr = etree.SubElement(anim_el, f"{{{P_NS}}}cBhvr", additive="base")
            anim_ctn = etree.SubElement(anim_cbhvr, f"{{{P_NS}}}cTn", id=get_id(), dur=dur, decel="100000", fill="hold")
            anim_tgt = etree.SubElement(anim_cbhvr, f"{{{P_NS}}}tgtEl")
            etree.SubElement(anim_tgt, f"{{{P_NS}}}spTgt", spid=spid)
            anim_attr = etree.SubElement(anim_cbhvr, f"{{{P_NS}}}attrNameLst")
            etree.SubElement(anim_attr, f"{{{P_NS}}}attrName").text = attr_name
            tav_lst = etree.SubElement(anim_el, f"{{{P_NS}}}tavLst")
            tav0 = etree.SubElement(tav_lst, f"{{{P_NS}}}tav", tm="0")
            val0 = etree.SubElement(tav0, f"{{{P_NS}}}val")
            etree.SubElement(val0, f"{{{P_NS}}}strVal", val=start_expr)
            tav1 = etree.SubElement(tav_lst, f"{{{P_NS}}}tav", tm="100000")
            val1 = etree.SubElement(tav1, f"{{{P_NS}}}val")
            etree.SubElement(val1, f"{{{P_NS}}}strVal", val=end_expr)

    # Sequence navigation conditions
    prev_lst = etree.SubElement(seq, f"{{{P_NS}}}prevCondLst")
    prev_cond = etree.SubElement(prev_lst, f"{{{P_NS}}}cond", evt="onPrev", delay="0")
    etree.SubElement(prev_cond, f"{{{P_NS}}}tgtEl")
    etree.SubElement(prev_cond.find(f"{{{P_NS}}}tgtEl"), f"{{{P_NS}}}sldTgt")

    next_lst = etree.SubElement(seq, f"{{{P_NS}}}nextCondLst")
    next_cond = etree.SubElement(next_lst, f"{{{P_NS}}}cond", evt="onNext", delay="0")
    etree.SubElement(next_cond, f"{{{P_NS}}}tgtEl")
    etree.SubElement(next_cond.find(f"{{{P_NS}}}tgtEl"), f"{{{P_NS}}}sldTgt")

    return timing


def insert_slide_fx(slide, add_transition: bool, animated_shapes: list[dict]) -> None:
    """Insert <p:transition> and <p:timing> in ECMA-376 CT_Slide order (before <p:extLst>)."""
    sld = slide._element
    ext_lst = sld.find(f"{{{P_NS}}}extLst")
    insert_idx = list(sld).index(ext_lst) if ext_lst is not None else len(sld)

    if add_transition:
        sld.insert(insert_idx, build_transition_xml())
        insert_idx += 1

    if animated_shapes:
        sld.insert(insert_idx, build_timing_xml(animated_shapes))


def export_deck(root_dir: Path, out_path: Path) -> None:
    index_url = (root_dir / "index.html").resolve().as_uri()
    chrome_exe = find_chrome()

    prs = Presentation()
    prs.slide_width = SLIDE_W_EMU
    prs.slide_height = SLIDE_H_EMU
    blank_layout = prs.slide_layouts[6]

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chrome_exe)
        page = browser.new_page(viewport={"width": SLIDE_W_PX, "height": SLIDE_H_PX}, device_scale_factor=1)
        page.goto(index_url, wait_until="networkidle")
        page.evaluate("() => document.fonts.ready")
        page.wait_for_timeout(700)
        page.evaluate("() => { if (typeof window.initDoodles === 'function') window.initDoodles(); }")
        page.add_style_tag(content=EXPORT_CSS)
        page.wait_for_timeout(150)

        total = page.evaluate("() => document.querySelectorAll('.slide').length")
        print(f"Exporting {total} slides from {index_url} ...", flush=True)

        for idx in range(total):
            meta = page.evaluate(EXTRACT_TARGETS_JS, idx)
            slide = prs.slides.add_slide(blank_layout)

            # 1. Background layer (JPEG)
            page.evaluate("() => { document.body.classList.remove('export-cutout'); document.body.classList.add('export-bg-only'); }")
            bg_png = page.screenshot(clip={"x": 0, "y": 0, "width": SLIDE_W_PX, "height": SLIDE_H_PX})
            bg_jpg = png_to_jpeg(bg_png, quality=92)
            slide.shapes.add_picture(io.BytesIO(bg_jpg), Emu(0), Emu(0), SLIDE_W_EMU, SLIDE_H_EMU)

            # 2. Animated element cutout layers (transparent PNG)
            page.evaluate("() => { document.body.classList.remove('export-bg-only'); document.body.classList.add('export-cutout'); }")
            animated_shapes = []
            for t in meta["targets"]:
                page.evaluate(
                    "(tIdx) => { const el = document.querySelector('.slide.active [data-export-idx=\"' + tIdx + '\"]'); if (el) el.setAttribute('data-export-active', '1'); }",
                    t["idx"],
                )
                raw_cutout = page.screenshot(
                    clip={"x": t["x"], "y": t["y"], "width": t["w"], "height": t["h"]},
                    omit_background=True,
                )
                page.evaluate(
                    "(tIdx) => { const el = document.querySelector('.slide.active [data-export-idx=\"' + tIdx + '\"]'); if (el) el.removeAttribute('data-export-active'); }",
                    t["idx"],
                )
                opt_cutout = optimize_png(raw_cutout)
                pic = slide.shapes.add_picture(
                    io.BytesIO(opt_cutout),
                    Emu(round(t["x"] * PX_TO_EMU_X)),
                    Emu(round(t["y"] * PX_TO_EMU_Y)),
                    Emu(round(t["w"] * PX_TO_EMU_X)),
                    Emu(round(t["h"] * PX_TO_EMU_Y)),
                )
                animated_shapes.append(
                    {
                        "spid": pic.shape_id,
                        "anim": t["anim"],
                        "dur": t["dur"],
                        "delay": t["delay"],
                    }
                )

            page.evaluate("() => { document.body.classList.remove('export-cutout', 'export-bg-only'); }")

            # 3. Clickable transparent hyperlink hotspots above cutouts
            for link in meta["links"]:
                hs = slide.shapes.add_shape(
                    MSO_SHAPE.RECTANGLE,
                    Emu(round(link["x"] * PX_TO_EMU_X)),
                    Emu(round(link["y"] * PX_TO_EMU_Y)),
                    Emu(max(1, round(link["w"] * PX_TO_EMU_X))),
                    Emu(max(1, round(link["h"] * PX_TO_EMU_Y))),
                )
                hs.fill.background()
                hs.line.fill.background()
                hs.shadow.inherit = False
                hs.click_action.hyperlink.address = link["href"]

            # 4. Speaker notes
            if meta["notes"]:
                slide.notes_slide.notes_text_frame.text = meta["notes"]

            # 5. Slide transition (slides 2..N) + entrance animations
            insert_slide_fx(slide, add_transition=(idx > 0), animated_shapes=animated_shapes)

            if (idx + 1) % 10 == 0 or idx + 1 == total:
                print(f"  Processed slide {idx + 1}/{total} ({len(animated_shapes)} layers, {len(meta['links'])} links)", flush=True)

        browser.close()

    prs.save(str(out_path))
    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"Saved {out_path} ({size_mb:.2f} MB)", flush=True)


def main() -> int:
    root_dir = Path(__file__).resolve().parent.parent
    out_name = "Dinh dưỡng - đề phòng độc tố · Slide thuyết trình.pptx"
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else (root_dir / out_name)
    export_deck(root_dir, out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
