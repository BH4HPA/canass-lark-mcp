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
| 12 | `ordered` | 有序列表 |
| 13 | `bullet` | 无序列表 |
| 14 | `code` | 代码块 |
| 15 | `quote` | 引用 |
| 17 | `todo` | 待办事项（`style.done` 标记完成状态） |

所有富文本块结构相同：`{ "elements": [{ "text_run": { "content": "文本" } }] }`。可通过 `text_run.text_element_style` 添加加粗（`bold`）、斜体（`italic`）等样式。

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
