(function () {
  'use strict';

  var stage = document.getElementById('stage');
  var prog = document.getElementById('progress');
  var toc = document.getElementById('toc');
  var tocGrid = document.getElementById('tocGrid');
  var tocTitle = document.getElementById('tocTitle');
  var edgeL = document.getElementById('edgeL');
  var edgeR = document.getElementById('edgeR');

  // Nạp các phần slide đã đăng ký từ thư mục slides/*.js vào #stage
  if (Array.isArray(window.DECK_SLIDES) && window.DECK_SLIDES.length) {
    stage.innerHTML = window.DECK_SLIDES.join('\n');
  }

  var slides = Array.prototype.slice.call(stage.querySelectorAll('.slide'));
  var total = slides.length;
  var cur = 0;

  if (tocTitle) {
    tocTitle.textContent = 'Mục lục · ' + total + ' slide';
  }

  // Khung slide luôn giữ đúng tỉ lệ 16:9 (1600x900), chỉ thu/phóng đồng đều
  // và căn giữa; phần nền đỏ bên ngoài tự dãn theo màn hình.
  function fit() {
    var s = Math.min(window.innerWidth / 1660, window.innerHeight / 950);
    stage.style.transform = 'scale(' + s + ')';
  }

  function countUp(slide) {
    if (!slide) return;
    slide.querySelectorAll('[data-count]').forEach(function (el) {
      if (el.dataset.done) return;
      el.dataset.done = '1';
      var target = parseFloat(el.dataset.count), t0 = null, dur = 1400;
      function tick(t) {
        if (!t0) t0 = t;
        var p = Math.min((t - t0) / dur, 1);
        el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
        if (p < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    });
  }

  function drawCurrentDoodles() {
    if (window.DeckDoodles && slides[cur]) {
      window.DeckDoodles.draw(slides[cur]);
    }
  }

  function render() {
    slides.forEach(function (sl, i) {
      sl.classList.toggle('active', i === cur);
      sl.classList.toggle('before', i < cur);
    });
    prog.style.width = total ? ((cur + 1) / total * 100) + '%' : '0%';
    countUp(slides[cur]);
    drawCurrentDoodles();
  }

  function go(i) {
    if (!total) return;
    var target = Math.max(0, Math.min(total - 1, i));
    if (target === cur) {
      render();
      return;
    }
    cur = target;
    // nút chuyển slide hai bên nảy nhẹ một nhịp khi đổi slide
    [edgeL, edgeR].forEach(function (b) {
      b.classList.remove('bump');
      void b.offsetWidth;
      b.classList.add('bump');
      if (b._bumpT) clearTimeout(b._bumpT);
      b._bumpT = setTimeout(function () { b.classList.remove('bump'); }, 560);
    });
    render();
  }

  function toggleFs() {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else if (document.documentElement.requestFullscreen) {
      document.documentElement.requestFullscreen();
    }
  }

  edgeL.addEventListener('click', function () { go(cur - 1); });
  edgeR.addEventListener('click', function () { go(cur + 1); });

  document.addEventListener('keydown', function (e) {
    var tocOpen = toc.classList.contains('open');
    if (e.key === 'Escape') { toc.classList.remove('open'); return; }
    if (tocOpen) return;
    if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {
      e.preventDefault();
      go(cur + 1);
    } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
      e.preventDefault();
      go(cur - 1);
    } else if (e.key === 'Home') {
      go(0);
    } else if (e.key === 'End') {
      go(total - 1);
    } else if (e.key === 'f' || e.key === 'F') {
      toggleFs();
    }
  });

  var wheelLock = false;
  document.addEventListener('wheel', function (e) {
    if (toc.classList.contains('open')) return;
    if (wheelLock || Math.abs(e.deltaY) < 24) return;
    wheelLock = true;
    go(cur + (e.deltaY > 0 ? 1 : -1));
    setTimeout(function () { wheelLock = false; }, 1150);
  }, { passive: true });

  var tx = null;
  document.addEventListener('touchstart', function (e) {
    tx = e.changedTouches[0].clientX;
  }, { passive: true });
  document.addEventListener('touchend', function (e) {
    if (tx === null) return;
    var dx = e.changedTouches[0].clientX - tx;
    tx = null;
    if (Math.abs(dx) > 60) go(cur + (dx < 0 ? 1 : -1));
  }, { passive: true });

  // TOC
  slides.forEach(function (sl, i) {
    var b = document.createElement('button');
    b.innerHTML = '<span class="no">' + String(i + 1).padStart(2, '0') + '</span><span class="tt">' +
      (sl.dataset.title || ('Slide ' + (i + 1))) + '</span>';
    b.addEventListener('click', function () {
      toc.classList.remove('open');
      go(i);
    });
    tocGrid.appendChild(b);
  });
  document.getElementById('btnToc').addEventListener('click', function () { toc.classList.add('open'); });
  document.getElementById('tocClose').addEventListener('click', function () { toc.classList.remove('open'); });
  document.getElementById('btnFs').addEventListener('click', toggleFs);

  var doodlesDone = false;
  function initDoodles() {
    if (doodlesDone || !window.DeckDoodles) return;
    doodlesDone = true;
    window.DeckDoodles.place(slides);
    window.DeckDoodles.draw(slides[cur]);
  }

  var fontsReady = (document.fonts && document.fonts.ready) ? document.fonts.ready : Promise.resolve();
  var pageLoaded = new Promise(function (resolve) {
    if (document.readyState === 'complete') resolve();
    else window.addEventListener('load', resolve, { once: true });
  });
  Promise.all([fontsReady, pageLoaded]).then(function () {
    setTimeout(initDoodles, 120);
  });
  setTimeout(initDoodles, 2600);

  window.addEventListener('resize', fit);
  fit();
  render();
})();
