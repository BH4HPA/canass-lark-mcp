# 飞书 MCP 使用指南

你可以通过飞书 MCP 工具以**应用身份**（Claude）操作飞书云文档和消息。所有 API 调用使用 `tenant_access_token`，无需用户登录。

## 团队成员

| 成员 | open_id | 角色 |
|------|---------|------|
| Canass | `ou_3839de508ed93574a1e27eb556dcf68d` | 文档接收人，消息接收人 |
| Ray | `ou_27485e1ea4427c88d5e7d1f0108f1f2d` | 开发者 |

默认消息发送给 **Canass**。

## 两种调用方式

**读取操作**通过 MCP 工具调用（7 个工具，schema ~10K 字符，已常驻加载）。

**写入操作**通过 `lark_api.py` 脚本直接调用飞书 Open API（零 context 占用）：

```bash
python3 /path/to/canass-lark-mcp/lark_api.py <METHOD> '<API_PATH>' ['<JSON_BODY>']
```

> 为什么不用 MCP 做写入？写入相关的 MCP 工具 schema 高达 ~276K 字符（其中 `documentBlockChildren_create` 一个工具就占 194K），会吃掉大部分 context 窗口。直调 API 零占用且功能完全等价。

## MCP 工具速查（只读，7 个）

### 知识库

- `wiki_v2_space_getNode` — 获取知识库节点信息（将 wiki token 转换为实际 docx obj_token）

### 云文档读取

- `docs_v1_content_get` — 获取云文档 **Markdown** 格式内容（推荐用于理解文档内容，支持 wiki 文档）
- `docx_v1_documentBlock_list` — 获取文档所有块（含结构化信息，编辑文档时需要）

> **读取策略**：想要理解文档内容时，优先使用 `docs_v1_content_get`，它返回 Markdown 格式，保留标题层级、列表、待办等结构。需要编辑文档块时，再配合 `docx_v1_documentBlock_list` 获取块 ID。

### 云文档评论（只读）

- `drive_v1_fileComment_list` — 获取文档所有评论（支持读取全文评论和局部评论）
- `drive_v1_fileComment_get` — 获取单条评论详情
- `drive_v1_fileCommentReply_list` — 获取评论的回复列表

### 权限（只读）

- `drive_v1_permissionMember_list` — 获取协作者列表

## 查 lark-mcp 全量工具清单（排查 API 能力时用）

当要做的事不在本文档里、又不想靠盲试接口时，先翻 **lark-mcp 自带的工具索引**——它把飞书 Open API 按业务域做了聚合，每行带官方文档链接。`start.sh` 只挂了 7 个只读工具；完整清单在本地 npm 缓存里：

```bash
# 定位已安装的 lark-mcp 包
ls ~/.npm/_npx/*/node_modules/@larksuiteoapi/lark-mcp/package.json

# 工具清单（~1900 行，中/英双份）
MCP=~/.npm/_npx/*/node_modules/@larksuiteoapi/lark-mcp/docs
ls $MCP   # → tools-zh.md, tools-en.md
grep -n "docx.v1\|drive.v1.media\|board.v1" $MCP/tools-zh.md   # 按业务域搜
```

排查思路举例：
- 要画流程图 → 搜 `diagram`、`board`、`mermaid` → 只找到 `board.v1.whiteboardNode.list`（只读），没有创建接口 → 换方案（图片上传，见下文）。
- 要上传文件 → 搜 `upload` → 找到 `drive.v1.media.uploadPrepare/uploadFinish`（分片） → 另有 `drive/v1/medias/upload_all`（一次性，≤20 MB，MCP 未导出但 Open API 支持）。
- 要启动本地 mcp 看 CLI 选项 → `npx -y @larksuiteoapi/lark-mcp mcp --help`（可用 `--debug` 查 token 交换与请求体）。

> **没在 tools-zh.md 里找到 ≠ API 不支持**。lark-mcp 只 wrap 了官方 Open API 的一部分；其余接口可直接用 `lark_api.py <METHOD> '<path>'` 调。找不到 tool 时去 [open.feishu.cn/document](https://open.feishu.cn/document) 搜一下 API 路径。

## 直调 API 速查（写入）

以下操作通过 `python3 lark_api.py` 执行。脚本自动从 `.env` 加载凭证并获取 token。

### 创建文档

```bash
python3 lark_api.py POST '/open-apis/docx/v1/documents' '{"title":"文档标题"}'
```

返回 `data.document.document_id`，后续操作都用这个 ID。

### 写入内容块

```bash
python3 lark_api.py POST '/open-apis/docx/v1/documents/<document_id>/blocks/<block_id>/children' '<JSON>'
```

`block_id` 使用 `document_id`（即文档根块）将内容追加到文档顶层。`index` 控制插入位置（0 = 文档开头）。

请求体格式：

```json
{
  "children": [
    {
      "block_type": 3,
      "heading1": { "elements": [{ "text_run": { "content": "一级标题" } }] }
    },
    {
      "block_type": 2,
      "text": { "elements": [{ "text_run": { "content": "正文内容" } }] }
    },
    {
      "block_type": 17,
      "todo": {
        "elements": [{ "text_run": { "content": "待办事项" } }],
        "style": { "done": false }
      }
    }
  ],
  "index": 0
}
```

**块类型（block_type）常用值**：

| block_type | 字段名 | 说明 |
|------------|--------|------|
| 2 | `text` | 文本块 |
| 3 | `heading1` | 一级标题 |
| 4 | `heading2` | 二级标题 |
| 5 | `heading3` | 三级标题 |
| 12 | `bullet` | 无序列表 |
| 13 | `ordered` | 有序列表 |
| 14 | `code` | 代码块 |
| 15 | `quote` | 引用 |
| 17 | `todo` | 待办事项（`style.done` 标记完成状态） |
| 27 | `image` | 图片（见下方「插入图片 / 用 mermaid 画流程图」） |
| 31 | `table` | 表格（需配合 `table_cell` 使用，见下文） |
| 32 | `table_cell` | 表格单元格（不能单独创建，由 table 自动生成） |

> **`block_type: 21`（diagram）/ 画板 / 思维导图**：Feishu Open API **不允许通过接口创建**（返回 `1770029 block not support to create`）。需要图表请走「插入图片」的方案——把 mermaid / graphviz 渲染成 PNG 再上传为 image 块。

所有富文本块结构相同：`{ "elements": [{ "text_run": { "content": "文本" } }] }`。可通过 `text_run.text_element_style` 添加加粗（`bold`）、斜体（`italic`）等样式。

### 创建表格

表格需要两步：先创建表格骨架，再往每个单元格里写内容。

**第一步：创建表格骨架**

```bash
python3 lark_api.py POST '/open-apis/docx/v1/documents/<document_id>/blocks/<document_id>/children' '{
  "children": [{
    "block_type": 31,
    "table": {
      "property": {
        "row_size": 3,
        "column_size": 2,
        "column_width": [240, 360],
        "header_row": true
      }
    }
  }],
  "index": 0
}'
```

返回值中 `data.children[0].table.cells` 是一个按 **行优先** 顺序排列的 cell_id 数组，长度 = `row_size × column_size`。例如 3 行 2 列的表格，cell 顺序是：[行1列1, 行1列2, 行2列1, 行2列2, 行3列1, 行3列2]。

**第二步：向每个 cell 写文本**

```bash
python3 lark_api.py POST '/open-apis/docx/v1/documents/<document_id>/blocks/<cell_id>/children' '{
  "children": [{
    "block_type": 2,
    "text": {"elements": [{"text_run": {"content": "单元格内容"}}]}
  }],
  "index": 0
}'
```

每个 cell 必须单独调用一次 children 接口（不能批量）。cell 内可以放 text / bullet / heading 等任意块。

**property 可选字段**：
- `header_row: true` — 首行作为表头
- `header_column: true` — 首列作为表头
- `column_width` — 各列宽度数组（单位：像素），长度必须等于 column_size
- `merge_info` — 单元格合并信息（默认每个 cell 都是 1×1）

> **表格 cell 总数上限 ~50**：实测 24×4=96 会报 `1770001 invalid param`；7×3=21、5×4=20、6×3=18 均 OK。超限时请拆成多个小表，或改回 bullet 列表。

### 插入图片 / 用 mermaid 画流程图

Feishu 原生 diagram 块（`block_type: 21`）不能通过 API 创建；需要画流程图、架构图请走「图片」路线：本地用 [`@mermaid-js/mermaid-cli`](https://github.com/mermaid-js/mermaid-cli)（命令名 `mmdc`）把 mermaid 源码渲染为 PNG，再通过三步流程上传：

**第一步：创建空 image 块**

```bash
python3 lark_api.py POST '/open-apis/docx/v1/documents/<document_id>/blocks/<document_id>/children' \
  '{"children":[{"block_type":27,"image":{}}],"index":0}'
```

记下返回里的 `block_id`——上传素材时要用。

**第二步：上传 PNG 为素材（multipart/form-data）**

`lark_api.py` 不支持 multipart 上传，直接用 Python 或 curl。表单字段：`file_name`, `parent_type=docx_image`, `parent_node=<image_block_id>`, `size`, `file`（二进制）。

```python
import os, urllib.request
boundary = "----MB" + os.urandom(8).hex()
def f(name, value):
    return f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
data = open("chart.png", "rb").read()
body = f("file_name","chart.png") + f("parent_type","docx_image") + \
       f("parent_node", IMAGE_BLOCK_ID) + f("size", str(len(data))) + \
       f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="chart.png"\r\nContent-Type: image/png\r\n\r\n'.encode() + \
       data + f'\r\n--{boundary}--\r\n'.encode()
req = urllib.request.Request(
    "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all",
    data=body, method="POST",
    headers={"Authorization": f"Bearer {TOKEN}",
             "Content-Type": f"multipart/form-data; boundary={boundary}"})
resp = urllib.request.urlopen(req).read()  # data.file_token
```

**第三步：用 token 绑定到 image 块**

```bash
python3 lark_api.py PATCH '/open-apis/docx/v1/documents/<document_id>/blocks/<image_block_id>' \
  '{"replace_image":{"token":"<file_token>"}}'
```

> **mermaid 渲染经验**：用 `mmdc -i flow.mmd -o flow.png -b white -s 2` 输出 2× 高清 PNG；中文需系统装字体；节点里换行用 `<br/>`（不要 `\n`）；PDF/SVG 输出用 `-o foo.svg` 但 Feishu image 块只接受光栅格式（PNG/JPEG）。
>
> `upload_all` 上限 20 MB；超限改走 `upload_prepare` → `upload_part` → `upload_finish` 分片流程。
>
> **不要指望 code 块渲染 mermaid**：`block_type: 14` 带 `language` 值都只显示源码文本，不会渲染图。

### 更新单个块

```bash
python3 lark_api.py PATCH '/open-apis/docx/v1/documents/<document_id>/blocks/<block_id>' '<JSON>'
```

### 删除子块

```bash
python3 lark_api.py DELETE '/open-apis/docx/v1/documents/<document_id>/blocks/<block_id>/children/batch_delete' \
  '{"start_index":0,"end_index":2}'
```

### 添加全文评论

```bash
python3 lark_api.py POST '/open-apis/drive/v1/files/<file_token>/comments?file_type=docx' \
  '{"reply_list":{"replies":[{"content":{"elements":[{"type":"text_run","text_run":{"text":"评论内容"}}]}}]}}'
```

> **评论限制**：只能创建全文评论，无法创建局部评论。但读取时可以读到所有评论（含局部评论）。用户可能通过划词局部评论与你交互，读取时 `quote` 字段会包含被评论的原文。

### 回复评论

```bash
python3 lark_api.py POST '/open-apis/drive/v1/files/<file_token>/comments/<comment_id>/replies?file_type=docx' \
  '{"content":{"elements":[{"type":"text_run","text_run":{"text":"回复内容"}}]}}'
```

`comment_id` 从 MCP `drive_v1_fileComment_list` 或直调 `GET /open-apis/drive/v1/files/<file_token>/comments?file_type=docx` 获取。

### 转移文档所有者

```bash
python3 lark_api.py POST '/open-apis/drive/v1/permissions/<document_id>/members/transfer_owner?type=docx&remove_old_owner=false&old_owner_perm=full_access' \
  '{"member_type":"openid","member_id":"ou_3839de508ed93574a1e27eb556dcf68d"}'
```

### 添加协作者

```bash
python3 lark_api.py POST '/open-apis/drive/v1/permissions/<document_id>/members?type=docx&need_notification=true' \
  '{"member_type":"openid","member_id":"<open_id>","perm":"full_access"}'
```

`perm` 可选值：`view`（可阅读）、`edit`（可编辑）、`full_access`（可管理）。

### 发送飞书消息

```bash
python3 lark_api.py POST '/open-apis/im/v1/messages?receive_id_type=open_id' \
  '{"receive_id":"ou_3839de508ed93574a1e27eb556dcf68d","msg_type":"text","content":"{\"text\":\"消息内容\"}"}'
```

> `content` 字段是 JSON 字符串，需要双重序列化。

## 核心操作指南

### 从飞书链接提取 token

飞书链接有两种常见格式：

| 格式 | URL 示例 | token 位置 |
|------|----------|------------|
| 普通文档 | `https://xxx.feishu.cn/docx/XXXXXXXXXX` | `/docx/` 之后的部分 |
| 知识库文档 | `https://xxx.feishu.cn/wiki/XXXXXXXXXX` | `/wiki/` 之后的部分 |

### 处理知识库（wiki）文档 — 重要

知识库文档的 wiki token 与底层 docx token **不同**。操作知识库文档时必须先转换：

1. **获取节点信息**：调用 MCP 工具 `wiki_v2_space_getNode` 传入 wiki token：
   ```json
   { "params": { "token": "<wiki_token>" } }
   ```
2. **提取 obj_token**：返回值中 `node.obj_token` 是实际的 docx document_id，`node.obj_type` 是文档类型（通常为 `"docx"`）
3. **后续操作使用对应 token**：
   - MCP 读取（`docs_v1_content_get`、`docx_v1_documentBlock_list`）：可以直接用 **wiki token**
   - API 写入（创建子块、更新块等）：必须用 **obj_token**
   - API 添加评论：使用 **obj_token** 作为 `file_token`

### 权限：应用对用户文档的访问

应用身份对**应用自己创建的文档**拥有完全控制权。但对于**用户拥有的文档**（包括知识库文档），权限取决于文档的共享设置：

| 操作 | 权限要求 |
|------|----------|
| 读取文档内容 | 文档对应用可见即可（通常默认可读） |
| 添加评论 | 文档对应用可见即可 |
| 编辑文档块 | 需要文档所有者将 Claude 应用添加为**可编辑**或**可管理**协作者 |
| 管理权限 | 需要文档所有者将 Claude 应用添加为**可管理**协作者 |

如果编辑操作返回 `forBidden`（错误码 1770032）或权限操作返回 `Permission denied`（错误码 1063002），说明应用没有足够权限，需要通知用户在飞书文档设置中给 Claude 应用添加编辑权限。

### 操作路径 1：读取云文档 TODO 并执行

1. **提取 token**：从用户发来的飞书链接中提取 token
   - wiki 链接：先用 MCP `wiki_v2_space_getNode` 获取 `obj_token`
   - docx 链接：直接使用 URL 中的 token
2. **读取文档内容**：用 MCP `docs_v1_content_get` 获取 Markdown 内容
3. **读取全文评论**：用 MCP `drive_v1_fileComment_list` 获取所有评论
4. **执行任务**：逐项完成 TODO
5. **创建任务报告文档**：
   ```bash
   python3 lark_api.py POST '/open-apis/docx/v1/documents' '{"title":"任务执行报告：<原文档标题>"}'
   ```
6. **写入报告内容**：
   ```bash
   python3 lark_api.py POST '/open-apis/docx/v1/documents/<report_doc_id>/blocks/<report_doc_id>/children' '{
     "children": [
       {"block_type": 2, "text": {"elements": [{"text_run": {"content": "原文档：<链接>"}}]}},
       {"block_type": 3, "heading1": {"elements": [{"text_run": {"content": "已完成"}}]}},
       {"block_type": 17, "todo": {"elements": [{"text_run": {"content": "任务描述 —— 完成说明"}}], "style": {"done": true}}},
       {"block_type": 3, "heading1": {"elements": [{"text_run": {"content": "需要你补充"}}]}},
       {"block_type": 17, "todo": {"elements": [{"text_run": {"content": "待确认任务 —— 需要补充什么"}}], "style": {"done": false}}}
     ],
     "index": 0
   }'
   ```
7. **转移所有权**：
   ```bash
   python3 lark_api.py POST '/open-apis/drive/v1/permissions/<report_doc_id>/members/transfer_owner?type=docx&remove_old_owner=false&old_owner_perm=full_access' \
     '{"member_type":"openid","member_id":"ou_3839de508ed93574a1e27eb556dcf68d"}'
   ```
8. **发送消息**：
   ```bash
   python3 lark_api.py POST '/open-apis/im/v1/messages?receive_id_type=open_id' \
     '{"receive_id":"ou_3839de508ed93574a1e27eb556dcf68d","msg_type":"text","content":"{\"text\":\"任务已处理完毕，请查看报告：https://gcnitdycxk0z.feishu.cn/docx/<report_doc_id>\\n\\n已完成 X 项，待补充 Y 项。\"}"}'
   ```

> **后续交互**：Canass 可以直接在报告文档中评论来回复你的问题。你下次读取时，用 MCP `drive_v1_fileComment_list` 读取报告文档的评论即可获取反馈。

### 操作路径 2：调研后创建飞书文档

1. **执行调研**：完成用户交办的调研任务
2. **创建文档**：
   ```bash
   python3 lark_api.py POST '/open-apis/docx/v1/documents' '{"title":"调研报告：<主题>"}'
   ```
   返回 `data.document.document_id`
3. **写入内容**：
   ```bash
   python3 lark_api.py POST '/open-apis/docx/v1/documents/<document_id>/blocks/<document_id>/children' '{
     "children": [
       {"block_type": 3, "heading1": {"elements": [{"text_run": {"content": "章节标题"}}]}},
       {"block_type": 2, "text": {"elements": [{"text_run": {"content": "正文内容..."}}]}}
     ],
     "index": 0
   }'
   ```
4. **转移所有权**：
   ```bash
   python3 lark_api.py POST '/open-apis/drive/v1/permissions/<document_id>/members/transfer_owner?type=docx&remove_old_owner=false&old_owner_perm=full_access' \
     '{"member_type":"openid","member_id":"ou_3839de508ed93574a1e27eb556dcf68d"}'
   ```
5. **发送消息**：通知 Canass 文档已创建，附上文档链接

## 注意事项

- MCP 工具调用中 **不要设置 `useUAT: true`**，默认使用应用身份
- 应用创建的文档默认在应用的云空间中，转移所有权后文档会移动到目标用户的空间
- `lark_api.py` 的路径以本仓库位置为准，在其他仓库中使用时需要用绝对路径
- 发送消息时 `content` 字段是 JSON 字符串，需要双重序列化：`"{\"text\":\"消息内容\"}"`
