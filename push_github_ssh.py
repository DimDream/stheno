#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
丝西娜的酒馆 — 独立 GitHub 同步脚本
====================================
直接把博客项目用 SSH key 推送到 GitHub（git init / commit / push 自动完成）。
配置读取自 .stheno_admin.json（远程地址、分支、SSH 私钥路径）。

用法：
  python push_github_ssh.py

首次使用前，请先在管理后台「GitHub 同步」页填写远程仓库地址并保存，
或手动编辑 .stheno_admin.json 的 repo_url 字段。
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import admin  # noqa: E402


def main():
    print("== 丝西娜的酒馆 · 同步到 GitHub ==")
    ok, log = admin.sync_to_github()
    for line in log:
        print(("  ✔ " if not line.startswith("ERR") else "  ✘ ") + line)
    if ok:
        print("\n完成：已推送到 GitHub。")
        sys.exit(0)
    else:
        print("\n未完成，请根据上面的提示修正（通常是远程仓库地址或 SSH key）。")
        sys.exit(1)


if __name__ == "__main__":
    main()
