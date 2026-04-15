# Canass 飞书 MCP 服务

为 Claude Code 提供飞书云文档操作能力的 MCP 服务配置。以飞书应用「Claude」的身份运行，可读写云文档、添加评论、发送消息。

## 快速开始

### 前置条件

- Node.js >= 18
- npm 或 npx

### 在其他仓库中接入此 MCP 服务

#### 第 1 步：添加 MCP 服务器配置

在目标仓库根目录创建或编辑 `.mcp.json`：

```json
{
  "mcpServers": {
    "lark": {
      "command": "npx",
      "args": [
        "-y",
        "@larksuiteoapi/lark-mcp",
        "mcp",
        "-a", "<YOUR_APP_ID>",
        "-s", "<YOUR_APP_SECRET>",
        "--token-mode", "tenant_access_token",
        "-l", "zh",
        "-t", "docs.v1.content.get,docx.v1.document.rawContent,docx.v1.document.create,docx.v1.documentBlock.list,docx.v1.documentBlock.get,docx.v1.documentBlock.patch,docx.v1.documentBlock.batchUpdate,docx.v1.documentBlockChildren.create,docx.v1.documentBlockChildren.batchDelete,docx.builtin.import,drive.v1.fileComment.create,drive.v1.fileComment.get,drive.v1.fileComment.list,drive.v1.fileComment.patch,drive.v1.fileCommentReply.list,drive.v1.fileCommentReply.update,drive.v1.permissionMember.create,drive.v1.permissionMember.list,drive.v1.permissionMember.update,drive.v1.permissionMember.transferOwner,im.v1.message.create,contact.v3.user.batchGetId,wiki.v2.space.getNode"
      ]
    }
  }
}
```

> **安全提示**：`.mcp.json` 包含应用凭证，若仓库为公开仓库，应将其加入 `.gitignore`，或改为使用环境变量方案（见下文）。

#### 使用环境变量方案（推荐用于公开仓库）

在 `.mcp.json` 中使用 shell 脚本启动：

```json
{
  "mcpServers": {
    "lark": {
      "command": "bash",
      "args": ["/path/to/canass-lark-mcp/start.sh"]
    }
  }
}
```

然后在本仓库的 `.env` 文件中配置凭证（已在 `.gitignore` 中忽略）。

#### 第 2 步：添加 AGENTS.md

将本仓库的 `AGENTS.md` 复制到目标仓库根目录，或在目标仓库的 `AGENTS.md` / `CLAUDE.md` 中引用：

```markdown
## 飞书 MCP

本项目已接入飞书 MCP 服务，详见 [canass-lark-mcp/AGENTS.md](/path/to/canass-lark-mcp/AGENTS.md)。
```

也可以直接将 `AGENTS.md` 中的内容粘贴到目标仓库的 `CLAUDE.md` 中。

#### 第 3 步：验证 MCP 服务

在目标仓库中启动 Claude Code，MCP 服务会自动加载。可以用以下方式验证：

1. 进入 Claude Code 后，检查是否出现 `lark` MCP 服务器的工具列表
2. 尝试发一条测试消息：让 Claude 调用 `im_v1_message_create` 给 Canass 发送一条消息

## 文件说明

| 文件 | 说明 |
|------|------|
| `mcp-config.json` | MCP 服务器完整配置，可直接复制到 `.mcp.json` |
| `start.sh` | MCP 服务器启动脚本（从 `.env` 读取凭证） |
| `.env` | 应用凭证（不提交到 git） |
| `.env.example` | 环境变量模板 |
| `permissions.json` | 飞书应用已开通的权限列表 |
| `AGENTS.md` | Agent 使用指南 |

## 飞书应用信息

- **应用名称**：Claude
- **APP ID**：`cli_a954426ca83b1cb6`
- **可用范围**：全员
- **鉴权模式**：tenant_access_token（应用身份）

## 权限概览

应用已开通以下类别的权限（详见 `permissions.json`）：

- **云文档**：读取/写入文档内容、管理评论、导入/导出
- **权限管理**：添加/移除协作者、转移所有权
- **云空间**：搜索文件、管理文件位置
