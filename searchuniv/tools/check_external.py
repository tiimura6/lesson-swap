#!/usr/bin/env python3
"""他のAIが集めた JSON を、取り込む前に確かめる。
使い方: python3 tools/check_external.py 入力.json  → 問題の一覧を表示し、取り込める形を batches/external_日時.json に書き出す
- 出典URL（sources）が無い学校、cat/features/memo が足りない新規校は取り込まない。
- 2027年度以外の入試日程・入試方式は落とす（学費は2026年度まで可）。
- 取り込むデータには info._via = "external-ai" を付け、自動収集が大学公式で裏取りする。"""
import json, os, re, sys, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATS = {'national', 'public', 'private', 'daigakkou', 'senmon'}
URLRE = re.compile(r'https?://[^\s\]\)"]+')
def clean_url(u):
    """[https://a](https://www.google.com/search?q=https://a) のような書き方から、実際のURLを取り出す"""
    if not isinstance(u, str): return u
    urls = URLRE.findall(u)
    urls = [re.sub(r'^https://www\.google\.com/search\?q=', '', x) for x in urls]
    return urls[0] if urls else u
def deep_clean(o):
    if isinstance(o, dict): return {k: deep_clean(v) for k, v in o.items()}
    if isinstance(o, list): return [deep_clean(v) for v in o]
    if isinstance(o, str) and ('http' in o) and (o.startswith('[') or 'google.com/search' in o): return clean_url(o)
    if isinstance(o, str) and o.startswith('http') and 'utm_' in o: return re.sub(r'[?&]utm_[^#]*', '', o)  # 広告の追跡用の文字を外す
    return o
# 数字の項目は、その数字が載っているページ（学費ページ・河合塾など）が出典に無ければ取り込まない
NEED_SRC = {'money': r'academicpay|gakunou|gakuno|gakuhi|tuition|fee|noufu|nofu|gakuhi|expense|cost|passnavi|keinet|manabi|学費|納付',
            'difficulty': r'keinet|passnavi|manabi', 'fdiff': r'keinet|passnavi|manabi'}
def main(path):
    raw = open(path, encoding='utf-8').read().strip()
    raw = re.sub(r'^```(json)?|```$', '', raw, flags=re.M).strip()
    data = json.loads(raw); data = data if isinstance(data, list) else [data]
    data = deep_clean(data)
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
        for k, pat in NEED_SRC.items():
            if info.get(k) and not any(re.search(pat, u, re.I) for u in src):
                notes.append(f'{n}: {k} は裏付けのページが出典に無いので取り込まない'); info.pop(k)
        # 日程：2027-02-06 → 2/6 に揃え、日付が1つも無い行は落とす
        sc = info.get('schedule')
        if isinstance(sc, dict) and isinstance(sc.get('rows'), list):
            iso = lambda s: re.sub(r'20\d\d[-/]0?(\d{1,2})[-/]0?(\d{1,2})', r'\1/\2', s).replace('～', '〜') if isinstance(s, str) else s
            rows = [{k: (iso(v) if k in ('apply', 'exam', 'result', 'proc') else v) for k, v in z.items()} for z in sc['rows'] if isinstance(z, dict)]
            kept = [z for z in rows if any(z.get(k) for k in ('apply', 'exam', 'result', 'proc'))]
            if len(kept) < len(rows): notes.append(f'{n}: 日付の無い日程の行を {len(rows) - len(kept)} 件落とした')
            sc['rows'] = kept
        # year 以外がすべて空（null）の項目は落とす
        for k in list(info):
            v = info[k]
            if isinstance(v, dict) and not any(x not in (None, '', [], {}) and not (isinstance(x, list) and all(y is None for y in x)) for z, x in v.items() if z != 'year'):
                info.pop(k)
        # 方式名の「※…」は見づらいので（…）に直す
        for k, z in (('schedule', 'rows'), ('methods', 'list'), ('subjects', 'rows')):
            for row in ((info.get(k) or {}).get(z) or []):
                if isinstance(row, dict) and isinstance(row.get("name"), str) and "※" in row["name"]:
                    row['name'] = re.sub(r'\s*※\s*(.+)$', r'（\1）', row['name'])
        # 学費：内訳の合計が初年度の額と合わない行は、0 を「不明（null）」に直す（抜けている費目がある）
        for row in ((info.get('money') or {}).get('rows') or []):
            if isinstance(row, dict) and isinstance(row.get('first_year'), (int, float)):
                ks = ('admission', 'tuition', 'facility', 'practical', 'other')
                if all(isinstance(row.get(k), (int, float)) for k in ks) and sum(row[k] for k in ks) != row['first_year']:
                    for k in ks:
                        if row[k] == 0: row[k] = None
                    notes.append(f"{n}: 学費「{row.get('f')}」は内訳の合計が初年度の額と合わない")
        # 入試方式のリンクが大学のトップページなら外す（入試の資料ではない）
        hp = (r.get('hp') or '').rstrip('/')
        for row in ((info.get('methods') or {}).get('list') or []):
            if isinstance(row, dict) and hp and (row.get('url') or '').rstrip('/') == hp: row['url'] = None
        # 6年制の行の four_year は「4年間合計」と誤解されるので外す（6年間の総額は特色・メモに書く）
        for row in ((info.get('money') or {}).get('rows') or []):
            if isinstance(row, dict) and row.get('four_year') and re.search(r'6年', str(row.get('f', ''))):
                notes.append(f"{n}: 学費「{row.get('f')}」の総額 {row['four_year']:,} 円は6年間分なので four_year から外した"); row['four_year'] = None
        # 中身が空の入れ物（rows/list/events が空）は落とす
        for k in list(info):
            v = info[k]
            if isinstance(v, dict) and any(isinstance(v.get(z), list) for z in ('rows', 'list', 'events')) and not any(v.get(z) for z in ('rows', 'list', 'events')) and not v.get('url'):
                info.pop(k)
        info = {k: v for k, v in info.items() if v not in (None, '', [], {})}
        info['_via'] = 'external-ai'
        r2 = {k: v for k, v in r.items() if k in ('name', 'cat', 'type', 'pref', 'pref_name', 'city', 'hp', 'reading', 'features', 'memo', 'aliases', 'latlng')}
        r2['info'] = info; r2['sources'] = src; r2['info']['sources'] = src
        out.append(r2); notes.append(f'{n}: OK（{"新規" if new else "既存校の補完"}・項目 {len(info)-1}・出典 {len(src)}）')
    # 取り込んだ新規校は、裏取りと足りない項目の収集を自動収集の列に入れる
    newn = [r['name'] for r in out if r['name'] not in cards]
    if newn:
        have = {(e.get('name'), tuple(e.get('need', []))) for e in q['enrich']}
        ver = [{'name': n, 'need': ['verify']} for n in newn if (n, ('verify',)) not in have]
        rest = [{'name': n, 'need': [k]} for n in newn for k in ('methods', 'schedule_dates', 'fees', 'scholar') if (n, (k,)) not in have]
        q['enrich'] = ver + q['enrich'] + rest   # 裏取り(verify)は先頭、足りない項目の収集は後ろ
        json.dump(q, open(os.path.join(ROOT, 'data', 'queue.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        notes.append(f'新規 {len(newn)} 校の裏取りと補完（入試方式・日程・学費・奨学金）を自動収集の列に追加')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H%M')
    dst = os.path.join(ROOT, 'batches', f'external_{stamp}.json')
    json.dump(out, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n'.join(notes)); print(f'\n取り込める {len(out)} 校 → {dst}\n次に: python3 tools/merge_batch.py {dst}')
if __name__ == '__main__':
    main(sys.argv[1])
