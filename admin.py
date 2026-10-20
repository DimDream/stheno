#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
丝西娜的酒馆 — 可视化管理后台
================================

一个零依赖的本地 Web 管理工具，用于维护博客的栏目与文章，并一键同步到 GitHub。

功能：
  - 可视化维护：站点信息、首页台词、栏目（增删改）、文章（增删改）
  - 一键重新生成静态站点（调用 build.py）
  - 内置站点预览（iframe 直连本地文件，无需额外服务器）
  - 一键同步到 GitHub（git init / commit / push，使用 SSH key）

用法：
  python admin.py            # 默认在本机 8800 端口启动
  python admin.py 9000       # 指定端口

然后浏览器打开 http://localhost:8800
"""

import io
import json
import os
import subprocess
import sys
import mimetypes
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

# ---------------------------------------------------------------- 路径配置
HERE = os.path.dirname(os.path.abspath(__file__))
STHENO_DIR = HERE                                   # 博客根目录（与 admin 同级）
DATA_FILE = os.path.join(STHENO_DIR, "posts.json")
BUILD_SCRIPT = os.path.join(STHENO_DIR, "build.py")
ADMIN_UI = os.path.join(STHENO_DIR, "admin_ui.html")
CFG_FILE = os.path.join(STHENO_DIR, ".stheno_admin.json")
GIT_KEY = r"G:/moumou_deploy/id_ed25519"            # 复用的 GitHub SSH 私钥
DEFAULT_PORT = 8800

PYTHON = sys.executable


# ---------------------------------------------------------------- 工具
def load_data():
    if os.path.exists(DATA_FILE):
        with io.open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"site": {"title": "丝西娜的酒馆", "owner": "丝西娜"},
            "home_lines": [], "cat_intro": {}, "categories": [], "posts": []}


def save_data(data):
    with io.open(DATA_FILE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_cfg():
    if os.path.exists(CFG_FILE):
        try:
            with io.open(CFG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"repo_url": "", "branch": "main", "ssh_key": GIT_KEY, "remote": "origin"}


def save_cfg(cfg):
    with io.open(CFG_FILE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.write("\n")


# ---------------------------------------------------------------- Git 同步
def run_git(args, cwd=STHENO_DIR, cfg=None):
    env = dict(os.environ)
    if cfg and cfg.get("ssh_key") and os.path.exists(cfg["ssh_key"]):
        env["GIT_SSH_COMMAND"] = 'ssh -i "%s" -o IdentitiesOnly=yes -o StrictHostKeyChecking=no' % cfg["ssh_key"]
    proc = subprocess.run(
        ["git"] + args, cwd=cwd, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    out = (proc.stdout or b"").decode("utf-8", "replace")
    err = (proc.stderr or b"").decode("utf-8", "replace")
    return proc.returncode, out, err


def git_initialized():
    return os.path.isdir(os.path.join(STHENO_DIR, ".git"))


def get_git_state(cfg):
    state = {"initialized": git_initialized(), "remote": "", "branch": "",
             "dirty": False, "last_commit": "", "ahead": 0}
    if not state["initialized"]:
        return state
    rc, out, err = run_git(["config", "--get", "remote.%s.url" % cfg.get("remote", "origin")])
    if rc == 0:
        state["remote"] = out.strip()
    rc, out, err = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    if rc == 0:
        state["branch"] = out.strip()
    rc, out, err = run_git(["status", "--porcelain"])
    state["dirty"] = bool(out.strip())
    rc, out, err = run_git(["log", "-1", "--format=%h %s"])
    if rc == 0:
        state["last_commit"] = out.strip()
    # 是否已设置 upstream
    rc, out, err = run_git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    if rc != 0:
        # 未设置 upstream：用本地提交数粗略表示待推送量
        rc, out, err = run_git(["rev-list", "--count", "HEAD"])
        if rc == 0:
            try:
                state["ahead"] = int(out.strip())
            except ValueError:
                state["ahead"] = 0
    return state


def sync_to_github():
    """执行一次完整的 git 同步：init(若需) -> remote -> add -> commit -> push。
    返回 (ok, log_list)。可被 push_github_ssh.py 直接调用。"""
    cfg = load_cfg()
    log = []
    if not cfg.get("repo_url"):
        return False, ["未配置 GitHub 远程仓库地址。请在管理后台「GitHub 同步」页填写，或编辑 .stheno_admin.json 的 repo_url。"]
    if not os.path.exists(cfg.get("ssh_key", "")):
        return False, ["SSH 私钥不存在：%s" % cfg.get("ssh_key")]

    # 1. 初始化
    if not git_initialized():
        rc, out, err = run_git(["init"])
        log.append(("OK" if rc == 0 else "ERR") + " git init: " + (out or err).strip())
        if rc != 0:
            return False, log
        run_git(["config", "user.name", "stheno-bot"])
        run_git(["config", "user.email", "stheno@local"])
        run_git(["checkout", "-b", cfg.get("branch", "main")])
        # 写入 .gitignore，避免把临时预览图误传
        ignore = os.path.join(STHENO_DIR, ".gitignore")
        with io.open(ignore, "w", encoding="utf-8") as f:
            f.write("preview-*.png\n*.tmp\n")
        log.append("已初始化本地仓库（分支 %s）" % cfg.get("branch", "main"))

    # 2. 远程
    rc, out, err = run_git(["config", "--get", "remote.%s.url" % cfg.get("remote", "origin")])
    if rc == 0 and out.strip():
        run_git(["remote", "set-url", cfg.get("remote", "origin"), cfg["repo_url"]])
        log.append("已更新远程地址")
    else:
        run_git(["remote", "add", cfg.get("remote", "origin"), cfg["repo_url"]])
        log.append("已添加远程 %s" % cfg["repo_url"])

    # 3. 暂存
    rc, out, err = run_git(["add", "-A"])
    if rc != 0:
        return False, log + ["ERR git add: " + err.strip()]
    log.append("已暂存全部变更")

    # 4. 提交
    rc, out, err = run_git(["status", "--porcelain"])
    if out.strip():
        msg = "博客内容更新 %s" % __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")
        rc, out, err = run_git(["commit", "-m", msg])
        if rc == 0:
            log.append("已提交：" + msg)
        else:
            return False, log + ["ERR git commit: " + (err or out).strip()]
    else:
        log.append("没有需要提交的变更")

    # 5. 推送
    rc, out, err = run_git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    branch = cfg.get("branch", "main")
    remote = cfg.get("remote", "origin")
    if rc == 0:
        rc, out, err = run_git(["push"])
        tail = out.strip() or err.strip()
    else:
        rc, out, err = run_git(["push", "-u", remote, branch])
        tail = out.strip() or err.strip()
    if rc == 0:
        log.append("已推送到 GitHub（%s/%s）" % (remote, branch))
        return True, log
    errmsg = tail or "推送失败"
    log.append("ERR git push: " + errmsg)
    # 常见引导
    if "could not read Username" in errmsg or "Authentication" in errmsg:
        log.append("提示：推送需要 SSH 认证。请确认该 SSH key 已添加到你的 GitHub 账户，且 repo_url 为 SSH 格式（git@github.com:用户名/仓库.git）。")
    elif "repository not found" in errmsg or "does not exist" in errmsg:
        log.append("提示：远程仓库不存在或无权限。请先在 GitHub 上创建该空仓库，再同步。")
    return False, log


# ---------------------------------------------------------------- 重新生成站点
def rebuild_site():
    if not os.path.exists(BUILD_SCRIPT):
        return False, "未找到 build.py"
    try:
        proc = subprocess.run([PYTHON, BUILD_SCRIPT, "--out", STHENO_DIR],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        out = (proc.stdout or b"").decode("utf-8", "replace")
        err = (proc.stderr or b"").decode("utf-8", "replace")
        if proc.returncode == 0:
            return True, out.strip() or "生成成功"
        return False, (err or out).strip()
    except Exception as e:
        return False, "生成异常：" + str(e)


# ---------------------------------------------------------------- HTTP 处理
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False)
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _json_body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8", "replace"))
        except Exception:
            return {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            if os.path.exists(ADMIN_UI):
                with io.open(ADMIN_UI, "r", encoding="utf-8") as f:
                    return self._send(200, f.read(), "text/html; charset=utf-8")
            return self._send(404, "未找到 admin_ui.html")

        if path == "/api/state":
            data = load_data()
            cfg = load_cfg()
            git = get_git_state(cfg)
            return self._send(200, {
                "site": data.get("site", {}),
                "home_lines": data.get("home_lines", []),
                "cat_intro": data.get("cat_intro", {}),
                "categories": data.get("categories", []),
                "posts": data.get("posts", []),
                "git": git,
                "git_cfg": {"repo_url": cfg.get("repo_url", ""),
                            "branch": cfg.get("branch", "main"),
                            "ssh_key": cfg.get("ssh_key", "")},
            })

        if path == "/api/git-config":
            return self._send(200, load_cfg())

        if path.startswith("/site/"):
            return self._serve_site(path[len("/site/"):])

        return self._send(404, {"ok": False, "error": "not found"})

    def _serve_site(self, rel):
        # 防目录穿越
        rel = urllib.parse.unquote(rel)
        target = os.path.normpath(os.path.join(STHENO_DIR, rel))
        if not target.startswith(os.path.normpath(STHENO_DIR)):
            return self._send(403, "forbidden")
        if os.path.isdir(target):
            target = os.path.join(target, "index.html")
        if not os.path.exists(target):
            return self._send(404, "文件不存在：" + rel)
        ctype, _ = mimetypes.guess_type(target)
        if not ctype:
            ctype = "application/octet-stream"
        with io.open(target, "rb") as f:
            return self._send(200, f.read(), ctype)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._json_body()

        if path == "/api/site":
            data = load_data()
            data["site"] = body.get("site", data.get("site", {}))
            data["home_lines"] = body.get("home_lines", data.get("home_lines", []))
            save_data(data)
            return self._send(200, {"ok": True})

        if path == "/api/category":
            data = load_data()
            cats = data.setdefault("categories", [])
            cat_intro = data.setdefault("cat_intro", {})
            cid = body.get("id", "").strip()
            if not cid:
                return self._send(400, {"ok": False, "error": "栏目 id 不能为空"})
            existing = next((c for c in cats if c["id"] == cid), None)
            info = {"id": cid, "name": body.get("name", cid),
                    "icon": body.get("icon", "mug"), "desc": body.get("desc", "")}
            if existing:
                existing.update(info)
            else:
                cats.append(info)
            cat_intro[cid] = body.get("intro", cat_intro.get(cid, []))
            save_data(data)
            return self._send(200, {"ok": True, "category": info})

        if path == "/api/post":
            data = load_data()
            posts = data.setdefault("posts", [])
            pid = body.get("id", "").strip()
            if not pid:
                return self._send(400, {"ok": False, "error": "文章 id 不能为空"})
            existing = next((p for p in posts if p["id"] == pid), None)
            info = {"id": pid, "cat": body.get("cat", ""),
                    "title": body.get("title", ""), "date": body.get("date", ""),
                    "lines": body.get("lines", [])}
            if existing:
                existing.update(info)
            else:
                posts.append(info)
            save_data(data)
            return self._send(200, {"ok": True, "post": info})

        if path == "/api/git-config":
            cfg = load_cfg()
            cfg.update({k: body[k] for k in ("repo_url", "branch", "ssh_key", "remote") if k in body})
            save_cfg(cfg)
            return self._send(200, {"ok": True, "cfg": cfg})

        if path == "/api/git-sync":
            ok, log = sync_to_github()
            return self._send(200, {"ok": ok, "log": log, "git": get_git_state(load_cfg())})

        if path == "/api/rebuild":
            ok, msg = rebuild_site()
            return self._send(200, {"ok": ok, "message": msg})

        return self._send(404, {"ok": False, "error": "not found"})

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._json_body()

        if path == "/api/category":
            data = load_data()
            cid = body.get("id", "")
            before = len(data.get("posts", []))
            data["posts"] = [p for p in data.get("posts", []) if p.get("cat") != cid]
            data["categories"] = [c for c in data.get("categories", []) if c["id"] != cid]
            data.get("cat_intro", {}).pop(cid, None)
            save_data(data)
            removed = before - len(data["posts"])
            return self._send(200, {"ok": True, "removed_posts": removed})

        if path == "/api/post":
            data = load_data()
            pid = body.get("id", "")
            data["posts"] = [p for p in data.get("posts", []) if p["id"] != pid]
            save_data(data)
            return self._send(200, {"ok": True})

        return self._send(404, {"ok": False, "error": "not found"})


def main():
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    server = HTTPServer(("127.0.0.1", port), Handler)
    print("丝西娜的酒馆 · 管理后台已启动")
    print("  浏览器打开： http://localhost:%d" % port)
    print("  博客根目录： %s" % STHENO_DIR)
    print("  按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
        server.shutdown()


if __name__ == "__main__":
    main()
