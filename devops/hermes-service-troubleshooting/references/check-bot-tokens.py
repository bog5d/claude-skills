import subprocess, json

"""
Check which Telegram bot each Hermes profile's .env points to.
Useful for diagnosing polling conflicts when multiple gateways
share the same TELEGRAM_BOT_TOKEN.
"""

tokens = {}
for label, path in [
    ('global', '/Users/mac/.hermes/.env'),
    ('english-tutor', '/Users/mac/.hermes/profiles/english-tutor/.env'),
    ('her-m2', '/Users/mac/.hermes/profiles/her-m2/.env'),
]:
    try:
        with open(path) as f:
            for line in f:
                if line.startswith('TELEGRAM_BOT_TOKEN=***                    tokens[label] = line.strip().split('=', 1)[1]
                    break
    except FileNotFoundError:
        pass

for label, token in tokens.items():
    url = f'https://api.telegram.org/bot{token}/getMe'
    r = subprocess.run(['curl', '-s', '--max-time', '5', url], capture_output=True, text=True)
    try:
        data = json.loads(r.stdout)
        username = data.get('result', {}).get('username', 'N/A')
        print(f'{label:16s} → @{username}')
    except:
        print(f'{label:16s} → PARSE_ERROR (token may be invalid)')
