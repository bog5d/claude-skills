#!/usr/bin/env python3
"""
千问 VL 直接 API 调用脚本（绕过 Hermes auxiliary vision 路由）
用途：当 vision_analyze_tool 因 config merge 或 provider routing 失败时的降级方案

用法：
    cd /Users/mac/.hermes/hermes-agent
    HERMES_HOME=/Users/mac/.hermes/profiles/finance/home \
      ./venv/bin/python3 references/qwen-vl-direct-call.py <image_path> [prompt]

依赖：hermes-agent venv（httpx 已安装）
"""

import sys
import json
import base64
import asyncio
from pathlib import Path

import httpx

# ── 配置 ──
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "qwen-vl-max"

def load_api_key() -> str:
    """从 Hermes profile config 读取 DashScope API key"""
    sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "hermes-agent"))
    from hermes_cli.config import load_config
    cfg = load_config()
    
    # 优先从 auxiliary.vision 读
    v = cfg.get("auxiliary", {}).get("vision", {})
    key = v.get("api_key", "")
    if key:
        return key
    
    # 降级：从 providers.dashscope 读
    p = cfg.get("providers", {}).get("dashscope", {})
    if isinstance(p, str):
        p = json.loads(p)
    return p.get("api_key", "")


async def call_qwen_vl(image_path: str, prompt: str, timeout: int = 60) -> dict:
    """调用千问 VL API 描述图片"""
    api_key = load_api_key()
    if not api_key:
        return {"success": False, "error": "API key not configured", "analysis": ""}
    
    # 读图 + base64
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{img_b64}"
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }],
                "max_tokens": 2000,
                "temperature": 0.1,
            },
        )
        result = resp.json()
        
        if "choices" in result:
            return {
                "success": True,
                "analysis": result["choices"][0]["message"]["content"],
                "usage": result.get("usage", {}),
            }
        else:
            return {
                "success": False,
                "error": result.get("error", {}).get("message", "Unknown error"),
                "analysis": "",
            }


async def main():
    if len(sys.argv) < 2:
        print("用法: python3 qwen-vl-direct-call.py <image_path> [prompt]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else "详细描述这张截图中的所有文字、数字、金额。"
    
    result = await call_qwen_vl(image_path, prompt)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
