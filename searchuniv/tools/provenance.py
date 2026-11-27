#!/usr/bin/env python3
"""出典の区分（一次資料優先・2026-11-25 先生の方針）。

方針（PIPELINE.md「出典の区分」）：
- 入試の事実（日程・方式・科目・学費・倍率・英語外部試験・奨学金・OC）は、各大学の公式サイト・募集要項（一次資料）を最終的な出典にする。
- 学部構成・学生数・設立などは、大学ポートレート・文部科学省などの公的DB（準一次）でもよい。
- 偏差値・共テ得点率（difficulty / fdiff）は予備校の推定値なので一次資料は存在しない。「予備校推定」と明記して残す。
- 河合塾・旺文社・ベネッセなどの二次資料は、一次資料を見つける手がかりと、一次資料から写した値の検算にだけ使う。

区分の記号：p＝大学公式（一次）／m＝一部だけ大学公式／d＝公的DB（準一次）／s＝二次資料のみ／u＝出典の記録なし（大学公式で未照合）／e＝予備校推定

使い方：
  python3 tools/provenance.py --report          優先校（data/primary_ledger.json）の一次資料化の進み具合
  python3 tools/provenance.py --pick 2          次に一次資料化する学校と、未照合の項目
  python3 tools/provenance.py --seed            台帳の URL 欄を、既存データにある大学公式の URL から下書きする（空欄だけ）
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda n: os.path.join(ROOT, 'data', n + '.json')
L = lambda n: json.load(open(P(n), encoding='utf-8'))

# 一次資料（大学公式）を最終的な出典にする項目
PRIMARY_FIELDS = ['schedule', 'methods', 'subjects', 'money', 'ratios', 'eng', 'scholar', 'oc']
# 公的DB（大学ポートレート・文部科学省）でもよい項目
DB_OK_FIELDS = ['departments', 'students', 'founded']
# 予備校の推定値（一次資料は存在しない）
ESTIMATE_FIELDS = ['difficulty', 'fdiff']
LABEL = {'schedule': '入試日程', 'methods': '入試方式', 'subjects': '入試科目', 'money': '学費', 'ratios': '入試倍率',
         'eng': '英語外部試験', 'scholar': '奨学金', 'oc': 'オープンキャンパス', 'departments': '学部・学科',
         'students': '学生数', 'founded': '設立', 'difficulty': '偏差値・共テ得点率', 'fdiff': '学部別の難易度'}

DB_HOSTS = ('portraits.niad.ac.jp', 'mext.go.jp', 'dnc.ac.jp', 'niad.ac.jp', 'e-stat.go.jp', 'jasso.go.jp')
SECONDARY_HOSTS = ('keinet.ne.jp', 'obunsha.co.jp', 'benesse', 'manabi.', 'toshin.com', 'yozemi', 'sundai', 'stepup-school',
                   'univ-journal.net', 'shingakunet', 'mynavi', 'minkou', 'wikipedia.org', 'gakusei', 'jpnuniv')
# 大学が出願・要項配布に使う外部サイト（大学の公式な配布元なので一次扱い）
OFFICIAL_RELAY = ('postanet.jp', 'e-apply.jp', 'ucaro.net', 'guide.52school.com/guidance/net-', 'telemail.jp/shingaku', 'mirai-compass')


def host(u):
    m = re.match(r'https?://([^/]+)', u or '')
    return re.sub(r'^www\.', '', m.group(1).lower()) if m else ''


def base_domain(u):
    """www.ibaraki.ac.jp → ibaraki.ac.jp、admission.xxx.ac.jp → xxx.ac.jp（.ac.jp / .go.jp / .jp / .com などの末尾2〜3段）"""
    h = host(u)
    parts = h.split('.')
    if len(parts) >= 3 and parts[-1] == 'jp' and parts[-2] in ('ac', 'go', 'or', 'co', 'ed', 'lg', 'ne'):
        return '.'.join(parts[-3:])
    return '.'.join(parts[-2:])


def classify(u, hp_url):
    """1つの URL の区分：p / d / s"""
    h = host(u)
    if not h: return None
    if any(x in u for x in OFFICIAL_RELAY): return 'p'
    if hp_url and (h == host(hp_url) or h.endswith('.' + base_domain(hp_url)) or h == base_domain(hp_url)):
        return 'p'
    if any(h.endswith(x) or x in h for x in DB_HOSTS): return 'd'
    return 's'


def field_urls(v):
    """項目の値に入っている URL（行ごとの url、項目の sources / url / src）"""
    out = []
    if isinstance(v, dict):
        for k in ('url', 'src'):
            if isinstance(v.get(k), str): out.append(v[k])
        if isinstance(v.get('sources'), list): out += [s for s in v['sources'] if isinstance(s, str)]
        for key in ('rows', 'list'):
            for r in v.get(key) or []:
                if isinstance(r, dict) and isinstance(r.get('url'), str): out.append(r['url'])
    return [u for u in out if u.startswith('http')]


def row_kinds(v, hp_url):
    """行ごとの区分（行に url が無ければ None）。一部の行だけ公式、を見分けるのに使う"""
    if not isinstance(v, dict): return []
    rows = v.get('rows') or v.get('list') or []
    return [classify(r.get('url'), hp_url) if isinstance(r, dict) and r.get('url') else None for r in rows if isinstance(r, dict)]


def kind_of(rec, field, hp_url):
    """1校1項目の区分"""
    if field in ESTIMATE_FIELDS: return 'e' if rec.get(field) else None
    v = rec.get(field)
    if v in (None, '', [], {}): return None
    urls = field_urls(v) + list(((rec.get('_src') or {}).get(field) or {}).get('u') or [])
    ks = {classify(u, hp_url) for u in urls} - {None}
    rk = row_kinds(v, hp_url)
    if rk and any(k == 'p' for k in rk) and not all(k == 'p' for k in rk):
        # 行ごとに出典があるとき、公式の行と未照合の行が混ざっていれば「一部公式」
        return 'm'
    if 'p' in ks: return 'p'
    if 'd' in ks: return 'd'
    if 's' in ks: return 's'
    return 'u'


def kinds(rec, hp_url):
    out = {}
    for f in PRIMARY_FIELDS + DB_OK_FIELDS + ESTIMATE_FIELDS:
        k = kind_of(rec, f, hp_url)
        if k: out[f] = k
    return out


def done_ok(field, k):
    return k == 'p' or (field in DB_OK_FIELDS and k == 'd')


def ledger():
    return L('primary_ledger') if os.path.exists(P('primary_ledger')) else {'priority': []}


def report():
    info, hp, lg = L('info'), L('hp'), ledger()
    rows = []
    tot = {f: [0, 0] for f in PRIMARY_FIELDS}
    for e in lg['priority']:
        n = e['name']; rec = info.get(n) or {}
        ks = kinds(rec, hp.get(n, ''))
        for f in PRIMARY_FIELDS:
            if f in ks:
                tot[f][1] += 1
                if ks[f] == 'p': tot[f][0] += 1
        rows.append((n, ks))
    print('優先校 %d校の一次資料化（大学公式で照合済み／データあり）' % len(rows))
    for f in PRIMARY_FIELDS:
        a, b = tot[f]
        print('  %-10s %3d / %3d' % (LABEL[f], a, b))
    full = sum(1 for _, ks in rows if all(ks.get(f) == 'p' for f in ('schedule', 'methods', 'money')))
    print('  日程・方式・学費の3項目すべて公式：%d校' % full)


def pick(n):
    info, hp, lg = L('info'), L('hp'), ledger()
    out = []
    for e in lg['priority']:
        if e.get('skip'): continue
        nm = e['name']; rec = info.get(nm) or {}
        ks = kinds(rec, hp.get(nm, ''))
        todo = [f for f in PRIMARY_FIELDS if not done_ok(f, ks.get(f)) and f not in (e.get('wait') or {})]  # 公式の公表待ち（wait）は選ばない
        if not todo: continue
        out.append({'name': nm, 'hp': hp.get(nm, ''), 'todo': todo, 'pages': e.get('pages', {}), 'fails': e.get('fails', 0)})
    out.sort(key=lambda x: x['fails'] >= 2)  # 2回取れなかった学校は後回し（並びは台帳の順）
    for x in out[:n]:
        print(json.dumps(x, ensure_ascii=False))
    if not out: print('優先校の一次資料化はすべて完了')


PAGE_HINT = {
    'yoko': re.compile(r'yoko|youkou|bosyu|boshu|senbatsu|senbatu|sembatsu|guidelines|requirement|募集要項|選抜要項|要項', re.I),
    'result': re.compile(r'kekka|result|jisseki|jokyo|joukyou|data|statistics|入試結果|志願者|状況', re.I),
    'admission': re.compile(r'admission|nyushi|nyuushi|exam|entrance|juken|受験|入試', re.I),
}


def seed():
    """台帳の pages の空欄を、既存データにある大学公式 URL から下書きする（定期実行が公式で確かめて直す前提の手がかり）"""
    info, hp, lg = L('info'), L('hp'), ledger()
    filled = 0
    for e in lg['priority']:
        n = e['name']; h = hp.get(n, ''); rec = info.get(n) or {}
        urls = list(rec.get('sources') or [])
        for f in PRIMARY_FIELDS: urls += field_urls(rec.get(f))
        off = [u for u in dict.fromkeys(urls) if isinstance(u, str) and classify(u, h) == 'p']
        pg = e.setdefault('pages', {})
        for k in ('yoko', 'result', 'admission'):
            if pg.get(k): continue
            ok = (lambda u: not u.lower().endswith('.pdf')) if k == 'admission' else (lambda u: True)
            hit = next((u for u in off if PAGE_HINT[k].search(u) and ok(u)), '')
            if hit: pg[k] = hit; filled += 1
    json.dump(lg, open(P('primary_ledger'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('台帳の URL を %d 件下書き（大学公式の URL のみ。定期実行が中身を確かめる）' % filled)


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--report' in a: report()
    elif '--pick' in a: pick(int(a[a.index('--pick') + 1]) if len(a) > a.index('--pick') + 1 else 2)
    elif '--seed' in a: seed()
    else: print(__doc__)
