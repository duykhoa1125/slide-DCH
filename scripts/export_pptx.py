"""Export the 53-slide web deck (index.html) to a 100% native editable PowerPoint (.pptx).

Every slide uses real editable PowerPoint text boxes, vector shapes, native lines/arrows,
native hyperlinks, native OOXML shadows, transitions, and staggered entrance animations.
The only raster images embedded in the deck are the actual 44 photos/diagrams from assets/images/.
"""

from __future__ import annotations

import hashlib
import io
import math
import os
import re
import struct
import sys
import urllib.request
from pathlib import Path
from urllib.parse import unquote

from lxml import etree
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.opc.package import Part
from pptx.opc.packuri import PackURI
from pptx.util import Emu, Pt

SLIDE_W_PX = 1600
SLIDE_H_PX = 900
SLIDE_W_EMU = Emu(12192000)
SLIDE_H_EMU = Emu(6858000)
PX_TO_EMU = 7620
PX_TO_PT = 0.60
FONT_SCALE = 0.96

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
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
"""

EXTRACT_SLIDE_JS = """(slideIdx) => {
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

  const slide = slides[slideIdx];
  const inner = slide.querySelector('.slide-inner');
  const slideCs = getComputedStyle(slide);
  const innerCs = getComputedStyle(inner);
  const firstChild = [...inner.children].find(c => !c.classList.contains('doodles'));
  const isFullBleed = parseFloat(innerCs.paddingTop) === 0 && firstChild && firstChild.classList.contains('imgbig');

  // 1. Tag animation groups matching styles/animations.css
  document.querySelectorAll('[data-ag]').forEach(el => el.removeAttribute('data-ag'));

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

  let agCandidates = [];
  if (isFullBleed) {
    agCandidates = [...firstChild.children].filter(el => el.tagName !== 'IMG' && el.textContent.trim().length > 0);
    const snum = inner.querySelector('.s-num');
    if (snum) agCandidates.push(snum);
    inner.querySelectorAll('.hl, svg.floaty').forEach(el => agCandidates.push(el));
  } else {
    const sel = [
      '.s-head', '.bigtitle', '.statement', '.scope-head', '.col5-head',
      '.sub', '.pt', '.lrow', '.mtr', '.memrow', '.fstep', '.col', '.mcol',
      '.imgbig', '.imgwhite', '.illus', '.stat', '.box', '.foot', '.ts-lv',
      '.fd-step', '.fd-side', '.fd-nd', '.fd-ln', '.newsfr', '.figcap',
      '.mol', '.s-num', '.scope-pill', '.tlevels', '[style*="--d"]',
      '.txtcol > div', '.txtcol > p', '.split > div > p',
      '.hl', '.imgbig .cap', '.pt .n', '.fstep .n', '.col .n', '.fd-step .n', 'svg.floaty'
    ].join(', ');
    agCandidates = [...inner.querySelectorAll(sel)];
    inner.querySelectorAll('div').forEach(div => {
      if ([...div.children].some(ch => ch.classList && ch.classList.contains('chip'))) {
        agCandidates.push(div);
      }
    });
  }

  const isDedicatedSubAnim = (el) => el.classList && (
    el.classList.contains('hl') ||
    el.classList.contains('cap') ||
    el.classList.contains('n') ||
    el.classList.contains('floaty')
  );

  const agSeen = new Set();
  const agUnique = [];
  for (const el of agCandidates) {
    if (!el || agSeen.has(el) || el.closest('.doodles')) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    if (r.width >= 1560 && r.height >= 860 && !isFullBleed) continue;
    agSeen.add(el);
    agUnique.push(el);
  }
  const agChosen = agUnique.filter(el => {
    if (isDedicatedSubAnim(el)) return true;
    let p = el.parentElement;
    while (p && p !== inner) {
      if (agSeen.has(p) && !isDedicatedSubAnim(p)) return false;
      p = p.parentElement;
    }
    return true;
  });

  const animGroups = [];
  agChosen.forEach((el, idx) => {
    el.setAttribute('data-ag', String(idx));
    const d = parseDelayVar(el);
    let anim = 'pop';
    let dur = 580;
    let delay = Math.min(40 + Math.round(d * 65), 750);
    let ambient = null;
    if (el.classList.contains('hl')) {
      anim = 'hlsweep';
      dur = 680;
      delay = 280;
      ambient = 'bob';
    } else if (el.classList.contains('cap')) {
      anim = 'capup';
      dur = 700;
      delay = 300;
    } else if (el.classList.contains('n')) {
      anim = 'numdrop';
      dur = 680;
      delay = Math.min(120 + Math.round(d * 130), 820);
    } else if (el.classList.contains('floaty')) {
      anim = 'fade';
      dur = 500;
      delay = 120;
      ambient = 'floaty';
    } else if (el.classList.contains('s-head') || el.classList.contains('bigtitle') || el.classList.contains('statement')) {
      anim = 'tin';
      dur = 640;
      delay = el.classList.contains('statement') ? Math.min(30 + Math.round(d * 55), 400) : 0;
    } else if (el.classList.contains('lrow') || el.classList.contains('mtr') || el.classList.contains('memrow')) {
      anim = 'rowin';
      dur = 540;
      delay = el.classList.contains('head') ? 0 : Math.min(60 + Math.round(d * 80), 850);
    } else if (el.classList.contains('fd-ln')) {
      anim = 'fade';
      dur = 480;
      delay = Math.min(260 + Math.round(d * 70), 800);
    } else if (el.classList.contains('s-num') && isFullBleed) {
      anim = 'pop';
      dur = 450;
      delay = 120;
    }
    animGroups.push({ id: idx, anim, dur, delay, ambient });
  });

  const getAgId = (el) => {
    const host = el.closest('[data-ag]');
    return host ? parseInt(host.getAttribute('data-ag'), 10) : -1;
  };

  // Helpers
  const isBadgeEl = (el) => el && el.classList && (
    el.classList.contains('hl') ||
    el.classList.contains('s-num') ||
    el.classList.contains('chip') ||
    el.classList.contains('scope-pill')
  );

  const parseShadow = (sh) => {
    if (!sh || sh === 'none') return null;
    // Pick the first solid shadow if multiple
    const m = sh.match(/(rgba?\\([^)]+\\))\\s+(-?[0-9.]+)px\\s+(-?[0-9.]+)px\\s+([0-9.]+)px/);
    if (!m) return null;
    return {
      color: m[1],
      dx: parseFloat(m[2]),
      dy: parseFloat(m[3]),
      blur: parseFloat(m[4])
    };
  };

  const hasVisibleBorderSide = (w, c) => parseFloat(w) > 0 && c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent';
  const isZeroAlpha = (c) => !c || c === 'transparent' || /rgba\\([^,]+,[^,]+,[^,]+,\\s*0(\\.0+)?\\s*\\)/.test(c);

  const boxes = [];
  const dividers = [];
  const images = [];
  const badges = [];
  const textBlocks = [];
  const svgItems = [];

  // 2. Collect boxes, dividers, and images in DOM order
  const allEls = [inner, ...inner.querySelectorAll('*')];
  for (const el of allEls) {
    if (el.closest('.doodles') || el.closest('svg')) continue;
    if (el === inner) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 0.5 || r.height < 0.5) continue;

    const agId = getAgId(el);

    if (el.tagName === 'IMG') {
      const parentCard = el.closest('.imgbig, .imgwhite, .fr, .illus');
      let parentRadius = 0;
      let parentBorder = 0;
      if (parentCard) {
        const pcs = getComputedStyle(parentCard);
        parentRadius = parseFloat(pcs.borderTopLeftRadius) || 0;
        parentBorder = parseFloat(pcs.borderTopWidth) || 0;
      }
      const isCapSibling = parentCard && parentCard.classList.contains('imgbig');
      images.push({
        src: el.getAttribute('src') || '',
        x: r.left,
        y: r.top,
        w: r.width,
        h: r.height,
        objectFit: cs.objectFit || 'fill',
        objectPosition: cs.objectPosition || '50% 50%',
        radius: parseFloat(cs.borderTopLeftRadius) || Math.max(0, parentRadius - parentBorder),
        fullBleedImg: !!(isFullBleed && el.closest('.imgbig') === firstChild),
        inImgBig: !!isCapSibling,
        kenburns: !!(el.classList.contains('ph') && parentCard && parentCard.classList.contains('imgbig') && !(isFullBleed && el.closest('.imgbig') === firstChild)),
        agId
      });
      continue;
    }

    if (isBadgeEl(el)) continue; // Badges are emitted separately with their centered text

    const bgGrad = (cs.backgroundImage && cs.backgroundImage.includes('linear-gradient')) ? cs.backgroundImage : null;
    const hasBg = !isZeroAlpha(cs.backgroundColor) || !!bgGrad;
    const bt = hasVisibleBorderSide(cs.borderTopWidth, cs.borderTopColor);
    const bb = hasVisibleBorderSide(cs.borderBottomWidth, cs.borderBottomColor);
    const bl = hasVisibleBorderSide(cs.borderLeftWidth, cs.borderLeftColor);
    const br = hasVisibleBorderSide(cs.borderRightWidth, cs.borderRightColor);
    const fullBorder = bt && bb && bl && br;
    const sh = parseShadow(cs.boxShadow);
    const radius = parseFloat(cs.borderTopLeftRadius) || 0;

    if (hasBg || fullBorder || sh) {
      // Skip inner frame container if parent .slide already has same bg
      const isCap = el.classList.contains('cap') && !!el.closest('.imgbig');
      let capRadius = radius;
      if (isCap) {
        const pCs = getComputedStyle(el.closest('.imgbig'));
        capRadius = Math.max(0, (parseFloat(pCs.borderBottomLeftRadius) || 0) - (parseFloat(pCs.borderBottomWidth) || 0));
      }
      boxes.push({
        x: r.left,
        y: r.top,
        w: r.width,
        h: r.height,
        bg: isZeroAlpha(cs.backgroundColor) ? null : cs.backgroundColor,
        bgGrad,
        borderColor: fullBorder ? cs.borderTopColor : null,
        borderWidth: fullBorder ? parseFloat(cs.borderTopWidth) : 0,
        radius: isCap ? capRadius : radius,
        bottomRoundOnly: isCap,
        shadow: sh,
        isOverlay: !!(isFullBleed && el.parentElement === firstChild && bgGrad),
        isCap,
        agId
      });
    }

    // Partial borders -> crisp thin rectangles
    if (!fullBorder) {
      if (bt) {
        const bw = parseFloat(cs.borderTopWidth);
        dividers.push({ x: r.left, y: r.top, w: r.width, h: Math.max(1, bw), color: cs.borderTopColor, agId });
      }
      if (bb) {
        const bw = parseFloat(cs.borderBottomWidth);
        dividers.push({ x: r.left, y: r.bottom - bw, w: r.width, h: Math.max(1, bw), color: cs.borderBottomColor, agId });
      }
      if (bl) {
        const bw = parseFloat(cs.borderLeftWidth);
        dividers.push({ x: r.left, y: r.top, w: Math.max(1, bw), h: r.height, color: cs.borderLeftColor, agId });
      }
      if (br) {
        const bw = parseFloat(cs.borderRightWidth);
        dividers.push({ x: r.right - bw, y: r.top, w: Math.max(1, bw), h: r.height, color: cs.borderRightColor, agId });
      }
    }
  }

  // 3. Inline run collector for text containers
  const extractInlineRuns = (node, state, runsOut) => {
    if (node.nodeType === Node.TEXT_NODE) {
      let txt = node.nodeValue || '';
      txt = txt.replace(/[ \\t\\r\\n]+/g, ' ');
      if (!txt) return;
      if (state.transform === 'uppercase') txt = txt.toUpperCase();
      runsOut.push({
        text: txt,
        font: state.font,
        sizePx: state.sizePx,
        bold: state.bold,
        italic: state.italic,
        underline: state.underline,
        color: state.color,
        baseline: state.baseline,
        spcPx: state.spcPx,
        href: state.href
      });
      return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return;
    if (node.tagName === 'BR') {
      runsOut.push({ br: true });
      return;
    }
    const cs = getComputedStyle(node);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return;
    const fw = parseInt(cs.fontWeight, 10) || 400;
    const tag = node.tagName;
    let baseline = state.baseline;
    if (tag === 'SUB') baseline = -25000;
    else if (tag === 'SUP') baseline = 30000;
    else if (cs.verticalAlign === 'sub') baseline = -25000;
    else if (cs.verticalAlign === 'super') baseline = 30000;

    const spc = cs.letterSpacing && cs.letterSpacing !== 'normal' ? parseFloat(cs.letterSpacing) : 0;
    const nextState = {
      font: cs.fontFamily || state.font,
      sizePx: parseFloat(cs.fontSize) || state.sizePx,
      bold: fw >= 600,
      italic: cs.fontStyle === 'italic',
      underline: (cs.textDecorationLine || '').includes('underline'),
      color: cs.color || state.color,
      baseline,
      spcPx: spc,
      transform: cs.textTransform || state.transform,
      href: (tag === 'A' && node.getAttribute('href')) ? node.getAttribute('href') : state.href
    };
    for (const ch of node.childNodes) {
      extractInlineRuns(ch, nextState, runsOut);
    }
  };

  const makeState = (el) => {
    const cs = getComputedStyle(el);
    const fw = parseInt(cs.fontWeight, 10) || 400;
    return {
      font: cs.fontFamily,
      sizePx: parseFloat(cs.fontSize),
      bold: fw >= 600,
      italic: cs.fontStyle === 'italic',
      underline: (cs.textDecorationLine || '').includes('underline'),
      color: cs.color,
      baseline: 0,
      spcPx: cs.letterSpacing && cs.letterSpacing !== 'normal' ? parseFloat(cs.letterSpacing) : 0,
      transform: cs.textTransform || 'none',
      href: (el.tagName === 'A' && el.getAttribute('href')) ? el.getAttribute('href') : null
    };
  };

  const runsToParagraphs = (runs) => {
    const paras = [[]];
    for (const r of runs) {
      if (r.br) {
        paras.push([]);
      } else {
        const cur = paras[paras.length - 1];
        if (cur.length === 0) {
          r.text = r.text.replace(/^ +/, '');
        }
        if (r.text) cur.push(r);
      }
    }
    for (const p of paras) {
      if (p.length > 0) p[p.length - 1].text = p[p.length - 1].text.replace(/ +$/, '');
    }
    return paras.filter(p => p.some(r => r.text.length > 0));
  };

  const emitBadge = (el) => {
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return;
    const cs = getComputedStyle(el);
    const bt = hasVisibleBorderSide(cs.borderTopWidth, cs.borderTopColor);
    const sh = parseShadow(cs.boxShadow);
    const runs = [];
    extractInlineRuns(el, makeState(el), runs);
    const paras = runsToParagraphs(runs);
    if (!paras.length) return;
    badges.push({
      x: r.left,
      y: r.top,
      w: r.width,
      h: r.height,
      bg: isZeroAlpha(cs.backgroundColor) ? null : cs.backgroundColor,
      borderColor: bt ? cs.borderTopColor : null,
      borderWidth: bt ? parseFloat(cs.borderTopWidth) : 0,
      radius: parseFloat(cs.borderTopLeftRadius) || 0,
      shadow: sh,
      padL: parseFloat(cs.paddingLeft) || 0,
      padR: parseFloat(cs.paddingRight) || 0,
      padT: parseFloat(cs.paddingTop) || 0,
      padB: parseFloat(cs.paddingBottom) || 0,
      paras,
      agId: getAgId(el)
    });
  };

  // Emit all badges cleanly
  inner.querySelectorAll('.hl, .s-num, .chip, .scope-pill').forEach(el => {
    if (el.closest('.doodles') || el.closest('svg')) return;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return;
    emitBadge(el);
  });

  // Walk text containers cleanly without duplicating inline descendants or merging grid/block children
  const consumedInline = new Set();
  const isBlockChild = (node) => {
    if (node.nodeType !== Node.ELEMENT_NODE) return false;
    if (node.tagName === 'BR' || isBadgeEl(node)) return false;
    const ncs = getComputedStyle(node);
    return ncs.display !== 'inline' && ncs.display !== 'inline-block';
  };

  const trimTextBoxBounds = (el, r) => {
    const cs = getComputedStyle(el);
    const pl = parseFloat(cs.paddingLeft) || 0;
    const pr = parseFloat(cs.paddingRight) || 0;
    const pt = parseFloat(cs.paddingTop) || 0;
    const pb = parseFloat(cs.paddingBottom) || 0;
    return {
      x: r.left + pl,
      y: r.top + pt,
      w: Math.max(4, r.width - pl - pr),
      h: Math.max(4, r.height - pt - pb)
    };
  };

  for (const el of inner.querySelectorAll('*')) {
    if (consumedInline.has(el)) continue;
    if (el.closest('.doodles') || el.closest('svg') || isBadgeEl(el) || el.closest('.hl, .s-num, .chip, .scope-pill')) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) continue;

    let hasDirectInlineText = false;
    let hasBlockChildren = false;
    const hasEmbeddedBadge = !!el.querySelector('.hl, .s-num, .chip, .scope-pill');
    for (const ch of el.childNodes) {
      if (ch.nodeType === Node.TEXT_NODE && ch.nodeValue.trim().length > 0) {
        hasDirectInlineText = true;
      } else if (ch.nodeType === Node.ELEMENT_NODE) {
        if (isBadgeEl(ch)) {
          // badge itself handled separately
        } else if (isBlockChild(ch)) {
          hasBlockChildren = true;
        } else if (ch.tagName !== 'BR' && ch.textContent.trim().length > 0) {
          hasDirectInlineText = true;
        }
      }
    }

    if (!hasDirectInlineText) continue;

    const agId = getAgId(el);
    const baseState = makeState(el);

    if (!hasEmbeddedBadge && !hasBlockChildren) {
      const r = el.getBoundingClientRect();
      if (r.width < 1 || r.height < 1) continue;
      el.querySelectorAll('*').forEach(d => consumedInline.add(d));
      const box = trimTextBoxBounds(el, r);
      const runs = [];
      extractInlineRuns(el, baseState, runs);
      const paras = runsToParagraphs(runs);
      if (!paras.length) continue;
      const fs = parseFloat(cs.fontSize) || 24;
      const lh = parseFloat(cs.lineHeight);
      const lhRatio = (!isNaN(lh) && fs > 0) ? (lh / fs) : 1.3;
      textBlocks.push({
        ...box,
        align: cs.textAlign || 'left',
        lhRatio,
        singleLine: false,
        paras,
        agId
      });
    } else {
      // Extract only direct text / inline-flow nodes outside badges and outside separate block children
      const lines = [];
      const addNodeRects = (node, state) => {
        if (node.nodeType === Node.TEXT_NODE) {
          const raw = node.nodeValue || '';
          if (!raw.trim()) return;
          let i = 0;
          const len = raw.length;
          while (i < len) {
            while (i < len && /\\s/.test(raw[i])) i++;
            if (i >= len) break;
            let j = i + 1;
            const range = document.createRange();
            range.setStart(node, i);
            range.setEnd(node, j);
            let prevRects = range.getClientRects();
            while (j < len) {
              range.setEnd(node, j + 1);
              const rects = range.getClientRects();
              if (rects.length > 1) {
                range.setEnd(node, j);
                prevRects = range.getClientRects();
                break;
              }
              prevRects = rects;
              j++;
            }
            if (prevRects.length > 0) {
              const rc = prevRects[0];
              let piece = raw.slice(i, j).replace(/[ \\t\\r\\n]+/g, ' ');
              if (state.transform === 'uppercase') piece = piece.toUpperCase();
              piece = piece.trim();
              if (piece) {
                lines.push({
                  x: rc.left,
                  y: rc.top,
                  w: rc.width,
                  h: rc.height,
                  runs: [{ ...state, text: piece }]
                });
              }
            }
            i = j;
          }
        } else if (node.nodeType === Node.ELEMENT_NODE) {
          if (isBadgeEl(node) || isBlockChild(node) || node.tagName === 'BR') return;
          consumedInline.add(node);
          const ncs = getComputedStyle(node);
          if (ncs.display === 'none' || ncs.visibility === 'hidden' || parseFloat(ncs.opacity) === 0) return;
          const fw = parseInt(ncs.fontWeight, 10) || 400;
          const nextState = {
            font: ncs.fontFamily || state.font,
            sizePx: parseFloat(ncs.fontSize) || state.sizePx,
            bold: fw >= 600,
            italic: ncs.fontStyle === 'italic',
            underline: (ncs.textDecorationLine || '').includes('underline'),
            color: ncs.color || state.color,
            baseline: node.tagName === 'SUB' ? -25000 : (node.tagName === 'SUP' ? 30000 : 0),
            spcPx: ncs.letterSpacing && ncs.letterSpacing !== 'normal' ? parseFloat(ncs.letterSpacing) : 0,
            transform: ncs.textTransform || state.transform,
            href: (node.tagName === 'A' && node.getAttribute('href')) ? node.getAttribute('href') : state.href
          };
          for (const ch of node.childNodes) addNodeRects(ch, nextState);
        }
      };
      for (const ch of el.childNodes) addNodeRects(ch, baseState);
      for (const seg of lines) {
        const cleanRuns = seg.runs.map(r => ({
          text: r.text,
          font: r.font,
          sizePx: r.sizePx,
          bold: r.bold,
          italic: r.italic,
          underline: r.underline,
          color: r.color,
          baseline: r.baseline,
          spcPx: r.spcPx,
          href: r.href
        }));
        textBlocks.push({
          x: seg.x,
          y: seg.y,
          w: seg.w,
          h: seg.h,
          align: 'left',
          lhRatio: 1.08,
          singleLine: true,
          paras: [cleanRuns],
          agId
        });
      }
    }
  }

  // 4. Extract vector primitives from non-doodle SVGs (slides 9, 30, 50, 53)
  const mapSvgPt = (svg, ctm, x, y) => {
    const pt = svg.createSVGPoint();
    pt.x = x;
    pt.y = y;
    const res = pt.matrixTransform(ctm);
    return [res.x, res.y];
  };

  inner.querySelectorAll('svg').forEach(svg => {
    if (svg.closest('.doodles')) return;
    const svgCtm = svg.getScreenCTM();
    if (!svgCtm) return;
    const rootScale = Math.hypot(svgCtm.a, svgCtm.b) || 1;

    svg.querySelectorAll('rect, circle, line, path, text').forEach(node => {
      if (node.closest('defs') || node.closest('marker')) return;
      const ctm = node.getScreenCTM() || svgCtm;
      const scale = Math.hypot(ctm.a, ctm.b) || rootScale;
      const cs = getComputedStyle(node);
      if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return;
      const agId = getAgId(node);
      const tag = node.tagName.toLowerCase();
      const fill = (!cs.fill || cs.fill === 'none' || isZeroAlpha(cs.fill)) ? null : cs.fill;
      const stroke = (!cs.stroke || cs.stroke === 'none' || isZeroAlpha(cs.stroke)) ? null : cs.stroke;
      const strokeW = stroke ? (parseFloat(cs.strokeWidth) || 1) * scale : 0;

      if (tag === 'rect') {
        const x0 = parseFloat(node.getAttribute('x') || 0);
        const y0 = parseFloat(node.getAttribute('y') || 0);
        const rw = parseFloat(node.getAttribute('width') || 0);
        const rh = parseFloat(node.getAttribute('height') || 0);
        const rx = parseFloat(node.getAttribute('rx') || 0) * scale;
        const [px1, py1] = mapSvgPt(svg, ctm, x0, y0);
        const [px2, py2] = mapSvgPt(svg, ctm, x0 + rw, y0 + rh);
        svgItems.push({
          kind: 'rect',
          x: Math.min(px1, px2),
          y: Math.min(py1, py2),
          w: Math.abs(px2 - px1),
          h: Math.abs(py2 - py1),
          rx,
          fill,
          stroke,
          strokeWidth: strokeW,
          agId
        });
      } else if (tag === 'circle') {
        const cx = parseFloat(node.getAttribute('cx') || 0);
        const cy = parseFloat(node.getAttribute('cy') || 0);
        const cr = parseFloat(node.getAttribute('r') || 0);
        const [px1, py1] = mapSvgPt(svg, ctm, cx - cr, cy - cr);
        const [px2, py2] = mapSvgPt(svg, ctm, cx + cr, cy + cr);
        svgItems.push({
          kind: 'circle',
          x: Math.min(px1, px2),
          y: Math.min(py1, py2),
          w: Math.abs(px2 - px1),
          h: Math.abs(py2 - py1),
          fill,
          stroke,
          strokeWidth: strokeW,
          agId
        });
      } else if (tag === 'line') {
        const [px1, py1] = mapSvgPt(svg, ctm, parseFloat(node.getAttribute('x1') || 0), parseFloat(node.getAttribute('y1') || 0));
        const [px2, py2] = mapSvgPt(svg, ctm, parseFloat(node.getAttribute('x2') || 0), parseFloat(node.getAttribute('y2') || 0));
        svgItems.push({
          kind: 'line',
          x1: px1, y1: py1, x2: px2, y2: py2,
          stroke: stroke || '#16130F',
          strokeWidth: strokeW || (2 * scale),
          markerStart: !!node.getAttribute('marker-start'),
          markerEnd: !!node.getAttribute('marker-end'),
          agId
        });
      } else if (tag === 'path') {
        const d = (node.getAttribute('d') || '').trim();
        const mStart = !!node.getAttribute('marker-start');
        const mEnd = !!node.getAttribute('marker-end');
        const tokens = d.match(/[MLHVmlhv]|-?[0-9]*\\.?[0-9]+/g) || [];
        let ti = 0;
        let cmd = '';
        let cx = 0, cy = 0;
        const pts = [];
        while (ti < tokens.length) {
          if (/^[MLHVmlhv]$/.test(tokens[ti])) {
            cmd = tokens[ti++];
          }
          if (cmd === 'M' || cmd === 'L') {
            cx = parseFloat(tokens[ti++]);
            cy = parseFloat(tokens[ti++]);
            pts.push([cx, cy]);
          } else if (cmd === 'm' || cmd === 'l') {
            cx += parseFloat(tokens[ti++]);
            cy += parseFloat(tokens[ti++]);
            pts.push([cx, cy]);
          } else if (cmd === 'H') {
            cx = parseFloat(tokens[ti++]);
            pts.push([cx, cy]);
          } else if (cmd === 'h') {
            cx += parseFloat(tokens[ti++]);
            pts.push([cx, cy]);
          } else if (cmd === 'V') {
            cy = parseFloat(tokens[ti++]);
            pts.push([cx, cy]);
          } else if (cmd === 'v') {
            cy += parseFloat(tokens[ti++]);
            pts.push([cx, cy]);
          } else {
            ti++;
          }
        }
        for (let k = 0; k + 1 < pts.length; k++) {
          const [px1, py1] = mapSvgPt(svg, ctm, pts[k][0], pts[k][1]);
          const [px2, py2] = mapSvgPt(svg, ctm, pts[k + 1][0], pts[k + 1][1]);
          svgItems.push({
            kind: 'line',
            x1: px1, y1: py1, x2: px2, y2: py2,
            stroke: stroke || '#16130F',
            strokeWidth: strokeW || (2 * scale),
            markerStart: (k === 0) && mStart,
            markerEnd: (k === pts.length - 2) && mEnd,
            agId
          });
        }
      } else if (tag === 'text') {
        const rc = node.getBoundingClientRect();
        const anchor = cs.textAnchor || node.getAttribute('text-anchor') || 'start';
        const baseColor = fill || '#16130F';
        const baseFont = cs.fontFamily || 'Be Vietnam Pro';
        const baseFs = (parseFloat(cs.fontSize) || 18) * scale;
        const baseFw = (parseInt(cs.fontWeight, 10) || 400) >= 600;
        const runs = [];
        for (const ch of node.childNodes) {
          if (ch.nodeType === Node.TEXT_NODE) {
            const t = ch.nodeValue;
            if (t && t.trim()) {
              runs.push({ text: t, font: baseFont, sizePx: baseFs, bold: baseFw, italic: false, underline: false, color: baseColor, baseline: 0, spcPx: 0, href: null });
            }
          } else if (ch.nodeType === Node.ELEMENT_NODE && ch.tagName.toLowerCase() === 'tspan') {
            const dy = parseFloat(ch.getAttribute('dy') || 0);
            const tcs = getComputedStyle(ch);
            const tfs = (parseFloat(tcs.fontSize) || parseFloat(cs.fontSize) || 14) * scale;
            const t = ch.textContent;
            if (t && t.trim()) {
              runs.push({
                text: t,
                font: tcs.fontFamily || baseFont,
                sizePx: tfs,
                bold: (parseInt(tcs.fontWeight, 10) || 400) >= 600 || baseFw,
                italic: false,
                underline: false,
                color: (!tcs.fill || tcs.fill === 'none') ? baseColor : tcs.fill,
                baseline: dy > 0 ? -25000 : (dy < 0 ? 30000 : 0),
                spcPx: 0,
                href: null
              });
            }
          }
        }
        if (runs.length) {
          // Give center/middle text wide centered box so it never clips or wraps
          let bx = rc.left;
          let bw = rc.width + 12;
          let align = 'left';
          if (anchor === 'middle') {
            const cx = rc.left + rc.width / 2;
            bw = Math.max(rc.width + 36, 48);
            bx = cx - bw / 2;
            align = 'center';
          }
          svgItems.push({
            kind: 'text',
            x: bx,
            y: rc.top - 2,
            w: bw,
            h: rc.height + 6,
            align,
            runs,
            agId
          });
        }
      }
    });
  });

  // 4b. Extract background chemistry doodles as vector polylines with ambient drift metadata
  const doodleItems = [];
  const SVG_NS = 'http://www.w3.org/2000/svg';
  inner.querySelectorAll('.doodles .doodle').forEach((dEl, dIdx) => {
    const svg = dEl.querySelector('svg');
    if (!svg) return;
    const dcs = getComputedStyle(dEl);
    const dColor = dcs.color;
    const dOp = parseFloat(dcs.opacity) || 0.15;
    const durMs = Math.round((parseFloat(dEl.style.animationDuration) || 7) * 1000);
    const svgCtm = svg.getScreenCTM();
    if (!svgCtm) return;
    const baseScale = Math.hypot(svgCtm.a, svgCtm.b) || 1;
    const strokeW = 3.4 * baseScale;

    svg.querySelectorAll('path, circle, ellipse').forEach(node => {
      const ctm = node.getScreenCTM() || svgCtm;
      const tag = node.tagName.toLowerCase();
      if (tag === 'path') {
        const rawD = (node.getAttribute('d') || '').trim();
        const subpaths = rawD.split(/(?=[Mm])/).filter(s => s.trim().length > 0);
        for (const sp of subpaths) {
          const tmp = document.createElementNS(SVG_NS, 'path');
          tmp.setAttribute('d', sp);
          svg.appendChild(tmp);
          try {
            const totalLen = tmp.getTotalLength();
            if (totalLen > 1) {
              const steps = Math.max(8, Math.min(28, Math.ceil(totalLen / 4)));
              const pts = [];
              for (let s = 0; s <= steps; s++) {
                const pt = tmp.getPointAtLength((s / steps) * totalLen);
                const tp = pt.matrixTransform(ctm);
                pts.push([tp.x, tp.y]);
              }
              doodleItems.push({
                dIdx,
                pts,
                closed: /[Zz]\\s*$/.test(sp.trim()),
                color: dColor,
                opacity: dOp,
                strokeW,
                durMs
              });
            }
          } finally {
            tmp.remove();
          }
        }
      } else if (tag === 'circle' || tag === 'ellipse') {
        try {
          const totalLen = node.getTotalLength();
          if (totalLen > 1) {
            const steps = 24;
            const pts = [];
            for (let s = 0; s < steps; s++) {
              const pt = node.getPointAtLength((s / steps) * totalLen);
              const tp = pt.matrixTransform(ctm);
              pts.push([tp.x, tp.y]);
            }
            doodleItems.push({
              dIdx,
              pts,
              closed: true,
              color: dColor,
              opacity: dOp,
              strokeW,
              durMs
            });
          }
        } catch (e) {}
      }
    });
  });

  // 5. Speaker notes
  const noteLines = [];
  const title = slide.dataset.title || '';
  const sec = slide.dataset.sec || '';
  if (title) noteLines.push(title + (sec ? ' (' + sec + ')' : ''));
  const rawText = inner.innerText.split(/\\n+/).map(s => s.trim()).filter(Boolean);
  if (rawText.length) {
    noteLines.push('');
    noteLines.push(...rawText);
  }
  const srcLinks = [];
  inner.querySelectorAll('a.src-link[href]').forEach(a => {
    srcLinks.push({ text: a.textContent.trim(), href: a.getAttribute('href') });
  });
  if (srcLinks.length) {
    noteLines.push('');
    noteLines.push('Nguồn trích dẫn:');
    srcLinks.forEach(l => noteLines.push('- ' + l.text + ': ' + l.href));
  }

  return {
    bgColor: slideCs.backgroundColor,
    isFullBleed,
    animGroups,
    boxes,
    dividers,
    images,
    badges,
    textBlocks,
    svgItems,
    doodleItems,
    notes: noteLines.join('\\n')
  };
}"""


def find_chrome() -> str:
    for path in CHROME_CANDIDATES:
        if os.path.isfile(path):
            return path
    raise FileNotFoundError("Chrome/Edge executable not found in standard Windows paths.")


def parse_color(css_color: str | None) -> tuple[RGBColor, float] | None:
    if not css_color or css_color == "transparent":
        return None
    m = re.match(r"rgba?\(\s*(\d+),\s*(\d+),\s*(\d+)(?:,\s*([0-9.]+))?\s*\)", css_color)
    if not m:
        return None
    r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
    a = float(m.group(4)) if m.group(4) is not None else 1.0
    if a <= 0.001:
        return None
    return RGBColor(r, g, b), max(0.0, min(1.0, a))


def map_font(font_family: str) -> str:
    low = (font_family or "").lower()
    if "ibm plex mono" in low or "monospace" in low:
        return "IBM Plex Mono"
    if "archivo" in low:
        return "Archivo"
    return "Be Vietnam Pro"


def emu(px: float) -> Emu:
    return Emu(round(px * PX_TO_EMU))


def set_solid_fill_alpha(fill_obj, rgb: RGBColor, alpha: float) -> None:
    fill_obj.solid()
    fill_obj.fore_color.rgb = rgb
    if alpha < 0.999:
        sp_pr = fill_obj._xPr
        solid = sp_pr.find(f"{{{A_NS}}}solidFill")
        if solid is not None and len(solid):
            clr = solid[0]
            for old in clr.findall(f"{{{A_NS}}}alpha"):
                clr.remove(old)
            etree.SubElement(clr, f"{{{A_NS}}}alpha", val=str(int(round(alpha * 100000))))


def set_linear_gradient(shape, css_grad: str) -> bool:
    stops = re.findall(r"(rgba?\([^)]+\))\s*([0-9.]+%)?", css_grad)
    if len(stops) < 2:
        return False
    parsed_stops = []
    n = len(stops)
    for idx, (col_str, pos_str) in enumerate(stops):
        parsed = parse_color(col_str)
        if not parsed:
            rgb, alpha = RGBColor(0, 0, 0), 0.0
        else:
            rgb, alpha = parsed
        if pos_str and pos_str.endswith("%"):
            pos_val = int(round(float(pos_str[:-1]) * 1000))
        else:
            pos_val = int(round((idx / (n - 1)) * 100000))
        parsed_stops.append((pos_val, rgb, alpha))

    # Determine angle (90deg / to right -> ang=0 in OOXML; 180deg / to bottom -> ang=5400000)
    ang = 5400000
    m_deg = re.search(r"(-?[0-9.]+)deg", css_grad)
    if m_deg:
        deg = float(m_deg.group(1))
        ooxml_deg = (deg - 90.0) % 360.0
        ang = int(round(ooxml_deg * 60000))
    elif "to right" in css_grad:
        ang = 0

    sp_pr = shape._element.spPr
    for tag in ("noFill", "solidFill", "gradFill"):
        old = sp_pr.find(f"{{{A_NS}}}{tag}")
        if old is not None:
            sp_pr.remove(old)

    grad_fill = etree.Element(f"{{{A_NS}}}gradFill")
    gs_lst = etree.SubElement(grad_fill, f"{{{A_NS}}}gsLst")
    for pos_val, rgb, alpha in parsed_stops:
        gs = etree.SubElement(gs_lst, f"{{{A_NS}}}gs", pos=str(max(0, min(100000, pos_val))))
        srgb = etree.SubElement(gs, f"{{{A_NS}}}srgbClr", val=f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}")
        etree.SubElement(srgb, f"{{{A_NS}}}alpha", val=str(int(round(alpha * 100000))))
    etree.SubElement(grad_fill, f"{{{A_NS}}}lin", ang=str(ang), scaled="1")

    ln = sp_pr.find(f"{{{A_NS}}}ln")
    eff = sp_pr.find(f"{{{A_NS}}}effectLst")
    anchor = ln if ln is not None else eff
    if anchor is not None:
        anchor.addprevious(grad_fill)
    else:
        sp_pr.append(grad_fill)
    return True


def apply_shadow(shape, sh: dict | None) -> None:
    shape.shadow.inherit = False
    if not sh:
        return
    parsed = parse_color(sh["color"])
    if not parsed:
        return
    rgb, alpha = parsed
    dx, dy = sh.get("dx", 0.0), sh.get("dy", 0.0)
    dist_px = math.hypot(dx, dy)
    if dist_px < 0.5:
        return
    ang_deg = math.degrees(math.atan2(dy, dx)) % 360.0
    blur_emu = max(0, round(sh.get("blur", 0.0) * PX_TO_EMU))
    dist_emu = round(dist_px * PX_TO_EMU)
    dir_val = int(round(ang_deg * 60000))

    sp_pr = shape._element.spPr
    old = sp_pr.find(f"{{{A_NS}}}effectLst")
    if old is not None:
        sp_pr.remove(old)
    eff_lst = etree.SubElement(sp_pr, f"{{{A_NS}}}effectLst")
    outer = etree.SubElement(
        eff_lst,
        f"{{{A_NS}}}outerShdw",
        blurRad=str(blur_emu),
        dist=str(dist_emu),
        dir=str(dir_val),
        algn="tl",
        rotWithShape="0",
    )
    srgb = etree.SubElement(outer, f"{{{A_NS}}}srgbClr", val=f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}")
    if alpha < 0.999:
        etree.SubElement(srgb, f"{{{A_NS}}}alpha", val=str(int(round(alpha * 100000))))


def set_round_radius(shape, radius_px: float, w_px: float, h_px: float, bottom_only: bool = False) -> None:
    min_side = max(1.0, min(w_px, h_px))
    if radius_px <= 0.5:
        return
    if bottom_only:
        adj = min(0.5, radius_px / min_side)
        if len(shape.adjustments) >= 2:
            shape.adjustments[0] = 0.0
            shape.adjustments[1] = adj
    else:
        adj = min(0.5, radius_px / min_side)
        if len(shape.adjustments) >= 1:
            shape.adjustments[0] = adj


def choose_rect_type(radius_px: float, w_px: float, h_px: float, bottom_only: bool = False) -> MSO_SHAPE:
    if radius_px <= 0.5:
        return MSO_SHAPE.RECTANGLE
    if bottom_only:
        return MSO_SHAPE.ROUND_2_SAME_RECTANGLE
    if abs(w_px - h_px) <= 2.0 and radius_px >= min(w_px, h_px) / 2.0 - 1.5:
        return MSO_SHAPE.OVAL
    return MSO_SHAPE.ROUNDED_RECTANGLE


def build_image_blob(
    img_path: Path,
    box_w: int,
    box_h: int,
    object_fit: str,
    radius_px: float,
    cache: dict,
) -> bytes:
    w = max(1, round(box_w))
    h = max(1, round(box_h))
    rad = round(max(0.0, radius_px))
    key = (str(img_path), w, h, object_fit, rad)
    if key in cache:
        return cache[key]

    with Image.open(img_path) as im:
        im = im.convert("RGBA")
        iw, ih = im.size
        target_ratio = w / h
        src_ratio = iw / ih

        # Oversample slightly for crisp zoom in PowerPoint (up to 2x native up to src resolution)
        scale = min(2.0, max(1.0, min(iw / w, ih / h))) if iw > w and ih > h else 1.0
        cw = max(1, round(w * scale))
        ch = max(1, round(h * scale))
        crad = round(rad * scale)

        if object_fit == "cover":
            if src_ratio > target_ratio:
                crop_w = round(ih * target_ratio)
                left = (iw - crop_w) // 2
                cropped = im.crop((left, 0, left + crop_w, ih))
            else:
                crop_h = round(iw / target_ratio)
                top = (ih - crop_h) // 2
                cropped = im.crop((0, top, iw, top + crop_h))
            out = cropped.resize((cw, ch), Image.Resampling.LANCZOS)
        elif object_fit == "contain":
            s = min(cw / iw, ch / ih)
            nw = max(1, round(iw * s))
            nh = max(1, round(ih * s))
            resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
            out = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            out.paste(resized, ((cw - nw) // 2, (ch - nh) // 2), resized)
        else:
            out = im.resize((cw, ch), Image.Resampling.LANCZOS)

        if crad > 1:
            mask = Image.new("L", (cw, ch), 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=min(crad, cw // 2, ch // 2), fill=255)
            # Combine with existing alpha
            r_c, g_c, b_c, a_c = out.split()
            from PIL import ImageChops
            new_a = ImageChops.multiply(a_c, mask)
            out = Image.merge("RGBA", (r_c, g_c, b_c, new_a))

        has_transparency = (object_fit == "contain") or (crad > 1) or (out.getextrema()[3][0] < 255)
        buf = io.BytesIO()
        if has_transparency:
            out.save(buf, format="PNG", optimize=True)
        else:
            out.convert("RGB").save(buf, format="JPEG", quality=92, optimize=True, subsampling=0)
        blob = buf.getvalue()
        cache[key] = blob
        return blob


def write_paragraphs(tf, paras: list[list[dict]], align_str: str = "left", lh_ratio: float | None = None, font_scale: float = FONT_SCALE) -> None:
    align_map = {
        "center": PP_ALIGN.CENTER,
        "right": PP_ALIGN.RIGHT,
        "justify": PP_ALIGN.JUSTIFY,
        "left": PP_ALIGN.LEFT,
        "start": PP_ALIGN.LEFT,
    }
    pp_align = align_map.get(align_str, PP_ALIGN.LEFT)

    for p_idx, p_runs in enumerate(paras):
        p = tf.paragraphs[0] if p_idx == 0 else tf.add_paragraph()
        p.alignment = pp_align
        p.space_before = Pt(0)
        p.space_after = Pt(0)
        if lh_ratio is not None and lh_ratio > 0:
            p.line_spacing = min(1.8, max(0.9, lh_ratio))
        for r_meta in p_runs:
            run = p.add_run()
            run.text = r_meta["text"]
            font = run.font
            font.name = map_font(r_meta["font"])
            size_pt = max(6.0, r_meta["sizePx"] * PX_TO_PT * font_scale)
            font.size = Pt(size_pt)
            font.bold = bool(r_meta["bold"])
            font.italic = bool(r_meta["italic"])
            if r_meta.get("underline"):
                font.underline = True
            col = parse_color(r_meta["color"])
            if col:
                rgb, alpha = col
                font.color.rgb = rgb
                if alpha < 0.99:
                    r_pr = run._r.get_or_add_rPr()
                    sf = r_pr.find(f"{{{A_NS}}}solidFill")
                    if sf is not None and len(sf):
                        clr = sf[0]
                        for old in clr.findall(f"{{{A_NS}}}alpha"):
                            clr.remove(old)
                        etree.SubElement(clr, f"{{{A_NS}}}alpha", val=str(int(round(alpha * 100000))))
            r_pr = run._r.get_or_add_rPr()
            if r_meta.get("baseline"):
                r_pr.set("baseline", str(int(r_meta["baseline"])))
            if r_meta.get("spcPx") and abs(r_meta["spcPx"]) > 0.2:
                spc_hundredths = int(round(r_meta["spcPx"] * PX_TO_PT * 100))
                r_pr.set("spc", str(spc_hundredths))
            if r_meta.get("href"):
                run.hyperlink.address = r_meta["href"]


def build_transition_xml() -> etree._Element:
    trans = etree.Element(f"{{{P_NS}}}transition", spd="med")
    etree.SubElement(trans, f"{{{P_NS}}}fade", thruBlk="0")
    return trans


def build_timing_xml(animated_groups: list[dict], ambient_groups: list[dict] | None = None) -> etree._Element | None:
    """Build valid OOXML <p:timing> auto-playing all grouped entrance animations and continuous ambient loops."""
    valid = [g for g in animated_groups if g["spids"]]
    amb_valid = [a for a in (ambient_groups or []) if a["spids"]]
    if not valid and not amb_valid:
        return None

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

    for g in valid:
        anim = g["anim"]
        dur = str(g["dur"])
        delay = str(g["delay"])
        for spid_int in g["spids"]:
            spid = str(spid_int)

            eff_par = etree.SubElement(inner_children, f"{{{P_NS}}}par")
            eff_ctn = etree.SubElement(eff_par, f"{{{P_NS}}}cTn", id=get_id(), fill="hold")
            eff_st = etree.SubElement(eff_ctn, f"{{{P_NS}}}stCondLst")
            etree.SubElement(eff_st, f"{{{P_NS}}}cond", delay=delay)
            eff_children = etree.SubElement(eff_ctn, f"{{{P_NS}}}childTnLst")

            preset_id = "22" if anim == "hlsweep" else "10"
            anim_par = etree.SubElement(eff_children, f"{{{P_NS}}}par")
            anim_ctn = etree.SubElement(
                anim_par,
                f"{{{P_NS}}}cTn",
                id=get_id(),
                presetID=preset_id,
                presetClass="entr",
                presetSubtype="0",
                fill="hold",
                nodeType="withEffect",
            )
            anim_st = etree.SubElement(anim_ctn, f"{{{P_NS}}}stCondLst")
            etree.SubElement(anim_st, f"{{{P_NS}}}cond", delay="0")
            anim_children = etree.SubElement(anim_ctn, f"{{{P_NS}}}childTnLst")

            # Make visible at t=0
            set_el = etree.SubElement(anim_children, f"{{{P_NS}}}set")
            cbhvr = etree.SubElement(set_el, f"{{{P_NS}}}cBhvr")
            s_ctn = etree.SubElement(cbhvr, f"{{{P_NS}}}cTn", id=get_id(), dur="1", fill="hold")
            s_st = etree.SubElement(s_ctn, f"{{{P_NS}}}stCondLst")
            etree.SubElement(s_st, f"{{{P_NS}}}cond", delay="0")
            tgt = etree.SubElement(cbhvr, f"{{{P_NS}}}tgtEl")
            etree.SubElement(tgt, f"{{{P_NS}}}spTgt", spid=spid)
            attrs = etree.SubElement(cbhvr, f"{{{P_NS}}}attrNameLst")
            etree.SubElement(attrs, f"{{{P_NS}}}attrName").text = "style.visibility"
            to_el = etree.SubElement(set_el, f"{{{P_NS}}}to")
            etree.SubElement(to_el, f"{{{P_NS}}}strVal", val="visible")

            # Wipe right for .hl highlight sweep, smooth fade for others
            eff_filter = "wipe(right)" if anim == "hlsweep" else "fade"
            ae = etree.SubElement(anim_children, f"{{{P_NS}}}animEffect", transition="in", filter=eff_filter)
            ae_bhvr = etree.SubElement(ae, f"{{{P_NS}}}cBhvr")
            etree.SubElement(ae_bhvr, f"{{{P_NS}}}cTn", id=get_id(), dur=dur)
            ae_tgt = etree.SubElement(ae_bhvr, f"{{{P_NS}}}tgtEl")
            etree.SubElement(ae_tgt, f"{{{P_NS}}}spTgt", spid=spid)

            # Motion path mirroring styles/animations.css
            if anim in ("tin", "rowin", "pop", "numdrop", "capup"):
                if anim == "tin":
                    from_x, from_y = "-0.045", "0"
                elif anim == "rowin":
                    from_x, from_y = "-0.024", "0"
                elif anim == "numdrop":
                    from_x, from_y = "0", "-0.040"
                elif anim == "capup":
                    from_x, from_y = "0", "0.045"
                else:
                    from_x, from_y = "0", "0.032"
                mot = etree.SubElement(
                    anim_children,
                    f"{{{P_NS}}}animMotion",
                    origin="layout",
                    path=f"M {from_x} {from_y} L 0 0 E",
                    pathEditMode="relative",
                    ptsTypes="AA",
                )
                m_bhvr = etree.SubElement(mot, f"{{{P_NS}}}cBhvr", rctx="PPT")
                etree.SubElement(m_bhvr, f"{{{P_NS}}}cTn", id=get_id(), dur=dur, fill="hold")
                m_tgt = etree.SubElement(m_bhvr, f"{{{P_NS}}}tgtEl")
                etree.SubElement(m_tgt, f"{{{P_NS}}}spTgt", spid=spid)
                m_attrs = etree.SubElement(m_bhvr, f"{{{P_NS}}}attrNameLst")
                etree.SubElement(m_attrs, f"{{{P_NS}}}attrName").text = "ppt_x"
                etree.SubElement(m_attrs, f"{{{P_NS}}}attrName").text = "ppt_y"

    # Continuous ambient idle loops matching .hl (bob), .floaty, .doodle (drift), .imgbig img.ph (kenburns)
    for amb in amb_valid:
        kind = amb["kind"]
        dur = str(amb["dur"])
        delay = str(amb["delay"])
        for spid_int in amb["spids"]:
            spid = str(spid_int)
            eff_par = etree.SubElement(inner_children, f"{{{P_NS}}}par")
            eff_ctn = etree.SubElement(eff_par, f"{{{P_NS}}}cTn", id=get_id(), fill="hold")
            eff_st = etree.SubElement(eff_ctn, f"{{{P_NS}}}stCondLst")
            etree.SubElement(eff_st, f"{{{P_NS}}}cond", delay=delay)
            eff_children = etree.SubElement(eff_ctn, f"{{{P_NS}}}childTnLst")

            anim_par = etree.SubElement(eff_children, f"{{{P_NS}}}par")
            anim_ctn = etree.SubElement(
                anim_par,
                f"{{{P_NS}}}cTn",
                id=get_id(),
                presetID="6" if kind == "kenburns" else "1",
                presetClass="emph",
                presetSubtype="0",
                fill="hold",
                nodeType="withEffect",
            )
            anim_st = etree.SubElement(anim_ctn, f"{{{P_NS}}}stCondLst")
            etree.SubElement(anim_st, f"{{{P_NS}}}cond", delay="0")
            anim_children = etree.SubElement(anim_ctn, f"{{{P_NS}}}childTnLst")

            if kind in ("bob", "floaty", "drift"):
                dy = "-0.007" if kind == "bob" else ("-0.018" if kind == "floaty" else "-0.008")
                mot = etree.SubElement(
                    anim_children,
                    f"{{{P_NS}}}animMotion",
                    origin="layout",
                    path=f"M 0 0 L 0 {dy} E",
                    pathEditMode="relative",
                    ptsTypes="AA",
                )
                m_bhvr = etree.SubElement(mot, f"{{{P_NS}}}cBhvr", rctx="PPT")
                etree.SubElement(
                    m_bhvr,
                    f"{{{P_NS}}}cTn",
                    id=get_id(),
                    dur=dur,
                    repeatCount="indefinite",
                    autoRev="1",
                    fill="hold",
                )
                m_tgt = etree.SubElement(m_bhvr, f"{{{P_NS}}}tgtEl")
                etree.SubElement(m_tgt, f"{{{P_NS}}}spTgt", spid=spid)
                m_attrs = etree.SubElement(m_bhvr, f"{{{P_NS}}}attrNameLst")
                etree.SubElement(m_attrs, f"{{{P_NS}}}attrName").text = "ppt_x"
                etree.SubElement(m_attrs, f"{{{P_NS}}}attrName").text = "ppt_y"

                if kind == "bob":
                    rot = etree.SubElement(anim_children, f"{{{P_NS}}}animRot", by="42000")
                    r_bhvr = etree.SubElement(rot, f"{{{P_NS}}}cBhvr")
                    etree.SubElement(
                        r_bhvr,
                        f"{{{P_NS}}}cTn",
                        id=get_id(),
                        dur=dur,
                        repeatCount="indefinite",
                        autoRev="1",
                        fill="hold",
                    )
                    r_tgt = etree.SubElement(r_bhvr, f"{{{P_NS}}}tgtEl")
                    etree.SubElement(r_tgt, f"{{{P_NS}}}spTgt", spid=spid)
            elif kind == "kenburns":
                sc = etree.SubElement(anim_children, f"{{{P_NS}}}animScale", zoomContents="1")
                s_bhvr = etree.SubElement(sc, f"{{{P_NS}}}cBhvr")
                etree.SubElement(
                    s_bhvr,
                    f"{{{P_NS}}}cTn",
                    id=get_id(),
                    dur=dur,
                    repeatCount="indefinite",
                    autoRev="1",
                    fill="hold",
                )
                s_tgt = etree.SubElement(s_bhvr, f"{{{P_NS}}}tgtEl")
                etree.SubElement(s_tgt, f"{{{P_NS}}}spTgt", spid=spid)
                etree.SubElement(sc, f"{{{P_NS}}}from", x="100000", y="100000")
                etree.SubElement(sc, f"{{{P_NS}}}to", x="104000", y="104000")

    return timing


def insert_slide_fx(slide, add_transition: bool, animated_groups: list[dict], ambient_groups: list[dict] | None = None) -> None:
    root = slide._element
    ext_lst = root.find(f"{{{P_NS}}}extLst")

    def insert_before_ext(node: etree._Element) -> None:
        if ext_lst is not None:
            ext_lst.addprevious(node)
        else:
            root.append(node)

    if add_transition:
        insert_before_ext(build_transition_xml())
    timing = build_timing_xml(animated_groups, ambient_groups)
    if timing is not None:
        insert_before_ext(timing)


FONT_SPECS = [
    (
        "Archivo",
        "34",
        {
            "regular": "https://fonts.googleapis.com/css2?family=Archivo:wght@400",
            "bold": "https://fonts.googleapis.com/css2?family=Archivo:wght@700",
            "italic": "https://fonts.googleapis.com/css2?family=Archivo:ital,wght@1,400",
            "boldItalic": "https://fonts.googleapis.com/css2?family=Archivo:ital,wght@1,700",
        },
    ),
    (
        "Be Vietnam Pro",
        "34",
        {
            "regular": "https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400",
            "bold": "https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@700",
            "italic": "https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@1,400",
            "boldItalic": "https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@1,700",
        },
    ),
    (
        "IBM Plex Mono",
        "49",
        {
            "regular": "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400",
            "bold": "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@700",
            "italic": "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@1,400",
            "boldItalic": "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@1,700",
        },
    ),
]

FONT_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font"


def load_or_fetch_eot(fonts_dir: Path, slug: str, variant: str, url: str) -> bytes:
    fonts_dir.mkdir(parents=True, exist_ok=True)
    cached = fonts_dir / f"{slug}-{variant}.fntdata"
    if cached.is_file():
        return cached.read_bytes()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"})
    css = urllib.request.urlopen(req, timeout=20).read().decode("utf-8")
    urls = re.findall(r"url\(([^)]+)\)", css)
    if not urls:
        raise RuntimeError(f"Could not find EOT URL in {url}")
    blob = urllib.request.urlopen(urllib.request.Request(urls[0], headers={"User-Agent": "Mozilla/4.0"}), timeout=20).read()
    cached.write_bytes(blob)
    return blob


def embed_fonts(prs: Presentation, root_dir: Path) -> int:
    """Embed Archivo, Be Vietnam Pro, and IBM Plex Mono (.fntdata EOT) into the PPTX package."""
    fonts_dir = root_dir / "assets" / "fonts"
    pres_el = prs._element
    pres_el.set("embedTrueTypeFonts", "1")
    pres_el.set("saveSubsetFonts", "0")

    old_lst = pres_el.find(f"{{{P_NS}}}embeddedFontLst")
    if old_lst is not None:
        pres_el.remove(old_lst)

    font_lst = etree.Element(f"{{{P_NS}}}embeddedFontLst")
    font_idx = 1

    for typeface, pitch_family, variants in FONT_SPECS:
        slug = typeface.lower().replace(" ", "-")
        emb_font = etree.SubElement(font_lst, f"{{{P_NS}}}embeddedFont")
        reg_blob = load_or_fetch_eot(fonts_dir, slug, "regular", variants["regular"])
        panose = reg_blob[16:26].hex() if len(reg_blob) >= 26 else "00000000000000000000"
        etree.SubElement(
            emb_font,
            f"{{{P_NS}}}font",
            typeface=typeface,
            panose=panose,
            pitchFamily=pitch_family,
            charset="0",
        )
        for var, url in variants.items():
            blob = reg_blob if var == "regular" else load_or_fetch_eot(fonts_dir, slug, var, url)
            part = Part(
                PackURI(f"/ppt/fonts/font{font_idx}.fntdata"),
                "application/x-fontdata",
                prs.part.package,
                blob=blob,
            )
            r_id = prs.part.relate_to(part, FONT_REL_TYPE)
            var_el = etree.SubElement(emb_font, f"{{{P_NS}}}{var}")
            var_el.set(f"{{{R_NS}}}id", r_id)
            font_idx += 1

    # ECMA-376 CT_Presentation sequence: <p:embeddedFontLst> precedes <p:defaultTextStyle>
    default_ts = pres_el.find(f"{{{P_NS}}}defaultTextStyle")
    modify_ver = pres_el.find(f"{{{P_NS}}}modifyVerifier")
    ext_lst = pres_el.find(f"{{{P_NS}}}extLst")
    anchor = next((x for x in (default_ts, modify_ver, ext_lst) if x is not None), None)
    if anchor is not None:
        anchor.addprevious(font_lst)
    else:
        pres_el.append(font_lst)
    return font_idx - 1


def export_deck(root_dir: Path, out_path: Path) -> None:
    chrome_exe = find_chrome()
    index_url = (root_dir / "index.html").as_uri()

    prs = Presentation()
    prs.slide_width = SLIDE_W_EMU
    prs.slide_height = SLIDE_H_EMU
    blank_layout = prs.slide_layouts[6]
    img_cache: dict = {}

    total_shapes = 0
    total_pics = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chrome_exe)
        page = browser.new_page(viewport={"width": SLIDE_W_PX, "height": SLIDE_H_PX}, device_scale_factor=1)
        page.goto(index_url, wait_until="networkidle")
        page.evaluate("() => document.fonts.ready")
        page.wait_for_timeout(500)
        page.add_style_tag(content=EXPORT_CSS)
        page.wait_for_timeout(150)

        total = page.evaluate("() => document.querySelectorAll('.slide').length")
        print(f"Exporting {total} native slides from {index_url} ...", flush=True)

        for idx in range(total):
            meta = page.evaluate(EXTRACT_SLIDE_JS, idx)
            slide = prs.slides.add_slide(blank_layout)

            # 1. Native slide background color
            bg_col = parse_color(meta["bgColor"]) or (RGBColor(255, 248, 236), 1.0)
            slide.background.fill.solid()
            slide.background.fill.fore_color.rgb = bg_col[0]

            # Track shape IDs per entrance animation group & continuous ambient groups
            groups_map: dict[int, dict] = {
                g["id"]: {
                    "id": g["id"],
                    "anim": g["anim"],
                    "dur": g["dur"],
                    "delay": g["delay"],
                    "ambient": g.get("ambient"),
                    "spids": [],
                }
                for g in meta["animGroups"]
            }
            kenburns_spids: list[int] = []
            doodle_groups: dict[int, dict] = {}

            def register_shape(shape, ag_id: int) -> None:
                nonlocal total_shapes
                total_shapes += 1
                if ag_id in groups_map:
                    groups_map[ag_id]["spids"].append(shape.shape_id)

            # 2. Subtle decorative bottom-right corner ring matching .slide-inner::after
            if not meta["isFullBleed"]:
                ring = slide.shapes.add_shape(MSO_SHAPE.OVAL, emu(1386), emu(686), emu(336), emu(336))
                ring.fill.background()
                ring.line.color.rgb = RGBColor(255, 90, 90)
                ring.line.width = Pt(24)
                ln = ring.line._get_or_add_ln()
                sf = ln.find(f"{{{A_NS}}}solidFill")
                if sf is not None and len(sf):
                    etree.SubElement(sf[0], f"{{{A_NS}}}alpha", val="12000")
                ring.shadow.inherit = False
                total_shapes += 1

            # 3. Full-bleed background photos & overlays (Slides 36, 46)
            for im in meta["images"]:
                if not im["fullBleedImg"]:
                    continue
                img_file = root_dir / unquote(im["src"])
                if not img_file.is_file():
                    continue
                blob = build_image_blob(img_file, im["w"], im["h"], im["objectFit"], 0, img_cache)
                pic = slide.shapes.add_picture(io.BytesIO(blob), emu(im["x"]), emu(im["y"]), emu(im["w"]), emu(im["h"]))
                total_pics += 1
                total_shapes += 1

            for b in meta["boxes"]:
                if not b["isOverlay"]:
                    continue
                ov = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, emu(b["x"]), emu(b["y"]), emu(b["w"]), emu(b["h"]))
                ov.line.fill.background()
                ov.shadow.inherit = False
                if not b["bgGrad"] or not set_linear_gradient(ov, b["bgGrad"]):
                    set_solid_fill_alpha(ov.fill, RGBColor(22, 19, 15), 0.72)
                total_shapes += 1

            # 3b. Vector chemistry doodles drifting gently in background
            for d_item in meta.get("doodleItems", []):
                pts = d_item["pts"]
                if len(pts) < 2:
                    continue
                fb = slide.shapes.build_freeform(emu(pts[0][0]), emu(pts[0][1]))
                fb.add_line_segments([(emu(px), emu(py)) for px, py in pts[1:]], close=d_item["closed"])
                dshp = fb.convert_to_shape()
                dshp.fill.background()
                dcol = parse_color(d_item["color"]) or (RGBColor(22, 19, 15), 1.0)
                dshp.line.color.rgb = dcol[0]
                dshp.line.width = Pt(max(0.9, d_item["strokeW"] * PX_TO_PT))
                ln = dshp.line._get_or_add_ln()
                ln.set("cap", "rnd")
                sf = ln.find(f"{{{A_NS}}}solidFill")
                if sf is not None and len(sf):
                    op_val = int(round(max(0.05, min(1.0, d_item["opacity"])) * 100000))
                    etree.SubElement(sf[0], f"{{{A_NS}}}alpha", val=str(op_val))
                dshp.shadow.inherit = False
                total_shapes += 1
                did = d_item["dIdx"]
                grp = doodle_groups.setdefault(did, {"kind": "drift", "dur": max(2200, d_item["durMs"] // 2), "delay": (did * 250) % 900, "spids": []})
                grp["spids"].append(dshp.shape_id)

            # 4. Card boxes & backgrounds (excluding full-bleed overlays & photo captions which go on top of photos)
            for b in meta["boxes"]:
                if b["isOverlay"] or b["isCap"]:
                    continue
                stype = choose_rect_type(b["radius"], b["w"], b["h"], b["bottomRoundOnly"])
                shp = slide.shapes.add_shape(stype, emu(b["x"]), emu(b["y"]), emu(b["w"]), emu(b["h"]))
                set_round_radius(shp, b["radius"], b["w"], b["h"], b["bottomRoundOnly"])
                if b["bg"]:
                    col = parse_color(b["bg"])
                    if col:
                        set_solid_fill_alpha(shp.fill, col[0], col[1])
                    else:
                        shp.fill.background()
                elif b["bgGrad"] and set_linear_gradient(shp, b["bgGrad"]):
                    pass
                else:
                    shp.fill.background()

                if b["borderColor"] and b["borderWidth"] > 0:
                    bcol = parse_color(b["borderColor"])
                    if bcol:
                        shp.line.color.rgb = bcol[0]
                        shp.line.width = Pt(max(0.75, b["borderWidth"] * PX_TO_PT))
                else:
                    shp.line.fill.background()
                apply_shadow(shp, b["shadow"])
                register_shape(shp, b["agId"])

            # 5. Thin partial-border dividers
            for d in meta["dividers"]:
                col = parse_color(d["color"])
                if not col:
                    continue
                dv = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, emu(d["x"]), emu(d["y"]), max(Emu(6350), emu(d["w"])), max(Emu(6350), emu(d["h"])))
                set_solid_fill_alpha(dv.fill, col[0], col[1])
                dv.line.fill.background()
                dv.shadow.inherit = False
                register_shape(dv, d["agId"])

            # 6. Regular <img> photos / chemical structure diagrams
            for im in meta["images"]:
                if im["fullBleedImg"]:
                    continue
                img_file = root_dir / unquote(im["src"])
                if not img_file.is_file():
                    continue
                blob = build_image_blob(img_file, im["w"], im["h"], im["objectFit"], im["radius"], img_cache)
                pic = slide.shapes.add_picture(io.BytesIO(blob), emu(im["x"]), emu(im["y"]), emu(im["w"]), emu(im["h"]))
                total_pics += 1
                register_shape(pic, im["agId"])
                if im.get("kenburns"):
                    kenburns_spids.append(pic.shape_id)

            # 7. Caption bars (.imgbig .cap) stacked directly above photos
            for b in meta["boxes"]:
                if not b["isCap"]:
                    continue
                stype = choose_rect_type(b["radius"], b["w"], b["h"], b["bottomRoundOnly"])
                shp = slide.shapes.add_shape(stype, emu(b["x"]), emu(b["y"]), emu(b["w"]), emu(b["h"]))
                set_round_radius(shp, b["radius"], b["w"], b["h"], b["bottomRoundOnly"])
                col = parse_color(b["bg"]) if b["bg"] else (RGBColor(22, 19, 15), 1.0)
                if col:
                    set_solid_fill_alpha(shp.fill, col[0], col[1])
                shp.line.fill.background()
                shp.shadow.inherit = False
                register_shape(shp, b["agId"])

            # 8. SVG vector shapes & arrows (Slides 9, 30, 50, 53)
            for item in meta["svgItems"]:
                kind = item["kind"]
                if kind == "rect":
                    stype = MSO_SHAPE.ROUNDED_RECTANGLE if item["rx"] > 0.5 else MSO_SHAPE.RECTANGLE
                    shp = slide.shapes.add_shape(stype, emu(item["x"]), emu(item["y"]), emu(item["w"]), emu(item["h"]))
                    if item["rx"] > 0.5:
                        set_round_radius(shp, item["rx"], item["w"], item["h"])
                    fcol = parse_color(item["fill"])
                    if fcol:
                        set_solid_fill_alpha(shp.fill, fcol[0], fcol[1])
                    else:
                        shp.fill.background()
                    scol = parse_color(item["stroke"])
                    if scol and item["strokeWidth"] > 0:
                        shp.line.color.rgb = scol[0]
                        shp.line.width = Pt(max(0.75, item["strokeWidth"] * PX_TO_PT))
                    else:
                        shp.line.fill.background()
                    shp.shadow.inherit = False
                    register_shape(shp, item["agId"])
                elif kind == "circle":
                    shp = slide.shapes.add_shape(MSO_SHAPE.OVAL, emu(item["x"]), emu(item["y"]), emu(item["w"]), emu(item["h"]))
                    fcol = parse_color(item["fill"])
                    if fcol:
                        set_solid_fill_alpha(shp.fill, fcol[0], fcol[1])
                    else:
                        shp.fill.background()
                    scol = parse_color(item["stroke"])
                    if scol and item["strokeWidth"] > 0:
                        shp.line.color.rgb = scol[0]
                        shp.line.width = Pt(max(0.75, item["strokeWidth"] * PX_TO_PT))
                    else:
                        shp.line.fill.background()
                    shp.shadow.inherit = False
                    register_shape(shp, item["agId"])
                elif kind == "line":
                    conn = slide.shapes.add_connector(
                        MSO_CONNECTOR.STRAIGHT,
                        emu(item["x1"]), emu(item["y1"]),
                        emu(item["x2"]), emu(item["y2"]),
                    )
                    scol = parse_color(item["stroke"]) or (RGBColor(22, 19, 15), 1.0)
                    conn.line.color.rgb = scol[0]
                    conn.line.width = Pt(max(1.0, item["strokeWidth"] * PX_TO_PT))
                    conn.shadow.inherit = False
                    ln = conn.line._get_or_add_ln()
                    if item["markerStart"]:
                        etree.SubElement(ln, f"{{{A_NS}}}headEnd", type="triangle", w="med", len="med")
                    if item["markerEnd"]:
                        etree.SubElement(ln, f"{{{A_NS}}}tailEnd", type="triangle", w="med", len="med")
                    register_shape(conn, item["agId"])
                elif kind == "text":
                    tb = slide.shapes.add_textbox(emu(item["x"]), emu(item["y"]), emu(item["w"]), emu(item["h"]))
                    tf = tb.text_frame
                    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Emu(0)
                    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
                    tf.word_wrap = False
                    write_paragraphs(tf, [item["runs"]], item["align"], lh_ratio=1.1, font_scale=0.95)
                    register_shape(tb, item["agId"])

            # 9. Native badges (.hl, .s-num, .chip, .scope-pill): unified rounded shape + centered text
            for bg in meta["badges"]:
                stype = choose_rect_type(bg["radius"], bg["w"], bg["h"])
                shp = slide.shapes.add_shape(stype, emu(bg["x"]), emu(bg["y"]), emu(bg["w"]), emu(bg["h"]))
                set_round_radius(shp, bg["radius"], bg["w"], bg["h"])
                col = parse_color(bg["bg"]) if bg["bg"] else None
                if col:
                    set_solid_fill_alpha(shp.fill, col[0], col[1])
                else:
                    shp.fill.background()
                if bg["borderColor"] and bg["borderWidth"] > 0:
                    bcol = parse_color(bg["borderColor"])
                    if bcol:
                        shp.line.color.rgb = bcol[0]
                        shp.line.width = Pt(max(0.75, bg["borderWidth"] * PX_TO_PT))
                else:
                    shp.line.fill.background()
                apply_shadow(shp, bg["shadow"])
                tf = shp.text_frame
                tf.margin_left = emu(max(0.0, bg["padL"] - 2))
                tf.margin_right = emu(max(0.0, bg["padR"] - 2))
                tf.margin_top = emu(max(0.0, bg["padT"] - 2))
                tf.margin_bottom = emu(max(0.0, bg["padB"] - 2))
                tf.vertical_anchor = MSO_ANCHOR.MIDDLE
                tf.word_wrap = False
                write_paragraphs(tf, bg["paras"], "center", lh_ratio=1.05, font_scale=FONT_SCALE)
                register_shape(shp, bg["agId"])

            # 10. All native editable text boxes
            for tb_meta in meta["textBlocks"]:
                extra_w = 10.0 if tb_meta["singleLine"] else 8.0
                extra_h = 4.0
                tb = slide.shapes.add_textbox(
                    emu(tb_meta["x"]),
                    emu(max(0.0, tb_meta["y"] - 1.5)),
                    emu(tb_meta["w"] + extra_w),
                    emu(tb_meta["h"] + extra_h),
                )
                tf = tb.text_frame
                tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Emu(0)
                tf.word_wrap = not tb_meta["singleLine"]
                tf.vertical_anchor = MSO_ANCHOR.TOP
                write_paragraphs(tf, tb_meta["paras"], tb_meta["align"], lh_ratio=tb_meta["lhRatio"], font_scale=FONT_SCALE)
                register_shape(tb, tb_meta["agId"])

            # 11. Speaker notes
            if meta["notes"]:
                slide.notes_slide.notes_text_frame.text = meta["notes"]

            # 12. Native slide fade transition (slides 2..N) + grouped entrance & continuous ambient loops
            ordered_groups = sorted(groups_map.values(), key=lambda g: (g["delay"], g["id"]))
            ambient_groups = []
            for g in ordered_groups:
                if g.get("ambient") == "bob" and g["spids"]:
                    ambient_groups.append({"kind": "bob", "dur": 1600, "delay": g["delay"] + g["dur"] + 80, "spids": g["spids"]})
                elif g.get("ambient") == "floaty" and g["spids"]:
                    ambient_groups.append({"kind": "floaty", "dur": 2750, "delay": 200, "spids": g["spids"]})
            if kenburns_spids:
                ambient_groups.append({"kind": "kenburns", "dur": 6500, "delay": 500, "spids": kenburns_spids})
            ambient_groups.extend(doodle_groups.values())

            insert_slide_fx(slide, add_transition=(idx > 0), animated_groups=ordered_groups, ambient_groups=ambient_groups)

            if (idx + 1) % 10 == 0 or idx + 1 == total:
                print(f"  Built slide {idx + 1}/{total} ({len(meta['textBlocks'])} textboxes, {len(meta['badges'])} badges)", flush=True)

        browser.close()

    embedded_count = embed_fonts(prs, root_dir)
    prs.save(str(out_path))
    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"Saved {out_path} ({size_mb:.2f} MB) | shapes={total_shapes}, images={total_pics}, embedded_fonts={embedded_count}", flush=True)


def main() -> int:
    root_dir = Path(__file__).resolve().parent.parent
    out_name = "Dinh dưỡng - đề phòng độc tố · Slide thuyết trình.pptx"
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else (root_dir / out_name)
    export_deck(root_dir, out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
