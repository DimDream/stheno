#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
丝西娜的酒馆 — 静态个人博客生成器
================================

页面结构（视觉小说 / 游戏对话框风格）：
  - 舞台中央：酒馆女老板「丝西娜」立绘（固定居中，永不移动）
  - 立绘下方：对话框，博客内容以「丝西娜说的话」逐字打出
  - 舞台右侧：游戏菜单风格分类入口（咨询 / 杂谈），点击进入子页面
  - 固定舞台尺寸 + JS 等比缩放：桌面 1280x800，手机 430x860

素材（assets/img/，需自备）：
  背景.png   酒馆吧台全景，铺满舞台
  丝西娜.png 人物立绘（透明底 PNG），居中显示
  favicon.png 站点图标

用法：
  python build.py [输出目录]     默认输出到本脚本所在目录
  python build.py --out G:/Stheno

内容维护：编辑输出目录下的 posts.json 后重新运行 python build.py
"""

import io
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- 默认内容
DEFAULT_DATA = {
    "site": {"title": "丝西娜的酒馆", "owner": "丝西娜"},
    "home_lines": [
        "（门上的铜铃响了一声）欢迎，远道而来的旅人。",
        "这里是丝西娜的酒馆。不卖故事，只卖酒，和一点点容身之处。",
        "吧台永远擦得很亮，靠窗的位置看得见月亮。",
        "右边柜子里有我平时写的东西，归好类了。想看哪本，自己拿。",
        "还有——心情好的时候，点我一下，也不会挨打。",
        "当然，也可以只是坐着。坐着，也是酒馆的一部分。"
    ],
    "cat_intro": {
        "zixun": ["咨询箱里的问题，我挑了一些来回答。", "都是些深夜问题，得配深夜酒一起看。", "选一封吧，旅人。"],
        "zatan": ["杂谈，就是没分类的唠叨。", "酒馆老板娘的特权：想到哪，写到哪。", "随便翻，翻到哪页算哪页。"]
    },
    "categories": [
        {"id": "zixun", "name": "咨询", "icon": "scroll", "desc": "深夜问题，配深夜酒"},
        {"id": "zatan", "name": "杂谈", "icon": "mug", "desc": "没分类的唠叨"}
    ],
    "posts": [
        {
            "id": "advice-late-night",
            "cat": "zixun",
            "title": "咨询：深夜买醉的自我保护指南",
            "date": "2026-10-12",
            "lines": [
                "常有旅人问我：老板娘，深夜来喝酒，怎么才能既尽兴又不出事？",
                "第一条，杯子不离视线。下过药的酒，比沼泽里的瘴气还难防。",
                "第二条，账要当面结。模糊的账单和模糊的记忆一样，最容易被人做成陷阱。",
                "第三条，也是最重要的一条——觉得不对，立刻走人。酒馆的门永远开着：进来是客，出去是自由。",
                "尽兴而归，才不辜负这一夜的酒。"
            ]
        },
        {
            "id": "advice-monday",
            "cat": "zixun",
            "title": "咨询：周一综合征的土方子",
            "date": "2026-10-05",
            "lines": [
                "周一早上，连吧台上的木纹都显得无精打采。",
                "我的土方子：周五夜里预留半杯好酒，周日深夜再喝掉它——让周末的尾巴，扫过周一的额头。",
                "辅以早起十分钟的阳光，和一段不看消息的通勤路。",
                "一个疗程就好，别贪杯。",
                "如果还是不行，就来酒馆。周一的吧台，永远给你留一个安静的角落。"
            ]
        },
        {
            "id": "advice-snake-hair",
            "cat": "zixun",
            "title": "咨询：蛇发打结的一百种解法",
            "date": "2026-09-28",
            "lines": [
                "这一条其实不是旅人问的，是有人托梦问的：你那一头蛇，早上打结怎么办？",
                "普通梳子不行，它们咬。犀角梳太痒，桃木梳起火。",
                "试了十几年，最后发现它们只认一把旧的黄杨木梳——大概因为旧东西脾气好。",
                "结论：头发要有耐心，蛇也一样。急不得，急了真咬你。"
            ]
        },
        {
            "id": "after-closing",
            "cat": "zatan",
            "title": "打烊之后的半小时",
            "date": "2026-10-15",
            "lines": [
                "客人们散去，杯子洗净，椅子归位。酒馆进入一天里最安静的半小时。",
                "这时候我常坐在吧台里面，听木头的吱呀声，听酒桶呼吸，听远处城市的低鸣。",
                "有人说酒馆的灵魂在热闹的时候。我不这么看。",
                "灵魂是在打烊之后，还愿意留下来的那点灯光。"
            ]
        },
        {
            "id": "autumn-menu",
            "cat": "zatan",
            "title": "本周酒单 · 秋日限定",
            "date": "2026-10-10",
            "lines": [
                "秋深了，换酒单。",
                "新上「蛇发缠绕」：梅酒加一点肉桂，后劲像被蛇缠住，慢慢收紧。",
                "还有「石头汤」：热红酒的远房表亲，橙子、丁香，和一点点不切实际的野心。",
                "老位置留灯，老价格不变。新酒等老友。"
            ]
        },
        {
            "id": "about-name",
            "cat": "zatan",
            "title": "关于「丝西娜」这个名字",
            "date": "2026-09-30",
            "lines": [
                "有人叫我丝西娜，说听起来像某种古老的诅咒。",
                "其实那是很老很老的故事里，一个不太走运的名字。不过我不介意。",
                "名字是别人给的，酒馆是自己开的。被叫错一百年，也还是我。",
                "所以——欢迎来到丝西娜的酒馆。名字归故事，酒归你。"
            ]
        }
    ]
}

# ---------------------------------------------------------------- 样式
CSS = r"""@charset "UTF-8";
/* 丝西娜的酒馆 — 样式 */
:root{
  --gold:#e6c583;
  --gold-soft:#f0d9a8;
  --gold-dim:#b8934f;
  --wood-edge:#6b4a2a;
  --panel:rgba(22,15,10,.92);
  --parchment:#f3e7cf;
  --text-dim:#c9b394;
  --foot:#8d7654;
}
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{height:100%;overflow:hidden}
body{background:#070503;color:var(--parchment);font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;-webkit-font-smoothing:antialiased}
#viewport{position:fixed;left:0;top:0;right:0;bottom:0;display:flex;align-items:center;justify-content:center;overflow:hidden;background:radial-gradient(ellipse at center,#16100b 0%,#070503 78%)}
.stage{position:relative;width:1280px;height:800px;flex:none;overflow:hidden;transform-origin:center center;box-shadow:0 0 90px rgba(0,0,0,.95),0 0 0 1px #241812}

/* ---- 场景 ---- */
.scene-bg{position:absolute;left:0;top:0;right:0;bottom:0;background-image:url("../img/背景.png");background-size:cover;background-position:center center;z-index:0}
.halo{position:absolute;left:50%;top:330px;width:540px;height:540px;transform:translate(-50%,-50%);border-radius:50%;background:radial-gradient(circle,rgba(255,205,130,.13),transparent 65%);animation:halo 6s ease-in-out infinite;pointer-events:none;z-index:1}
@keyframes halo{0%,100%{opacity:.55}50%{opacity:.95}}
.vignette{position:absolute;left:0;top:0;right:0;bottom:0;background:radial-gradient(ellipse at center,transparent 52%,rgba(4,2,1,.62) 100%);pointer-events:none;z-index:5}

/* ---- 丝西娜立绘 ---- */
.stheno{position:absolute;left:50%;bottom:0;transform:translateX(calc(-50% - 8px));height:560px;width:auto;z-index:3;pointer-events:none;user-select:none;-webkit-user-drag:none}
.stheno-click{position:absolute;left:50%;bottom:0;transform:translateX(calc(-50% - 8px));width:420px;height:560px;z-index:4;border:none;background:none;cursor:pointer;border-radius:46% 46% 0 0}
.stheno-hint{position:absolute;left:50%;top:2px;transform:translate(-50%,-100%);padding:2px 12px;border:1px solid var(--gold-dim);border-radius:12px;background:rgba(22,15,10,.92);color:var(--gold);font-size:13px;opacity:0;transition:opacity .2s;pointer-events:none;white-space:nowrap}
.stheno-click:hover .stheno-hint{opacity:1}

/* ---- 招牌 ---- */
.sign{position:absolute;top:0;left:50%;transform:translateX(-50%);display:flex;flex-direction:column;align-items:center;z-index:6}
.sign-rope{width:2px;height:22px;background:linear-gradient(180deg,#6a5230,#31240f)}
.sign-board{position:relative;padding:11px 36px 9px;text-align:center;white-space:nowrap;border:2px solid var(--wood-edge);border-radius:8px;background:linear-gradient(180deg,#4a3020,#31200f 62%,#241609);box-shadow:0 8px 22px rgba(0,0,0,.65),inset 0 1px 0 rgba(255,220,160,.28)}
.sign-title{display:block;font-family:"KaiTi","STKaiti","Kaiti SC",serif;font-size:34px;font-weight:700;color:var(--gold);letter-spacing:8px;text-shadow:0 2px 8px rgba(0,0,0,.85)}
.sign-sub{display:block;margin-top:2px;font-size:10px;letter-spacing:5px;color:var(--gold-dim)}
.lantern{position:absolute;top:16px;width:26px;transform-origin:50% 0;animation:swing 4.6s ease-in-out infinite;pointer-events:none}
.lantern-l{left:-62px}
.lantern-r{right:-62px;animation-delay:-2.3s}
.lantern::before{content:"";display:block;width:1px;height:11px;margin:0 auto;background:#6a5230}
.lantern-body{display:block;width:22px;height:29px;border-radius:45%;border:1px solid #d8a54e;background:radial-gradient(circle at 50% 35%,rgba(255,214,140,.95),rgba(214,120,40,.85) 70%,rgba(120,55,15,.9));box-shadow:0 0 18px 4px rgba(255,170,70,.35),0 0 42px 10px rgba(255,150,50,.16)}
.lantern::after{content:"";display:block;width:2px;height:9px;margin:2px auto 0;background:linear-gradient(180deg,#c33,#8a1f1f)}
@keyframes swing{0%,100%{transform:rotate(-5deg)}50%{transform:rotate(5deg)}}

/* ---- 游戏菜单 ---- */
.game-menu{position:absolute;right:36px;top:120px;width:214px;padding:14px 12px 12px;z-index:7;border:2px solid var(--wood-edge);border-radius:12px;background:var(--panel);box-shadow:0 12px 32px rgba(0,0,0,.6),inset 0 1px 0 rgba(255,220,160,.14)}
.menu-title{font-size:12px;letter-spacing:6px;color:var(--gold-dim);text-align:center;padding-bottom:10px;margin-bottom:6px;border-bottom:1px solid rgba(230,197,131,.25)}
.menu-item{position:relative;display:flex;align-items:center;gap:10px;margin:5px 0;padding:11px 12px;border:1px solid transparent;border-radius:8px;color:var(--parchment);text-decoration:none;font-size:17px;letter-spacing:3px;transition:background .15s,border-color .15s,transform .15s,color .15s}
.menu-item .ico{width:22px;height:22px;flex:none}
.menu-item::before{content:"▶";position:absolute;left:-13px;top:50%;transform:translate(4px,-50%);color:var(--gold);font-size:12px;opacity:0;transition:opacity .15s,transform .15s}
.menu-item:hover,.menu-item:focus-visible{background:rgba(230,197,131,.12);border-color:rgba(230,197,131,.5);transform:translateX(3px);color:#ffe9bd;outline:none}
.menu-item:hover::before,.menu-item.active::before{opacity:1;transform:translate(0,-50%)}
.menu-item.active{background:rgba(230,197,131,.16);border-color:rgba(230,197,131,.55);color:#ffe9bd}
.menu-foot{margin-top:10px;padding-top:8px;border-top:1px solid rgba(230,197,131,.2);font-size:11px;letter-spacing:3px;color:var(--foot);text-align:center}

/* ---- 对话框 ---- */
.dialogue-box{position:absolute;left:50%;bottom:26px;transform:translateX(-50%);width:920px;min-height:164px;padding:22px 30px 32px;z-index:7;cursor:pointer;border:2px solid var(--wood-edge);border-radius:14px;background:linear-gradient(180deg,rgba(28,18,11,.94),rgba(15,9,5,.965));box-shadow:0 16px 44px rgba(0,0,0,.68),inset 0 1px 0 rgba(255,220,160,.16)}
.dialogue-box::before,.dialogue-box::after{content:"";position:absolute;width:14px;height:14px;border:2px solid var(--gold-dim);pointer-events:none}
.dialogue-box::before{left:6px;top:6px;border-right:none;border-bottom:none;border-radius:4px 0 0 0}
.dialogue-box::after{right:6px;bottom:6px;border-left:none;border-top:none;border-radius:0 0 4px 0}
.name-plate{position:absolute;top:-17px;left:24px;padding:4px 16px;border:1px solid var(--gold-dim);border-radius:6px;background:linear-gradient(180deg,#5a3d22,#3a2513);font-family:"KaiTi","STKaiti",serif;font-size:18px;font-weight:700;color:var(--gold);letter-spacing:4px;box-shadow:0 4px 12px rgba(0,0,0,.55)}
.dialogue-text{min-height:92px;font-family:"KaiTi","STKaiti","Kaiti SC",serif;font-size:21px;line-height:1.9;letter-spacing:1px;color:#f5ead2;text-shadow:0 1px 3px rgba(0,0,0,.65)}
.dialogue-text.typing::after{content:"▌";color:var(--gold);animation:blink .8s steps(1) infinite}
.dialogue-text a{color:#ffd98a;text-decoration:underline;text-underline-offset:3px;text-shadow:none;font-weight:600;cursor:pointer}
.dialogue-text a:hover{color:#fff0c8}
.dialogue-text a:active{color:#ffbf66}
@keyframes blink{50%{opacity:0}}
.dialogue-next{position:absolute;right:20px;bottom:12px;color:var(--gold);font-size:14px;opacity:0;transition:opacity .2s;pointer-events:none}
.dialogue-next.show{opacity:1;animation:bob 1.1s ease-in-out infinite}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(4px)}}

/* ---- 手记列表 / 文章头 ---- */
.post-list,.post-header{position:absolute;left:36px;top:120px;width:340px;z-index:7;padding:14px;border:2px solid var(--wood-edge);border-radius:12px;background:var(--panel);box-shadow:0 12px 32px rgba(0,0,0,.6),inset 0 1px 0 rgba(255,220,160,.14)}
.post-list{max-height:440px;overflow:auto}
.list-head{display:flex;align-items:baseline;justify-content:space-between;padding-bottom:10px;margin-bottom:4px;border-bottom:1px solid rgba(230,197,131,.25)}
.list-title{font-family:"KaiTi","STKaiti",serif;font-size:19px;font-weight:700;color:var(--gold);letter-spacing:2px}
.list-count{font-size:12px;color:var(--foot)}
.list-desc{font-size:12px;color:var(--text-dim);letter-spacing:1px;padding:6px 2px 10px}
.post-item{display:block;margin-bottom:8px;padding:10px 12px;border:1px solid rgba(230,197,131,.18);border-radius:8px;background:rgba(255,240,210,.03);text-decoration:none;transition:border-color .15s,background .15s,transform .15s}
.post-item:hover{border-color:var(--gold);background:rgba(230,197,131,.1);transform:translateX(3px)}
.post-date{display:block;margin-bottom:3px;font-size:11px;letter-spacing:2px;color:#9c8560}
.post-title{display:block;font-size:15px;line-height:1.55;color:#f0e2c6}
.post-list::-webkit-scrollbar{width:6px}
.post-list::-webkit-scrollbar-thumb{background:rgba(230,197,131,.35);border-radius:3px}
.post-list::-webkit-scrollbar-track{background:transparent}
.back-btn{display:inline-flex;align-items:center;gap:6px;margin-bottom:12px;padding:5px 14px;border:1px solid rgba(230,197,131,.4);border-radius:6px;color:var(--gold-soft);text-decoration:none;font-size:13px;letter-spacing:2px;background:rgba(22,15,10,.6);transition:color .15s,border-color .15s,background .15s}
.back-btn:hover{color:#ffe9bd;border-color:var(--gold);background:rgba(230,197,131,.14)}
.post-meta{margin-bottom:4px;font-size:12px;letter-spacing:3px;color:#9c8560}
.post-title-h{font-family:"KaiTi","STKaiti",serif;font-size:24px;font-weight:700;line-height:1.45;letter-spacing:1px;color:var(--gold);text-shadow:0 2px 10px rgba(0,0,0,.8)}

/* ---- 其他 ---- */
.stage-foot{position:absolute;left:36px;bottom:14px;z-index:4;font-size:11px;letter-spacing:3px;color:rgba(141,118,84,.75);pointer-events:none}
.mote{position:absolute;z-index:5;border-radius:50%;background:rgba(255,214,150,.55);box-shadow:0 0 6px rgba(255,200,120,.65);pointer-events:none;animation-name:drift;animation-timing-function:linear;animation-iteration-count:infinite}
@keyframes drift{0%{transform:translateY(40px);opacity:0}15%{opacity:.85}100%{transform:translateY(-840px);opacity:0}}
.noscript-note{padding:8px 12px;border:1px dashed var(--gold-dim);border-radius:8px;color:var(--gold-soft);font-size:14px}

/* ---- 手机布局 ---- */
.stage.mobile{width:430px;height:860px}
.stage.mobile .sign-title{font-size:25px;letter-spacing:5px}
.stage.mobile .sign-board{padding:9px 20px 7px}
.stage.mobile .lantern-l{left:-38px}
.stage.mobile .lantern-r{right:-38px}
.stage.mobile .game-menu{right:10px;top:88px;width:50px;padding:8px 6px}
.stage.mobile .menu-title{font-size:9px;letter-spacing:2px;padding-bottom:6px;margin-bottom:4px}
.stage.mobile .menu-item{justify-content:center;padding:9px 0;margin:4px 0}
.stage.mobile .menu-item .label{display:none}
.stage.mobile .menu-item::before{display:none}
.stage.mobile .menu-foot{display:none}
.stage.mobile .stheno{bottom:0;height:560px;transform:translateX(calc(-50% - 7px))}
.stage.mobile .stheno-click{bottom:0;width:420px;height:560px;transform:translateX(calc(-50% - 7px))}
.stage.mobile .halo{top:520px;width:480px;height:480px}
.stage.mobile .post-list,.stage.mobile .post-header{left:10px;right:64px;top:60px;bottom:auto;width:auto;max-height:236px;padding:10px}
.stage.mobile .list-title{font-size:15px}
.stage.mobile .post-title{font-size:13px}
.stage.mobile .post-date{font-size:10px}
.stage.mobile .post-title-h{font-size:18px}
.stage.mobile .back-btn{font-size:12px;margin-bottom:8px;padding:4px 10px}
.stage.mobile .dialogue-box{left:10px;right:10px;width:auto;transform:none;bottom:12px;min-height:140px;padding:18px 16px 28px}
.stage.mobile .dialogue-text{min-height:70px;font-size:16px;line-height:1.75}
.stage.mobile .name-plate{font-size:15px;left:16px;padding:3px 12px;top:-14px}
.stage.mobile .stage-foot{display:none}
"""

# ---------------------------------------------------------------- 脚本
JS = r"""(function () {
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
"""

# ---------------------------------------------------------------- 页面模板
TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="丝西娜的酒馆 — 深夜仍营业的个人博客">
<title>{title}</title>
<link rel="icon" type="image/png" href="{prefix}assets/img/favicon.png">
<link rel="stylesheet" href="{prefix}assets/css/style.css">
</head>
<body data-page="{page_id}">
<div id="viewport">
<div id="stage" class="stage">
  <div class="scene-bg"></div>
  <div class="halo"></div>
  <img class="stheno" src="{prefix}assets/img/丝西娜.png" alt="酒馆女老板丝西娜">
  <button class="stheno-click" id="sthenoBtn" type="button" aria-label="和丝西娜说句话"><span class="stheno-hint">?</span></button>
  <div class="vignette"></div>
  <header class="sign">
    <div class="sign-rope"></div>
    <div class="sign-board"><span class="sign-title">丝西娜的酒馆</span><span class="sign-sub">STHENO&#39;S TAVERN</span></div>
    <div class="lantern lantern-l"><span class="lantern-body"></span></div>
    <div class="lantern lantern-r"><span class="lantern-body"></span></div>
  </header>
  {menu}
  {panel}
  <section class="dialogue-box" id="dialogueBox">
    <div class="name-plate">丝西娜</div>
    <div class="dialogue-text" id="dialogueText"></div>
    <noscript><div class="noscript-note">请启用 JavaScript，老板娘才能开口说话。</div></noscript>
    <div class="dialogue-next" id="nextArrow">▼</div>
  </section>
  <div class="stage-foot">丝西娜的酒馆 · 永夜营业中</div>
</div>
</div>
<script>window.DIALOGUE_LINES = {dialogue_lines};</script>
<script src="{prefix}assets/js/app.js"></script>
</body>
</html>
"""

# ---------------------------------------------------------------- 说明
README = """# 丝西娜的酒馆

一个静态个人博客：页面正中永远站着酒馆女老板「丝西娜」，博客内容以对话的形式显示在她下方的对话框中；右侧是游戏菜单风格的分类入口。

## 本地预览

方式一：直接用浏览器打开 `index.html`。
方式二（推荐，资源加载更稳）：

```bash
python -m http.server 8720
# 然后访问 http://localhost:8720
```

## 目录结构

```
index.html          首页（吧台）
zixun.html          咨询 · 子页面
zatan.html          杂谈 · 子页面
posts/*.html        文章页（内容即对话框台词）
assets/css/style.css  样式
assets/js/app.js      舞台缩放 / 打字机对话框 / 彩蛋
assets/img/           背景.png / 丝西娜.png / favicon.png
posts.json          全站内容数据
build.py            静态生成器
```

## 更新内容

1. 编辑 `posts.json`：文章、分类、首页与分类页开场白都在里面。
2. 运行 `python build.py` 重新生成全部页面。
3. 刷新浏览器。

新增一篇文章的示例（ posts.json 的 posts 数组里加一项）：

```json
{
  "id": "my-new-post",
  "cat": "zatan",
  "title": "文章标题",
  "date": "2026-10-19",
  "lines": ["第一段，会作为丝西娜的台词逐字打出。", "第二段。"]
}
```

新增分类：在 `categories` 加一项（id / name / icon / desc），在 `cat_intro` 加该 id 的开场白，`posts` 里引用该 id，再运行 `python build.py`。

## 在台词 / 文章里加超链接

任意 `lines` 文本都支持 Markdown 风格的链接语法：

```
[显示文字](网址)
```

例如：

```json
"lines": ["完整酒单已同步到 [GitHub](https://github.com)，随时来取。"]
```

- 链接会以金色下划线显示在对话框里，点击在新标签页打开（`target="_blank"`）。
- 网址支持 `http(s):` `mailto:` `tel:`，以及站内相对路径（以 `/` `./` `../` `#` 开头）。
- 出于安全，`javascript:` 等危险协议会被自动忽略，降级为纯文字。
- 在管理后台编辑台词 / 文章时，可用文本框上方的「🔗 插入链接」按钮自动生成该语法。

## 交互说明

- 点击对话框或按 空格 / 回车 / → ：逐条播放台词（打字中点击可立即显示全句）。
- 点击丝西娜本人：触发随机台词（彩蛋），再点一下回到原文。
- 页面为固定舞台尺寸（桌面 1280x800 / 手机 430x860），自动等比缩放适配屏幕，人物始终居中。

## 部署

纯静态、零依赖：把整个目录传到任意静态托管（GitHub Pages / Vercel / Netlify / 对象存储）即可。
"""

# ---------------------------------------------------------------- 图标
ICONS = {
    "home": '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="#e6c583" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v2.5"/><rect x="8.5" y="4.5" width="7" height="11" rx="2.5"/><path d="M9.5 15.5h5"/><path d="M10 20h4"/></svg>',
    "scroll": '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="#e6c583" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="5.5" y="3.5" width="13" height="17" rx="2"/><path d="M9 8h6"/><path d="M9 12h6"/><path d="M9 16h3"/></svg>',
    "mug": '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="#e6c583" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 9h11v8a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3V9z"/><path d="M16 10.5h2.5a2.5 2.5 0 0 1 0 5H16"/><path d="M8.5 6.5c0-1.2.8-1.2.8-2.4"/><path d="M12 6.5c0-1.2.8-1.2.8-2.4"/></svg>'
}


def esc(s):
    s = str(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def w(path, content):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def load_data(out):
    p = os.path.join(out, "posts.json")
    if os.path.exists(p):
        with io.open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_DATA


def menu_html(prefix, cats):
    items = ['<a class="menu-item" data-nav="home" href="' + prefix + 'index.html" title="吧台">' + ICONS["home"] + '<span class="label">吧台</span></a>']
    for c in cats:
        icon = ICONS.get(c.get("icon", ""), ICONS["mug"])
        items.append('<a class="menu-item" data-nav="' + esc(c["id"]) + '" href="' + prefix + esc(c["id"]) + '.html" title="' + esc(c["name"]) + '">' + icon + '<span class="label">' + esc(c["name"]) + '</span></a>')
    return '<nav class="game-menu" id="gameMenu"><div class="menu-title">菜 单</div>' + "".join(items) + '<div class="menu-foot">深夜仍营业</div></nav>'


def post_list_html(prefix, cat, posts):
    # 按发布日期倒序（最新在前）；日期为 ISO 格式时字典序即时间序
    posts = sorted(posts, key=lambda p: p.get("date", ""), reverse=True)
    rows = []
    for p in posts:
        rows.append('<a class="post-item" href="' + prefix + 'posts/' + esc(p["id"]) + '.html"><span class="post-date">' + esc(p["date"]) + '</span><span class="post-title">' + esc(p["title"]) + '</span></a>')
    return ('<aside class="post-list"><div class="list-head"><span class="list-title">手记柜 · ' + esc(cat["name"]) + '</span><span class="list-count">'
            + str(len(posts)) + ' 篇</span></div><div class="list-desc">' + esc(cat.get("desc", "")) + '</div>' + "".join(rows) + '</aside>')


def post_header_html(prefix, cat, post):
    return ('<div class="post-header"><a class="back-btn" href="' + prefix + esc(cat["id"]) + '.html">◀ 返回' + esc(cat["name"]) + '</a>'
            '<div class="post-meta">' + esc(cat["name"]) + ' · ' + esc(post["date"]) + '</div>'
            '<h1 class="post-title-h">' + esc(post["title"]) + '</h1></div>')


def shell(prefix, page_id, title, menu, panel, lines):
    lines_js = json.dumps(lines, ensure_ascii=False).replace("</", "<\\/")
    return TEMPLATE.format(prefix=prefix, page_id=page_id, title=esc(title), menu=menu, panel=panel, dialogue_lines=lines_js)


def main():
    out = HERE
    args = sys.argv[1:]
    if "--out" in args:
        out = args[args.index("--out") + 1]
    elif args:
        out = args[0]
    out = os.path.abspath(out)

    data = load_data(out)
    cats = data["categories"]

    w(os.path.join(out, "assets", "css", "style.css"), CSS)
    w(os.path.join(out, "assets", "js", "app.js"), JS)
    w(os.path.join(out, "posts.json"), json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    w(os.path.join(out, "README.md"), README)

    menu = menu_html("", cats)
    w(os.path.join(out, "index.html"),
      shell("", "home", data["site"]["title"], menu, "", data["home_lines"]))

    for cat in cats:
        posts = [p for p in data["posts"] if p["cat"] == cat["id"]]
        panel = post_list_html("", cat, posts)
        intro = data.get("cat_intro", {}).get(cat["id"], ["……"])
        w(os.path.join(out, cat["id"] + ".html"),
          shell("", cat["id"], cat["name"] + " · " + data["site"]["title"], menu, panel, intro))
        for p in posts:
            w(os.path.join(out, "posts", p["id"] + ".html"),
              shell("../", cat["id"], p["title"] + " · " + data["site"]["title"],
                    menu_html("../", cats), post_header_html("../", cat, p), p["lines"]))

    if os.path.abspath(out) != os.path.abspath(HERE):
        try:
            shutil.copyfile(os.path.abspath(__file__), os.path.join(out, "build.py"))
        except Exception as e:
            print("WARN: 复制 build.py 失败:", e)

    print("生成完成 ->", out)
    for name in ("背景.png", "丝西娜.png", "favicon.png"):
        fp = os.path.join(out, "assets", "img", name)
        print(("  [OK]  " if os.path.exists(fp) else "  [MISS]"), name)


if __name__ == "__main__":
    main()
