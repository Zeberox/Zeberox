/* Progressive enhancement. The site is fully readable without this file;
   it adds the EN/VI switch, live search + category filter, and copy buttons. */
(function () {
  "use strict";

  var I18N = window.__I18N__ || {};
  var LANGS = window.__LANGS__ || ["en"];
  var DEFAULT = window.__DEFAULT_LANG__ || "en";

  var lang = DEFAULT;
  try { lang = localStorage.getItem("lang") || DEFAULT; } catch (e) {}
  if (LANGS.indexOf(lang) === -1) lang = DEFAULT;

  function t(key) {
    return (I18N[lang] && I18N[lang][key]) ||
           (I18N[DEFAULT] && I18N[DEFAULT][key]) || key;
  }

  function fmtDate(iso) {
    try {
      return new Date(iso + "T00:00:00").toLocaleDateString(
        lang === "vi" ? "vi-VN" : "en-US",
        { year: "numeric", month: "short", day: "numeric" });
    } catch (e) { return iso; }
  }

  function applyLang() {
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      el.textContent = t(el.dataset.i18n);
    });
    document.querySelectorAll("[data-i18n-ph]").forEach(function (el) {
      el.setAttribute("placeholder", t(el.dataset.i18nPh));
    });
    document.querySelectorAll("[data-i18n-aria]").forEach(function (el) {
      el.setAttribute("aria-label", t(el.dataset.i18nAria));
    });
    document.querySelectorAll("time[data-date]").forEach(function (el) {
      var iso = el.getAttribute("datetime");
      if (iso) el.textContent = fmtDate(iso);
    });
    document.querySelectorAll("[data-lang]").forEach(function (b) {
      var on = b.dataset.lang === lang;
      b.setAttribute("aria-pressed", String(on));
      // move the sliding highlight onto the active segment
      if (on && b.dataset.i && b.parentNode) {
        b.parentNode.style.setProperty("--i", b.dataset.i);
      }
    });
    // swap bilingual post content (body + title + summary)
    document.querySelectorAll("[data-lang-body]").forEach(function (el) {
      el.hidden = el.dataset.langBody !== lang;
    });
    document.querySelectorAll("[data-lang-text]").forEach(function (el) {
      el.hidden = el.dataset.langText !== lang;
    });
    try {
      var h = document.querySelector('article h1 [data-lang-text="' + lang + '"]');
      if (h && window.__SITE_NAME__) document.title = h.textContent + " | " + window.__SITE_NAME__;
    } catch (e) {}
  }

  /* Flip the language: dim the translatable text, swap it at the midpoint of
     the fade, then let it come back. The highlight slides on its own in CSS. */
  var swapTimer = null;
  function setLang(next) {
    if (next === lang) return;
    lang = next;
    try { localStorage.setItem("lang", lang); } catch (err) {}

    var reduced = false;
    try {
      reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    } catch (err) {}
    if (reduced || !document.body) { applyLang(); return; }

    document.body.classList.add("lang-swapping");
    clearTimeout(swapTimer);
    swapTimer = setTimeout(function () {
      applyLang();
      requestAnimationFrame(function () {
        document.body.classList.remove("lang-swapping");
      });
    }, 180);
    // the switch itself should react immediately, not after the fade
    document.querySelectorAll("[data-lang]").forEach(function (b) {
      var on = b.dataset.lang === lang;
      b.setAttribute("aria-pressed", String(on));
      if (on && b.dataset.i && b.parentNode) {
        b.parentNode.style.setProperty("--i", b.dataset.i);
      }
    });
  }

  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-lang]");
    if (!b) return;
    setLang(b.dataset.lang);
  });

  /* arrow keys walk the switch, like a native segmented control */
  var seg = document.getElementById("langseg");
  if (seg) seg.addEventListener("keydown", function (e) {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    var btns = Array.prototype.slice.call(seg.querySelectorAll("[data-lang]"));
    var i = btns.indexOf(document.activeElement);
    if (i === -1) return;
    e.preventDefault();
    var next = btns[(i + (e.key === "ArrowRight" ? 1 : btns.length - 1)) % btns.length];
    next.focus();
    setLang(next.dataset.lang);
  });

  /* ---- search + category filter (writeups index) ---- */
  var q = document.getElementById("q");
  var chips = document.getElementById("chips");
  var results = document.getElementById("results");
  var empty = document.getElementById("empty");
  var filterCat = "";

  function runFilter() {
    if (!results) return;
    var query = (q && q.value || "").trim().toLowerCase();
    var shown = 0;
    results.querySelectorAll("[data-card]").forEach(function (card) {
      var ok = (!filterCat || card.dataset.cat === filterCat) &&
               (!query || (card.dataset.text || "").indexOf(query) !== -1);
      card.hidden = !ok;
      if (ok) shown++;
    });
    if (empty) empty.hidden = shown !== 0;
  }

  if (q) q.addEventListener("input", runFilter);
  if (chips) chips.addEventListener("click", function (e) {
    var b = e.target.closest(".chip");
    if (!b) return;
    filterCat = b.dataset.c || "";
    chips.querySelectorAll(".chip").forEach(function (x) {
      x.setAttribute("aria-pressed", String(x === b));
    });
    runFilter();
  });

  /* ---- copy buttons on code blocks ---- */
  document.querySelectorAll(".md pre").forEach(function (pre) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "copy";
    btn.dataset.i18n = "copy";
    btn.textContent = t("copy");
    btn.addEventListener("click", function () {
      var code = pre.querySelector("code");
      var text = code ? code.innerText : pre.innerText;
      var done = function () {
        delete btn.dataset.i18n;
        btn.textContent = t("copied");
        setTimeout(function () {
          btn.dataset.i18n = "copy";
          btn.textContent = t("copy");
        }, 1400);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { fallback(text, done); });
      } else {
        fallback(text, done);
      }
    });
    pre.appendChild(btn);
  });

  function fallback(text, done) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); done(); } catch (e) {}
    document.body.removeChild(ta);
  }

  if (lang !== DEFAULT) applyLang();
})();
