# 科研进度看板（本地）

## 启动

双击 `start.command`（或在终端运行 `python3 server.py`），浏览器会自动打开 http://127.0.0.1:47321/ 。关闭终端窗口即停止服务。

首次双击 `start.command` 时如果 macOS 提示无法打开，右键选择「打开」一次即可。

## 文件

- `index.html`：页面
- `server.py`：本地服务，负责读取和保存 `data.json`
- `data.json`：所有内容
- `vendor/marked.min.js`：Markdown 渲染库

## 日常怎么用

- 点「＋ 新增卡片」新建当天的卡片，填好后点「保存」，内容立即写入 `data.json`。
- 点卡片右上角「编辑」修改内容；编辑状态下可以删除卡片。
- 任务、问题、实验内容和结论都支持 Markdown：`- 列表`、`1. 编号`、`**加粗**`、`` `代码` ``。
- 实验状态可选：计划 / 进行中 / 完成 / 无效。
- 阶段推进时，直接编辑 `data.json` 中 `stages` 的 `status`（`done` / `current` / `todo`），刷新页面即可。

## 同步到 GitHub

点击「同步到 GitHub」，会保存所有正在编辑的卡片，将 `data.json` 的改动提交，再推送到仓库的 `main` 分支。页面会显示成功或失败。同步失败时内容仍保存在本机，可以检查网络后再次点击。

此功能使用本机 `~/.ssh/config` 中的 `github-ethan` 配置，远程仓库为 `git@github-ethan:ethan-404-sys/Research_Board.git`。需要保持本地服务运行，并能连接 GitHub。没有新改动时仍会重试尚未推送的提交。按钮提交的文件为 `data.json`，页面和服务代码的修改需要通过终端提交。

在其他设备修改过仓库时，应先在终端合并远程更新，再同步。推送被拒绝时页面会显示 Git 错误。
