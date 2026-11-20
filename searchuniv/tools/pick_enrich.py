#!/usr/bin/env python3
"""空欄を優先して enrich を選ぶ（2026-11-20 先生の方針「収集率を早く上げる」）。

使い方（searchuniv/ で実行）:
  python3 tools/pick_enrich.py --gaps      Kei-Net でまとめて埋まる空欄がある学校を enrich の先頭に積む（need: gap_keinet）
  python3 tools/pick_enrich.py [N]         今回処理する enrich を最大 N 件（既定 8）選んで表示する（キューは変えない）
  python3 tools/pick_enrich.py --stats     段（tier）ごとの件数を表示

選ぶ順番（deferred は使わない。各段の中は cards.json の並び＝主要校が先）:
  段0  gap_keinet（Kei-Net の大学トップ・学部・資格・進路・共テ科目・ボーダーの各ページで、
       研究分野・学生数・設立・取得できる資格・主な進路・共テの科目・偏差値のうち空いている欄をまとめて埋める）
  段1  need の対象の欄が data/info.json でまだ空の項目（奨学金・OC・協定校・学部別難易度・英語外部試験・倍率・入試方式・入試科目など）
  段2  それ以外（すでにある欄の手直し：方式ごとの公式リンク、倍率を5年分に延ばす、methods_gap、外部AIの確認、学費内訳など）
  ※ 入試科目（subjects）は行数が多いため1回2校まで。段2は段0・段1が無くなったときだけ。
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda n: os.path.join(ROOT, 'data', n + '.json')
D = lambda n: json.load(open(P(n), encoding='utf-8'))

# gap_keinet で埋める欄（build.py の FILL_ITEMS と同じ判定）
GAP_FIELDS = {
    'research': lambda i: i.get('research'),
    'students': lambda i: i.get('students'),
    'founded': lambda i: i.get('founded'),
    'licenses': lambda i: i.get('licenses'),
    'careers': lambda i: i.get('careers'),
    'kyotsu': lambda i: (i.get('kyotsu') or {}).get('kamoku') or (i.get('kyotsu') or {}).get('kyoka'),
    'difficulty': lambda i: (i.get('difficulty') or {}).get('hensachi') or (i.get('difficulty') or {}).get('kyotei'),
}
# need → その need が埋める欄（空なら段1）
NEED_FIELD = {
    'scholar': lambda i: i.get('scholar'), 'oc': lambda i: i.get('oc'), 'partners': lambda i: i.get('partners'),
    'extra': lambda i: i.get('fdiff'), 'eng': lambda i: i.get('eng'), 'ratios': lambda i: i.get('ratios'),
    'methods': lambda i: (i.get('methods') or {}).get('list'), 'subjects': lambda i: (i.get('subjects') or {}).get('rows'),
    'qtrend': lambda i: i.get('qtrend'), 'licenses': lambda i: i.get('licenses'), 'research': lambda i: i.get('research'),
    'careers': lambda i: i.get('careers'), 'kyotsu': GAP_FIELDS['kyotsu'], 'departments': lambda i: i.get('departments') or i.get('faculties'),
    'fees': lambda i: i.get('money') or i.get('tuition'), 'schedule_dates': lambda i: (i.get('schedule') or {}).get('rows'),
    'schedule_general': lambda i: (i.get('schedule') or {}).get('rows'),
}


def keinet_code(i):
    for s in i.get('sources') or []:
        m = re.search(r'search\.keinet\.ne\.jp/(?:outline/department/)?(\d{4})', s)
        if m:
            return m.group(1)
    return ''


def order():
    return {c[0]: k for k, c in enumerate(D('cards'))}


def tier(e, info):
    need = e.get('need', [])
    if 'gap_keinet' in need:
        return 0
    i = info.get(e['name']) or {}
    if any(n in NEED_FIELD and not NEED_FIELD[n](i) for n in need):
        return 1
    return 2


def add_gaps():
    q = D('queue'); info = D('info'); od = order()
    have = {e['name'] for e in q['enrich'] if 'gap_keinet' in e.get('need', [])}
    have |= {d['name'] for d in q['done'] if isinstance(d, dict) and 'gap_keinet' in d.get('need', [])}
    new = []
    for name in sorted(info, key=lambda n: od.get(n, 9999)):
        if name in have:
            continue
        i = info[name] or {}
        miss = [k for k, f in GAP_FIELDS.items() if not f(i)]
        if miss:
            e = {'name': name, 'need': ['gap_keinet'], 'fields': miss}
            k = keinet_code(i)
            if k:
                e['keinet'] = k
            new.append(e)
    q['enrich'] = new + q['enrich']
    json.dump(q, open(P('queue'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('gap_keinet を %d校 積みました（既存 %d校）' % (len(new), len(have)))


def ranked():
    q = D('queue'); info = D('info'); od = order()
    L = [e for e in q['enrich'] if not e.get('deferred')]
    return sorted(L, key=lambda e: (tier(e, info), od.get(e['name'], 9999))), info


def pick(n):
    L, info = ranked()
    out, subj = [], 0
    t01 = any(tier(e, info) < 2 for e in L)
    for e in L:
        t = tier(e, info)
        if t == 2 and t01:
            break
        if 'subjects' in e.get('need', []):
            if subj >= 2:
                continue
            subj += 1
        out.append((t, e))
        if len(out) >= n:
            break
    for t, e in out:
        print('段%d' % t, json.dumps(e, ensure_ascii=False))


def stats():
    from collections import Counter
    L, info = ranked()
    print(Counter('段%d' % tier(e, info) for e in L))


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['--gaps']:
        add_gaps()
    elif a[:1] == ['--stats']:
        stats()
    else:
        pick(int(a[0]) if a else 8)
