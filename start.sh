#!/bin/bash
# 飞书 MCP 服务器启动脚本
# 使用应用身份（tenant_access_token）鉴权

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 从 .env 文件加载环境变量
if [ -f "$SCRIPT_DIR/.env" ]; then
  export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

if [ -z "$LARK_APP_ID" ] || [ -z "$LARK_APP_SECRET" ]; then
  echo "错误: 请设置 LARK_APP_ID 和 LARK_APP_SECRET 环境变量，或在 .env 文件中配置"
  exit 1
fi

# 启用的工具列表
TOOLS=$(cat <<'EOF'
docs.v1.content.get,
docx.v1.document.rawContent,
docx.v1.document.create,
docx.v1.documentBlock.list,
docx.v1.documentBlock.get,
docx.v1.documentBlock.patch,
docx.v1.documentBlock.batchUpdate,
docx.v1.documentBlockChildren.create,
docx.v1.documentBlockChildren.batchDelete,
docx.builtin.import,
drive.v1.fileComment.create,
drive.v1.fileComment.get,
drive.v1.fileComment.list,
drive.v1.fileComment.patch,
drive.v1.fileCommentReply.list,
drive.v1.fileCommentReply.update,
drive.v1.permissionMember.create,
drive.v1.permissionMember.list,
drive.v1.permissionMember.update,
drive.v1.permissionMember.transferOwner,
im.v1.message.create,
contact.v3.user.batchGetId,
wiki.v2.space.getNode
EOF
)
# 去掉换行和空格
TOOLS=$(echo "$TOOLS" | tr -d '\n' | tr -d ' ')

exec npx -y @larksuiteoapi/lark-mcp mcp \
  -a "$LARK_APP_ID" \
  -s "$LARK_APP_SECRET" \
  --token-mode tenant_access_token \
  -l zh \
  -t "$TOOLS"
