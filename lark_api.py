#!/usr/bin/env python3
"""飞书 Open API 轻量调用脚本，替代 MCP 方案以节省 context 空间。

用法:
    python3 lark_api.py <method> <path> [json_body]

示例:
    # 创建文档
    python3 lark_api.py POST '/open-apis/docx/v1/documents' '{"title":"测试文档"}'

    # 写入内容块
    python3 lark_api.py POST '/open-apis/docx/v1/documents/<doc_id>/blocks/<doc_id>/children' \\
        '{"children":[{"block_type":2,"text":{"elements":[{"text_run":{"content":"正文"}}]}}],"index":0}'

    # 发送消息
    python3 lark_api.py POST '/open-apis/im/v1/messages?receive_id_type=open_id' \\
        '{"receive_id":"ou_xxx","msg_type":"text","content":"{\\\"text\\\":\\\"hello\\\"}"}'

    # 读取评论
    python3 lark_api.py GET '/open-apis/drive/v1/files/<doc_id>/comments?file_type=docx'

环境变量 LARK_APP_ID 和 LARK_APP_SECRET 从 .env 文件自动加载。
"""

import json
import os
import sys
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOMAIN = "https://open.feishu.cn"


def load_env():
    env_path = os.path.join(SCRIPT_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def get_tenant_token():
    app_id = os.environ.get("LARK_APP_ID")
    app_secret = os.environ.get("LARK_APP_SECRET")
    if not app_id or not app_secret:
        print("错误: 需要 LARK_APP_ID 和 LARK_APP_SECRET", file=sys.stderr)
        sys.exit(1)
    req = urllib.request.Request(
        f"{DOMAIN}/open-apis/auth/v3/tenant_access_token/internal",
        data=json.dumps({"app_id": app_id, "app_secret": app_secret}).encode(),
        headers={"Content-Type": "application/json"},
    )
    resp = json.loads(urllib.request.urlopen(req).read())
    if resp.get("code") != 0:
        print(f"获取 token 失败: {resp}", file=sys.stderr)
        sys.exit(1)
    return resp["tenant_access_token"]


def call_api(method, path, body=None):
    token = get_tenant_token()
    url = f"{DOMAIN}{path}" if path.startswith("/") else f"{DOMAIN}/{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method.upper(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        resp = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        result = json.loads(e.read())
        print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)
    result = json.loads(resp.read())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main():
    load_env()
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    method = sys.argv[1]
    path = sys.argv[2]
    body = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
    call_api(method, path, body)


if __name__ == "__main__":
    main()
