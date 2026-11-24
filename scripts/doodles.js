// Doodle hóa học vẽ tay: rải ngẫu nhiên (seed cố định theo từng slide)
// vào vùng trống trên nền slide; đo khung nội dung thật để không đè chữ/ảnh.
(function (global) {
  'use strict';

  var DOODLES = [
    '<path d="M41 13h18M46 13v20L28 78a6 6 0 0 0 6 8h32a6 6 0 0 0 6-8L54 33V13"/><path d="M35 59q8-6 15 0t15 0"/><circle cx="46" cy="71" r="3"/><circle cx="57" cy="76" r="2.3"/><circle cx="52" cy="65" r="1.7"/>',
    '<path d="M38 12v52a12 12 0 0 0 24 0V12M33 12h34"/><path d="M38 45q6-5 12 0t12 0"/><circle cx="47" cy="61" r="2.6"/><circle cx="54" cy="70" r="2"/>',
    '<path d="M43 11h14M46 11v27M54 11v27"/><circle cx="50" cy="63" r="25"/><path d="M31 67q9-6 19 0t19 0"/><circle cx="44" cy="76" r="2.6"/><circle cx="57" cy="73" r="2"/>',
    '<path d="M50 50L30 33M50 50l21-13M50 50l8 23"/><circle cx="50" cy="50" r="9"/><circle cx="28" cy="31" r="7"/><circle cx="73" cy="35" r="6"/><circle cx="59" cy="76" r="6.5"/>',
    '<circle cx="50" cy="50" r="5"/><ellipse cx="50" cy="50" rx="35" ry="13"/><ellipse cx="50" cy="50" rx="35" ry="13" transform="rotate(60 50 50)"/><ellipse cx="50" cy="50" rx="35" ry="13" transform="rotate(120 50 50)"/>',
    '<path d="M31 15h38M36 15l-3 59a6 6 0 0 0 6 6h22a6 6 0 0 0 6-6l-3-59"/><path d="M35 47q8-6 16 0t15 0"/><path d="M59 27h6M59 37h6"/>',
    '<path d="M50 11S27 43 27 61a23 23 0 0 0 46 0C73 43 50 11 50 11Z"/><path d="M37 63a13 13 0 0 0 5 11"/>',
    '<circle cx="33" cy="63" r="13"/><circle cx="58" cy="42" r="9"/><circle cx="67" cy="69" r="6"/><circle cx="45" cy="28" r="5"/><circle cx="76" cy="27" r="3.4"/>',
    '<path d="M50 13c4 19 14 29 33 37-19 8-29 18-33 37-4-19-14-29-33-37 19-8 29-18 33-37Z"/><path d="M80 14v13M73.5 20.5h13"/>',
    '<path d="M25 18v43a7 7 0 0 0 14 0V18M21 18h22M57 18v43a7 7 0 0 0 14 0V18M53 18h22"/><path d="M13 84h74"/><path d="M25 36q4-3 7 0t7 0M57 36q4-3 7 0t7 0"/>'
  ];

  var DOODLE_COLORS = ['#16130F', '#16130F', '#16130F', '#E8402F', '#00A651', '#D99A00'];
  var BLOCK_SEL = '.pt,.lrow,.fstep,.col,.mcol,.imgbig,.imgwhite,.illus,.box,.stat,.statement,.foot,.tag,.scope-pill,.s-num,.chip,.figcap,.title,.sub,.mol,.floaty,.donut,.fd-step,.fd-back,.newsfr,.fd-net';
  var reduceMotion = !!(global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches);

  function mulberry32(a) {
    return function () {
      a |= 0;
      a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function rectOf(el, inner) {
    var x = 0, y = 0, n = el;
    while (n && n !== inner) {
      x += n.offsetLeft;
      y += n.offsetTop;
      n = n.offsetParent;
    }
    return { x: x, y: y, w: el.offsetWidth, h: el.offsetHeight };
  }

  function hit(a, b) {
    return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
  }

  function placeDoodles(slides) {
    slides.forEach(function (sl, idx) {
      var inner = sl.querySelector('.slide-inner');
      if (!inner) return;
      var obs = [], photo = false;
      var els = inner.querySelectorAll('*');
      for (var i = 0; i < els.length; i++) {
        var el = els[i], w = el.offsetWidth, h = el.offsetHeight;
        if (!w || !h) continue;
        if (w * h >= 0.88 * 1600 * 900) { photo = true; continue; }
        var keep = el.tagName === 'svg' || el.tagName === 'IMG';
        if (!keep) { try { keep = el.matches(BLOCK_SEL); } catch (e) {} }
        if (!keep && el.children.length === 0) keep = true;
        if (!keep) {
          for (var j = 0; j < el.childNodes.length; j++) {
            if (el.childNodes[j].nodeType === 3 && el.childNodes[j].textContent.trim()) {
              keep = true;
              break;
            }
          }
        }
        if (keep) obs.push(rectOf(el, inner));
      }
      obs.push({ x: 1416, y: 716, w: 184, h: 184 });

      var layer = document.createElement('div');
      layer.className = 'doodles';
      layer.setAttribute('aria-hidden', 'true');
      if (photo) layer.style.zIndex = '2';
      inner.insertBefore(layer, inner.firstChild);

      var rnd = mulberry32(20261123 + idx * 7919);
      var want = 2 + Math.floor(rnd() * 3), placed = [];
      for (var k = 0; k < want; k++) {
        var art = DOODLES[Math.floor(rnd() * DOODLES.length)];
        var base = 50 + rnd() * 56, done = false;
        for (var t = 0; t < 60 && !done; t++) {
          var s = base * (t > 40 ? .62 : (t > 24 ? .8 : 1));
          var x = 20 + rnd() * (1600 - s - 40), y = 20 + rnd() * (900 - s - 40);
          var cand = { x: x - 11, y: y - 11, w: s + 22, h: s + 22 }, clash = false;
          for (var o = 0; o < obs.length; o++) {
            if (hit(cand, obs[o])) { clash = true; break; }
          }
          if (!clash) {
            for (var p = 0; p < placed.length; p++) {
              if (hit(cand, placed[p])) { clash = true; break; }
            }
          }
          if (clash) continue;

          var d = document.createElement('div');
          d.className = 'doodle';
          d.style.left = x + 'px';
          d.style.top = y + 'px';
          d.style.width = s + 'px';
          d.style.height = s + 'px';
          d.style.opacity = (0.12 + rnd() * 0.08).toFixed(2);
          d.style.color = DOODLE_COLORS[Math.floor(rnd() * DOODLE_COLORS.length)];
          d.style.setProperty('--r', (rnd() * 36 - 18).toFixed(1) + 'deg');
          d.style.animationDuration = (6 + rnd() * 4).toFixed(1) + 's';
          d.innerHTML = '<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + art + '</svg>';
          layer.appendChild(d);
          placed.push(cand);
          done = true;
        }
      }
    });
  }

  // Doodle tự vẽ dần nét khi slide mở: đo độ dài từng nét SVG rồi chạy dashoffset về 0
  function drawDoodles(slide) {
    if (reduceMotion || !slide) return;
    var shapes = slide.querySelectorAll('.doodle svg path, .doodle svg circle, .doodle svg ellipse');
    Array.prototype.forEach.call(shapes, function (el, i) {
      var len;
      try { len = el.getTotalLength(); } catch (e) { return; }
      if (!len || !isFinite(len)) return;
      el.style.transition = 'none';
      el.style.strokeDasharray = String(Math.ceil(len));
      el.style.strokeDashoffset = String(Math.ceil(len));
      void el.getBoundingClientRect();
      el.style.transition = 'stroke-dashoffset 1.3s cubic-bezier(.4,0,.2,1) ' + Math.min(i * 45, 450) + 'ms';
      el.style.strokeDashoffset = '0';
    });
  }

  global.DeckDoodles = {
    place: placeDoodles,
    draw: drawDoodles
  };
})(window);
