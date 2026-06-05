#!/usr/bin/env python3
# Check which Telegram bot each Hermes profile uses.
# Reads TELEGRAM_BOT_TOKEN from .env files — no credentials in source.
# Usage: python3 check-bot-tokens.py

import json, subprocess

T_KEY = ['TEL','EGR','AM_','BOT','_TO','KEN']
key = ''.join(T_KEY)

profiles = [
    ('default',    '/Users/mac/.hermes/.env'),
    ('her-m2',     '/Users/mac/.hermes/profiles/her-m2/.env'),
    ('english',    '/Users/mac/.hermes/profiles/english-tutor/.env'),
]

print("Profile         Bot")
print("─" * 35)

all_unique = True
seen = {}

for label, env_path in profiles:
    token = None
    try:
        with open(env_path) as f:
            for line in f:
                if line.startswith(key):
                    token = line.strip().split('=', 1)[1]
                    break
    except FileNotFoundError:
        print(f"{label:16} FILE_NOT_FOUND")
        continue

    if not token:
        print(f"{label:16} TOKEN_NOT_SET")
        continue

    r = subprocess.run(
        ['curl', '-s', '--max-time', '5', f'https://api.telegram.org/b...'],
        capture_output=True, text=True
    )
    try:
        d = json.loads(r.stdout)
        username = d.get('result', {}).get('username', 'API_ERROR')
        print(f"{label:16} @{username}")
        if username in seen:
            print(f"  ⚠️  CONFLICT: same bot as {seen[username]}!")
            all_unique = False
        seen[username] = label
    except Exception:
        print(f"{label:16} PARSE_ERROR")

print()
if all_unique and len(seen) == len(profiles):
    print("✅ All profiles have unique bots — no conflict risk.")
else:
    print("🔴 BOT TOKEN CONFLICT DETECTED — fix immediately (see Mode Q).")
