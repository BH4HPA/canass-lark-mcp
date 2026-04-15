# 飞书 MCP 使用指南

你可以通过飞书 MCP 工具以**应用身份**（Claude）操作飞书云文档和消息。所有 API 调用使用 `tenant_access_token`，无需用户登录。

## 团队成员

| 成员 | open_id | 角色 |
|------|---------|------|
| Canass | `ou_3839de508ed93574a1e27eb556dcf68d` | 文档接收人，消息接收人 |
| Ray | `ou_27485e1ea4427c88d5e7d1f0108f1f2d` | 开发者 |

默认消息发送给 **Canass**。

## 可用工具速查

### 知识库

- `wiki_v2_space_getNode` — 获取知识库节点信息（将 wiki token 转换为实际 docx obj_token）

### 云文档读取

- `docs_v1_content_get` — 获取云文档 **Markdown** 格式内容（推荐用于理解文档内容，支持 wiki 文档）
- `docx_v1_document_rawContent` — 获取文档纯文本内容（无格式信息）
- `docx_v1_documentBlock_list` — 获取文档所有块（含结构化信息，编辑文档时需要）
- `docx_v1_documentBlock_get` — 获取指定块内容

> **读取策略**：想要理解文档内容时，优先使用 `docs_v1_content_get`，它返回 Markdown 格式，保留标题层级、列表、待办等结构，比纯文本更易解析。需要编辑文档块时，再配合 `docx_v1_documentBlock_list` 获取块 ID。

### 云文档编辑

- `docx_v1_document_create` — 创建新文档
- `docx_v1_documentBlockChildren_create` — 在指定块下创建子块
- `docx_v1_documentBlock_patch` — 更新指定块内容
- `docx_v1_documentBlock_batchUpdate` — 批量更新块内容
- `docx_v1_documentBlockChildren_batchDelete` — 删除指定范围的子块
- `docx_builtin_import` — 导入文档

### 云文档评论

- `drive_v1_fileComment_create` — 添加全文评论（不支持局部评论）
- `drive_v1_fileComment_list` — 获取文档所有评论（支持读取全文评论和局部评论）
- `drive_v1_fileComment_get` — 获取单条评论详情
- `drive_v1_fileComment_patch` — 解决/恢复评论
- `drive_v1_fileCommentReply_list` — 获取评论的回复列表
- `drive_v1_fileCommentReply_update` — 更新回复内容

> **评论限制**：只能创建全文评论，无法创建局部评论（对特定文字评论）。但读取时可以读到所有评论（含局部评论）。用户可能在文档中添加局部评论来与你交互。

### 权限管理

- `drive_v1_permissionMember_create` — 添加协作者
- `drive_v1_permissionMember_list` — 获取协作者列表
- `drive_v1_permissionMember_update` — 更新协作者权限
- `drive_v1_permissionMember_transferOwner` — 转移文档所有者

### 消息

- `im_v1_message_create` — 发送飞书消息

### 通讯录

- `contact_v3_user_batchGetId` — 通过手机号或邮箱获取用户 ID

## 核心操作指南

### 从飞书链接提取 token

飞书链接有两种常见格式：

| 格式 | URL 示例 | token 位置 |
|------|----------|------------|
| 普通文档 | `https://xxx.feishu.cn/docx/XXXXXXXXXX` | `/docx/` 之后的部分 |
| 知识库文档 | `https://xxx.feishu.cn/wiki/XXXXXXXXXX` | `/wiki/` 之后的部分 |

### 处理知识库（wiki）文档 — 重要

知识库文档的 wiki token 与底层 docx token **不同**。操作知识库文档时必须先转换：

1. **获取节点信息**：调用 `wiki_v2_space_getNode` 传入 wiki token：
   ```json
   { "params": { "token": "<wiki_token>" } }
   ```
2. **提取 obj_token**：返回值中 `node.obj_token` 是实际的 docx document_id，`node.obj_type` 是文档类型（通常为 `"docx"`）
3. **后续操作使用对应 token**：
   - 读取内容（`rawContent`、`documentBlock_list`）：可以直接用 **wiki token** 作为 `document_id`
   - 编辑文档块（`documentBlockChildren_create`、`documentBlock_patch` 等）：必须用 **obj_token**
   - 添加评论（`fileComment_create`）：使用 **obj_token** 作为 `file_token`，`file_type` 设为 `"docx"`

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
   - wiki 链接：先调用 `wiki_v2_space_getNode` 获取 `obj_token`
   - docx 链接：直接使用 URL 中的 token
2. **读取文档内容**：调用 `docs_v1_content_get` 获取 Markdown 格式内容，理解文档结构和 TODO 列表
3. **读取全文评论**：调用 `drive_v1_fileComment_list` 获取所有评论（用户可能通过评论给你补充了信息）
4. **执行任务**：逐项完成 TODO
5. **创建任务报告文档**：调用 `docx_v1_document_create` 创建新文档，标题如「任务执行报告：<原文档标题>」
6. **写入报告内容**：调用 `docx_v1_documentBlockChildren_create` 写入以下结构：
   - 原文档链接（方便 Canass 跳转回原文档）
   - **已完成的任务**：用 `block_type: 17`（待办事项，`done: true`）列出每个已完成任务及完成说明
   - **需要补充的信息**：用 `block_type: 17`（待办事项，`done: false`）列出每个待确认任务，说明需要用户补充什么
   ```json
   {
     "path": { "document_id": "<report_doc_id>", "block_id": "<report_doc_id>" },
     "data": {
       "children": [
         {
           "block_type": 2,
           "text": { "elements": [{ "text_run": { "content": "原文档：<链接>" } }] }
         },
         {
           "block_type": 3,
           "heading1": { "elements": [{ "text_run": { "content": "已完成" } }] }
         },
         {
           "block_type": 17,
           "todo": { "elements": [{ "text_run": { "content": "评估项、优化项默认全选中 —— 已在 xxx 文件中修改" } }], "style": { "done": true } }
         },
         {
           "block_type": 3,
           "heading1": { "elements": [{ "text_run": { "content": "需要你补充" } }] }
         },
         {
           "block_type": 17,
           "todo": { "elements": [{ "text_run": { "content": "模型是否要开始接入？—— 请明确接入的模型类型和预期时间节点" } }], "style": { "done": false } }
         }
       ],
       "index": 0
     }
   }
   ```
7. **转移所有权**：调用 `drive_v1_permissionMember_transferOwner` 将报告文档转移给 Canass
8. **发送消息**：调用 `im_v1_message_create` 通知 Canass，附上报告文档链接：
   ```json
   {
     "params": { "receive_id_type": "open_id" },
     "data": {
       "receive_id": "ou_3839de508ed93574a1e27eb556dcf68d",
       "msg_type": "text",
       "content": "{\"text\":\"任务已处理完毕，请查看报告：https://gcnitdycxk0z.feishu.cn/docx/<report_doc_id>\\n\\n已完成 X 项，待补充 Y 项。如有问题请直接在报告文档中评论。\"}"
     }
   }
   ```

> **后续交互**：Canass 可以直接在报告文档中评论来回复你的问题。你下次读取时，调用 `drive_v1_fileComment_list` 读取报告文档的评论即可获取 Canass 的反馈。

### 操作路径 2：调研后创建飞书文档

1. **执行调研**：完成用户交办的调研任务
2. **创建文档**：调用 `docx_v1_document_create` 创建新文档：
   ```json
   {
     "data": { "title": "调研报告：<主题>" }
   }
   ```
   返回值中包含 `document_id`（即 document_token）
3. **写入内容**：调用 `docx_v1_documentBlockChildren_create` 向文档中添加内容块。`block_id` 参数使用 `document_id`（文档根块）：
   ```json
   {
     "path": { "document_id": "<document_id>", "block_id": "<document_id>" },
     "data": {
       "children": [
         {
           "block_type": 3,
           "heading1": {
             "elements": [{ "text_run": { "content": "章节标题" } }]
           }
         },
         {
           "block_type": 2,
           "text": {
             "elements": [{ "text_run": { "content": "正文内容..." } }]
           }
         }
       ],
       "index": 0
     }
   }
   ```
4. **转移所有权**：调用 `drive_v1_permissionMember_transferOwner` 将文档转移给 Canass：
   ```json
   {
     "path": { "token": "<document_token>" },
     "params": {
       "type": "docx",
       "remove_old_owner": false,
       "old_owner_perm": "full_access"
     },
     "data": {
       "member_type": "openid",
       "member_id": "ou_3839de508ed93574a1e27eb556dcf68d"
     }
   }
   ```
5. **发送消息**：通知 Canass 文档已创建，附上文档链接

## 注意事项

- 所有工具调用中 **不要设置 `useUAT: true`**，默认使用应用身份（tenant_access_token）
- 应用创建的文档默认在应用的云空间中，转移所有权后文档会移动到目标用户的空间
- 添加评论时 `file_type` 参数对于新版文档使用 `"docx"`
- 发送消息时 `content` 字段是 JSON 字符串，需要序列化。文本消息格式：`"{\"text\":\"消息内容\"}"`
- 文档块类型（block_type）常用值：1=页面块(page), 2=文本块(text), 3=标题1(heading1), 4=标题2, 5=标题3, 12=有序列表, 13=无序列表, 14=代码块, 15=引用, 17=待办事项(todo), 23=表格
- 待办事项块(block_type=17)的 `done` 字段标记完成状态
