#!/usr/bin/env python3
"""
批量补全音标 — 从 CMU 词典生成 IPA
读 GitHub words.json → 找缺音标的词 → pronouncing → ARPABET→IPA → 推送
用法: python3 scripts/generate_phonetics.py [--dry-run] [--skip-existing]
"""
import json, os, sys, subprocess, urllib.request, ssl, base64, argparse

def arpabet_to_ipa(arpabet_str):
    """ARPABET → IPA 映射"""
    if not arpabet_str:
        return ""
    mapping = {
        'AH0': 'ə', 'AA0': 'ɑː', 'AE0': 'æ', 'AH1': 'ʌ', 'AH2': 'ə',
        'AE1': 'eɪ', 'AE2': 'ɛ', 'AA1': 'ɑː', 'AA2': 'æ', 'AO0': 'ɔː',
        'AO1': 'ɔ', 'AO2': 'ɑ', 'ER0': 'ɜː', 'ER1': 'ɝ', 'ER2': 'ɚ',
        'EH0': 'ɛ', 'EH1': 'i', 'EH2': 'ɛ', 'AY0': 'aɪ', 'AY1': 'aɪ',
        'AY2': 'ɪ', 'AW0': 'aʊ', 'AW1': 'aʊ', 'AW2': 'ʌ', 'OY0': 'ɔɪ',
        'OY1': 'ɔɪ', 'OY2': 'ɒ', 'IH0': 'ɪ', 'IH1': 'ɪ', 'IH2': 'ɛ',
        'IY0': 'iː', 'IY1': 'i', 'IY2': 'ɪ', 'UH0': 'ʊ', 'UH1': 'ʊ',
        'UH2': 'ʌ', 'UW0': 'uː', 'UW1': 'u', 'UW2': 'ʊ',
        'DH': 'ð', 'TH': 'θ', 'SH': 'ʃ', 'ZH': 'ʒ', 'V': 'v',
        'Z': 'z', 'S': 's', 'N': 'ŋ', 'M': 'm', 'L': 'l',
        'R': 'r', 'W': 'w', 'Y': 'j', 'P': 'p', 'B': 'b',
        'D': 'd', 'G': 'ɡ', 'F': 'f', 'T': 't', 'K': 'k',
        'JH': 'dʒ', 'CH': 'tʃ', 'HH': 'h', 'NX': 'n̩',
    }
    phones = arpabet_str.split()
    ipa_parts = []
    for p in phones:
        ipa_parts.append(mapping.get(p, p))
    return '/' + ''.join(ipa_parts) + '/'

def main():
    parser = argparse.ArgumentParser(description='批量补全音标')
    parser.add_argument('--dry-run', action='store_true', help='只输出不推送')
    parser.add_argument('--skip-existing', action='store_true', help='跳过已有音标的词')
    args = parser.parse_args()

    # 从 git config 提取 PAT
    repo_path = '/Users/mac/bog-vocab-tracker'
    url = subprocess.check_output(['git', '-C', repo_path, 'config', '--get', 'remote.origin.url'], text=True).strip()
    token = url.split('@')[0].split(':')[-1]
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # 拉取 words.json
    req = urllib.request.Request(
        f'https://api.github.com/repos/bog5d/bog-vocab-tracker/contents/data/words.json',
        headers={'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    )
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        info = json.loads(resp.read())
    words_data = json.loads(base64.b64decode(info['content']))
    words = words_data['words']

    # 安装 pronouncing
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pronouncing', '-q'], check=False)
    import pronouncing

    updated = 0
    for w in words:
        if args.skip_existing and w.get('phonetic', '').strip():
            continue
        w_lower = w['word'].lower()
        phones = pronouncing.phones_for_word(w_lower)
        if phones:
            w['phonetic'] = arpabet_to_ipa(phones[0])
            updated += 1
            if not args.dry_run:
                print(f"  {w['word']}: {w['phonetic']}")

    if args.dry_run:
        print(f"\n[Dry run] Would update {updated} words")
        return

    # 推送
    new_content = base64.b64encode(json.dumps(words_data, ensure_ascii=False).encode()).decode()
    put_req = urllib.request.Request(
        f'https://api.github.com/repos/bog5d/bog-vocab-tracker/contents/data/words.json',
        data=json.dumps({
            'message': f'批量补全音标: {updated} 词',
            'content': new_content,
            'sha': info['sha']
        }).encode(),
        headers={
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        },
        method='PUT'
    )
    with urllib.request.urlopen(put_req, context=ctx, timeout=15) as resp:
        result = json.loads(resp.read())
    print(f"\nPushed: {result['commit']['sha'][:7]}")
    print(f"Updated: {updated} words")

if __name__ == '__main__':
    main()