#!/usr/bin/env python3
"""复现史官 capture.py 的哈希算法，为手工补录生成 hash（不写仓库文件）。

用法:
    python3 hash_only.py /tmp/turns-YYYYMMDD.json
输出: 每条 SEQ/TS/KIND/AGENT/CHANNEL + HASH，末尾 CHAIN_HEAD + ENTRIES。
要求输入 JSON 数组: [{"kind","agent","channel","at","user","ai"}, ...]
"""
import json
import hashlib
import sys


def entry_hash(prev, seq, ts, agent, channel, kind, user_text, ai_text, reply_to=""):
    payload = "\n".join([prev, str(seq), ts, agent, channel, kind, user_text, ai_text, reply_to])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/turns.json"
    items = json.load(open(path, encoding="utf-8"))
    prev = "GENESIS"
    for i, item in enumerate(items, 1):
        ts = item["at"]
        kind = item["kind"]
        user_text = item["user"]
        ai_text = item.get("ai", "")
        agent = item.get("agent", "hermes")
        channel = item.get("channel", "telegram")
        h = entry_hash(prev, i, ts, agent, channel, kind, user_text, ai_text, "")
        print(f"SEQ={i} TS={ts} KIND={kind} AGENT={agent} CHANNEL={channel}")
        print(f"HASH={h}")
        prev = h
    print(f"CHAIN_HEAD={prev}")
    print(f"ENTRIES={len(items)}")


if __name__ == "__main__":
    main()
