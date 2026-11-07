#!/usr/bin/env python3
"""他のAIが集めた JSON を、取り込む前に確かめる。
使い方: python3 tools/check_external.py 入力.json  → 問題の一覧を表示し、取り込める形を batches/external_日時.json に書き出す
- 出典URL（sources）が無い学校、cat/features/memo が足りない新規校は取り込まない。
- 2027年度以外の入試日程・入試方式は落とす（学費は2026年度まで可）。
- 取り込むデータには info._via = "external-ai" を付け、自動収集が大学公式で裏取りする。"""
import json, os, re, sys, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATS = {'national', 'public', 'private', 'daigakkou', 'senmon'}
def main(path):
    raw = open(path, encoding='utf-8').read().strip()
    raw = re.sub(r'^```(json)?|```$', '', raw, flags=re.M).strip()
    data = json.loads(raw); data = data if isinstance(data, list) else [data]
    cards = {c[0] for c in json.load(open(os.path.join(ROOT, 'data', 'cards.json'), encoding='utf-8'))}
    q = json.load(open(os.path.join(ROOT, 'data', 'queue.json'), encoding='utf-8'))
    excl = {e['name'] for e in q.get('excluded', [])}
    out, notes = [], []
    for r in data:
        n = (r.get('name') or '').strip()
        if not n: notes.append('名前の無い要素を除外'); continue
        if r.get('skip'): notes.append(f'{n}: 対象外（{r["skip"]}）→ 除外リスト候補'); continue
        if n in excl: notes.append(f'{n}: 除外済みの学校'); continue
        src = [u for u in (r.get('sources') or []) if isinstance(u, str) and u.startswith('http')]
        if not src: notes.append(f'{n}: 出典URLが無いので取り込まない'); continue
        new = n not in cards
        if new and (r.get('cat') not in CATS or len([f for f in r.get('features') or [] if f]) < 2 or not r.get('memo')):
            notes.append(f'{n}: 新規校なのに cat/features/memo が足りない'); continue
        info = dict(r.get('info') or {})
        for k in ('schedule', 'methods', 'subjects'):
            y = str((info.get(k) or {}).get('year', ''))
            if info.get(k) and y and '2027' not in y:
                notes.append(f'{n}: {k} が {y} のため落とした'); info.pop(k)
        y = str((info.get('money') or {}).get('year', ''))
        if info.get('money') and y and not re.search(r'202[67]', y): notes.append(f'{n}: 学費が {y} のため落とした'); info.pop('money')
        # 空の項目は落とす
        info = {k: v for k, v in info.items() if v not in (None, '', [], {})}
        info['_via'] = 'external-ai'
        r2 = {k: v for k, v in r.items() if k in ('name', 'cat', 'type', 'pref', 'pref_name', 'city', 'hp', 'reading', 'features', 'memo', 'aliases', 'latlng')}
        r2['info'] = info; r2['sources'] = src; r2['info']['sources'] = src
        out.append(r2); notes.append(f'{n}: OK（{"新規" if new else "既存校の補完"}・項目 {len(info)-1}・出典 {len(src)}）')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H%M')
    dst = os.path.join(ROOT, 'batches', f'external_{stamp}.json')
    json.dump(out, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n'.join(notes)); print(f'\n取り込める {len(out)} 校 → {dst}\n次に: python3 tools/merge_batch.py {dst}')
if __name__ == '__main__':
    main(sys.argv[1])
