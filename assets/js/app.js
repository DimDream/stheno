(function () {
  "use strict";

  var stage = document.getElementById("stage");
  var box = document.getElementById("dialogueBox");
  var textEl = document.getElementById("dialogueText");
  var nextEl = document.getElementById("nextArrow");
  var sthenoBtn = document.getElementById("sthenoBtn");
  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- 固定舞台 + 自适应缩放 ---------- */
  var mobileMQ = window.matchMedia("(max-width: 860px) and (orientation: portrait)");
  function fitStage() {
    var isMobile = mobileMQ.matches;
    var W = isMobile ? 430 : 1280;
    var H = isMobile ? 860 : 800;
    stage.classList.toggle("mobile", isMobile);
    stage.style.width = W + "px";
    stage.style.height = H + "px";
    var s = Math.min(window.innerWidth / W, window.innerHeight / H, 1.5);
    stage.style.transform = "scale(" + s + ")";
  }
  window.addEventListener("resize", fitStage);
  window.addEventListener("orientationchange", fitStage);
  fitStage();

  /* ---------- 菜单当前项高亮 ---------- */
  var page = document.body.getAttribute("data-page") || "";
  var items = document.querySelectorAll(".menu-item");
  for (var i = 0; i < items.length; i++) {
    if (items[i].getAttribute("data-nav") === page) {
      items[i].classList.add("active");
    }
  }

  /* ---------- 空气里的尘埃 ---------- */
  if (!reduceMotion) {
    for (var m = 0; m < 14; m++) {
      var mote = document.createElement("span");
      mote.className = "mote";
      var sz = 2 + Math.random() * 2.2;
      mote.style.width = sz + "px";
      mote.style.height = sz + "px";
      mote.style.left = (6 + Math.random() * 88) + "%";
      mote.style.top = (58 + Math.random() * 42) + "%";
      mote.style.animationDuration = (10 + Math.random() * 10) + "s";
      mote.style.animationDelay = (-Math.random() * 16) + "s";
      stage.appendChild(mote);
    }
  }

  /* ---------- 对话框打字机 ---------- */
  var lines = (window.DIALOGUE_LINES || []).slice();
  var idx = 0;
  var typing = false;
  var timer = null;
  var aside = false;
  var saved = null;

  /* ---------- 台词解析：支持 [文字](网址) 超链接 ---------- */
  function escHtml(s) {
    return String(s).replace(/[&<>]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c];
    });
  }
  function safeUrl(u) {
    u = String(u).trim();
    if (/^(https?:|mailto:|tel:)/i.test(u)) return u;
    if (/^[#./]/.test(u) || !/^[a-z][a-z0-9+.-]*:/i.test(u)) return u; // 站内相对路径 / 锚点
    return ""; // 拒绝 javascript: 等危险协议
  }
  function parseLine(line) {
    var tokens = [], re = /\[([^\]]+)\]\(([^)\s]+)\)/g, last = 0, m;
    while ((m = re.exec(line)) !== null) {
      if (m.index > last) tokens.push({ t: "text", v: line.slice(last, m.index) });
      tokens.push({ t: "link", text: m[1], url: safeUrl(m[2]) });
      last = re.lastIndex;
    }
    if (last < line.length) tokens.push({ t: "text", v: line.slice(last) });
    return tokens;
  }
  function buildHTML(tokens, n) {
    var html = "", left = n;
    for (var i = 0; i < tokens.length; i++) {
      var tk = tokens[i];
      if (tk.t === "text") {
        var take = Math.min(tk.v.length, left);
        html += escHtml(tk.v.slice(0, take));
        left -= take;
      } else {
        if (!tk.url) { // 危险网址降级为纯文字
          var lt = Math.min(tk.text.length, left);
          html += escHtml(tk.text.slice(0, lt));
          left -= lt;
          if (left <= 0) break;
          continue;
        }
        var ltk = Math.min(tk.text.length, left);
        html += '<a href="' + escHtml(tk.url).replace(/"/g, "&quot;") + '" target="_blank" rel="noopener noreferrer">' + escHtml(tk.text.slice(0, ltk)) + "</a>";
        left -= ltk;
      }
      if (left <= 0) break;
    }
    return html;
  }

  function setArrow(on) {
    nextEl.classList.toggle("show", !!on);
  }

  function done(line) {
    if (timer) { clearInterval(timer); timer = null; }
    textEl.innerHTML = buildHTML(parseLine(line), Infinity);
    textEl.classList.remove("typing");
    typing = false;
    setArrow(aside || idx < lines.length - 1);
  }

  function typeLine(line) {
    typing = true;
    setArrow(false);
    textEl.classList.add("typing");
    if (reduceMotion) { done(line); return; }
    var toks = parseLine(line);
    var len = 0;
    for (var i = 0; i < toks.length; i++) {
      len += (toks[i].t === "link") ? toks[i].text.length : toks[i].v.length;
    }
    var n = 0;
    textEl.innerHTML = "";
    timer = setInterval(function () {
      n += 1;
      textEl.innerHTML = buildHTML(toks, n);
      if (n >= len) { done(line); }
    }, 36);
  }

  function advance() {
    if (typing) { done(lines[idx]); return; }
    if (aside) {
      aside = false;
      if (saved) {
        lines = saved.lines;
        idx = Math.min(saved.idx, lines.length - 1);
        saved = null;
        textEl.innerHTML = buildHTML(parseLine(lines[idx]), Infinity);
        textEl.classList.remove("typing");
        setArrow(idx < lines.length - 1);
      } else {
        setArrow(false);
      }
      return;
    }
    idx += 1;
    if (idx < lines.length) {
      typeLine(lines[idx]);
    } else {
      setArrow(false);
    }
  }

  if (box) {
    box.addEventListener("click", function (e) {
      if (e.target && e.target.closest && e.target.closest("a, button")) { return; }
      advance();
    });
  }
  document.addEventListener("keydown", function (e) {
    var code = e.code;
    if (code === "Space" || code === "Enter" || code === "ArrowRight" || code === "ArrowDown") {
      var t = e.target || document.body;
      if (t.closest && t.closest("a, button")) { return; }
      e.preventDefault();
      advance();
    }
  });

  /* ---------- 点一下丝西娜 ---------- */
  var quips = [
    "……手别乱摸，吧台要另外收费。",
    "酒还满着。观察力不错，旅人。",
    "嗯？我脸上有东西？……是蛇，不是脏东西。",
    "打烊时间？对旅人来说，这里永远是刚开门。",
    "今天的月光适合配梅子酒。我请你一杯，记你账上。",
    "别盯着蛇看，它们会害羞。……骗你的，它们不会。",
    "坐吧。椅子比传闻中结实得多。",
    "想听故事，还是想喝酒？小孩子才做选择——我两样都收费。",
    "（她擦着杯子，没抬头）位置随便坐，吧台后面不行。"
  ];
  if (sthenoBtn) {
    sthenoBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      var q = quips[Math.floor(Math.random() * quips.length)];
      if (!aside) { saved = { lines: lines, idx: idx }; }
      lines = [q];
      idx = 0;
      aside = true;
      typeLine(q);
    });
  }

  if (lines.length > 0) { typeLine(lines[0]); }
})();
