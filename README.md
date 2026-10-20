# 丝西娜的酒馆

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
