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

建议把这个文件夹放进一个私有 git 仓库或网盘同步，`data.json` 的 diff 就是天然的进度历史。
