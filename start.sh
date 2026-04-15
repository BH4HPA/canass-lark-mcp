#!/bin/bash
# 飞书 MCP 服务器启动脚本（只读模式）
# 使用应用身份（tenant_access_token）鉴权
# 写入操作通过 lark_api.py 直调 API，不走 MCP

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

# 只读工具（7 个，~10K 字符 schema）
TOOLS=$(cat <<'EOF'
docs.v1.content.get,
docx.v1.documentBlock.list,
drive.v1.fileComment.get,
drive.v1.fileComment.list,
drive.v1.fileCommentReply.list,
drive.v1.permissionMember.list,
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
