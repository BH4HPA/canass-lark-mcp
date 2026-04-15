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
      "command": "bash",
      "args": ["/path/to/canass-lark-mcp/start.sh"]
    }
  }
}
```

MCP 仅加载**只读工具**（7 个，schema 约 10K 字符）。**写入操作**（创建文档、编辑、发消息等）通过 `lark_api.py` 直接调用飞书 Open API，不走 MCP，避免大体积 schema 占用 context。

| 工具 | 说明 |
|------|------|
| `docs.v1.content.get` | 获取文档 Markdown 内容 |
| `docx.v1.documentBlock.list` | 获取文档所有块 |
| `drive.v1.fileComment.get` | 获取单条评论 |
| `drive.v1.fileComment.list` | 获取文档所有评论 |
| `drive.v1.fileCommentReply.list` | 获取评论的回复列表 |
| `drive.v1.permissionMember.list` | 获取协作者列表 |
| `wiki.v2.space.getNode` | 获取知识库节点（wiki token → obj_token） |

凭证在本仓库的 `.env` 文件中配置（已在 `.gitignore` 中忽略）。

#### 第 2 步：添加 AGENTS.md

将本仓库的 `AGENTS.md` 复制到目标仓库根目录，或在目标仓库的 `AGENTS.md` / `CLAUDE.md` 中引用：

```markdown
## 飞书 MCP

本项目已接入飞书 MCP 服务，详见 [canass-lark-mcp/AGENTS.md](/path/to/canass-lark-mcp/AGENTS.md)。
```

也可以直接将 `AGENTS.md` 中的内容粘贴到目标仓库的 `CLAUDE.md` 中。

> **注意**：`AGENTS.md` 中的 `lark_api.py` 路径需要替换为本仓库的绝对路径（如 `/Users/xxx/canass-lark-mcp/lark_api.py`），否则在其他仓库中无法找到脚本。

#### 第 3 步：验证 MCP 服务

在目标仓库中启动 Claude Code，MCP 服务会自动加载。可以用以下方式验证：

1. 进入 Claude Code 后，检查是否出现 `lark` MCP 服务器的工具列表
2. 尝试让 Claude 用 `lark_api.py` 给 Canass 发送一条测试消息

## 文件说明

| 文件 | 说明 |
|------|------|
| `mcp-config.json` | MCP 服务器配置模板，可直接复制到 `.mcp.json` |
| `start.sh` | MCP 服务器启动脚本（只读工具，从 `.env` 读取凭证） |
| `lark_api.py` | 飞书 API 直调脚本（写入操作，零 context 占用） |
| `.env` | 应用凭证（不提交到 git） |
| `.env.example` | 环境变量模板 |
| `permissions.json` | 飞书应用已开通的权限列表 |
| `AGENTS.md` | Agent 使用指南（含 MCP 工具和直调 API 用法） |

## 飞书应用信息

- **应用名称**：Claude
- **APP ID**：`cli_a954426ca83b1cb6`
- **可用范围**：全员
- **鉴权模式**：tenant_access_token（应用身份）

## 权限概览

应用已开通以下类别的权限（详见 `permissions.json`）：

- **云文档**：读取/写入文档内容、管理评论
- **权限管理**：添加/移除协作者、转移所有权
