"""check_external.py の出力（batches/external_*.json）に「迷ったら取り込まない」判断を足す。
2026-11-25〜26 の Gemini 取り込み（8周・80校）で手で判断した決まりを自動にしたもの。

使い方:
  python3 tools/postfilter_external.py batches/external_XXXX.json [手で落とす指定.json]
手で落とす指定（任意）: {"大学名": ["*" | "項目" | "項目:行名の一部", ...]}
  "*" は学校ごと取り込まない。"schedule:総合型" は schedule/schedule_replace の行名に「総合型」を含む行を落とす。

出力ファイルは上書きする。落とした理由を標準出力に1行ずつ出す（報告にそのまま使える）。
"""
import json, re, sys
from urllib.parse import urlparse

path = sys.argv[1]
drops = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else {}
I = json.load(open('data/info.json'))
HP = json.load(open('data/hp.json'))
data = json.load(open(path))

# 2027年度（令和9年度）以外の要項に見える URL
BAD_YEAR = re.compile(r'R8[_/.-]|r8_|令和8|2026年度入試|2026nyushi|R7[_/.-]|令和7|2025nyushi')
# 公式以外で使ってよい二次資料（偏差値などの裏付け用）
OK_SECOND = re.compile(r'keinet\.ne\.jp|passnavi\.obunsha|manabi\.benesse')

def dom(u):
    try:
        h = urlparse(u if '://' in u else 'https://' + u).hostname or ''
    except Exception:
        return ''
    h = h.lower()
    if h.startswith('www.'):
        h = h[4:]
    p = h.split('.')
    # ○○.ac.jp / ○○.go.jp / ○○.co.jp などは3つ、ほかは2つで「同じ組織」とみなす
    if len(p) >= 3 and p[-1] == 'jp' and p[-2] in ('ac', 'go', 'co', 'or', 'ne', 'ed', 'lg'):
        return '.'.join(p[-3:])
    return '.'.join(p[-2:])

log = []
def L(n, s):
    log.append(f'{n}: {s}')

def rows_of(v):
    if not isinstance(v, dict):
        return None, None
    for k in ('list', 'rows', 'events'):
        if isinstance(v.get(k), list):
            return k, v[k]
    return None, None

def empty(x):
    return x in (None, '', [], {})

for r in data:
    n = r['name']; info = r['info']; cur = I.get(n, {})
    reg = dom(HP.get(n) or '')
    srcs = (r.get('sources') or []) + (info.get('sources') or [])

    # 0) 手で「学校ごと落とす」
    if '*' in drops.get(n, []):
        r['info'] = {'_via': info.get('_via')}; L(n, '学校ごと取り込まない（手で判断）'); continue

    # 1) 公式サイトが登録と違う → 学校ごと見送り（別の学校・別法人の可能性）
    gem = dom(r.get('hp') or '')
    if reg and gem and gem != reg:
        r['info'] = {'_via': info.get('_via')}
        L(n, f'公式サイトが登録（{reg}）と違う（{gem}）ため学校ごと見送り'); continue

    # 2) 入試の行の URL が登録の公式ドメイン以外 → その項目を落とす
    for k in ('methods', 'schedule', 'schedule_replace', 'subjects'):
        sub, rows = rows_of(info.get(k))
        if rows is None:
            continue
        keep = []
        for z in rows:
            u = str(z.get('url') or '')
            if u and reg and dom(u) != reg:
                L(n, f'{k}「{z.get("name") or z.get("f")}」は出典が登録の公式ドメイン外（{dom(u)}）なので落とした'); continue
            if u and BAD_YEAR.search(u):
                L(n, f'{k}「{z.get("name") or z.get("f")}」は2027年度以外の要項のURLなので落とした'); continue
            keep.append(z)
        info[k][sub] = keep
    # methods の URL が全部公式外なら、同じ要項から来た schedule/subjects も落とす
    m = (info.get('methods') or {}).get('list') if isinstance(info.get('methods'), dict) else None
    if isinstance(info.get('methods'), dict) and m == [] and reg:
        for k in ('schedule', 'schedule_replace', 'subjects'):
            if k in info:
                info.pop(k); L(n, f'{k} は方式の出典が公式外のため一緒に落とした')

    # 3) 公式・Kei-Net・パスナビ・マナビジョン以外の出典がある → 日程とOCは落とす（どこ由来か分からないため）
    other = sorted({dom(s) for s in srcs if s and dom(s) != reg and not OK_SECOND.search(s)})
    if other and reg:
        for k in ('schedule', 'schedule_replace', 'oc'):
            if k in info:
                info.pop(k); L(n, f'{k} は承認外の出典（{", ".join(other)}）が混じるため落とした')

    # 4) 日程：日付が「〜」だけ・開始日だけの行は落とす
    for k in ('schedule', 'schedule_replace'):
        sub, rows = rows_of(info.get(k))
        if rows is None:
            continue
        keep = []
        for z in rows:
            vals = [str(z.get(x) or '') for x in ('apply', 'exam', 'result', 'proc')]
            real = [v for v in vals if re.search(r'\d', v) and not re.fullmatch(r'\s*〜?\s*\d{1,2}/\d{1,2}\s*〜\s*', v)]
            if not real:
                L(n, f'{k}「{z.get("name")}」は日付がそろわないので落とした'); continue
            keep.append(z)
        info[k][sub] = keep

    # 5) 学費：内訳の無い行・合計が合わない行を落とす。既に学部別の額がある学校には足さない
    for k in ('money', 'money_replace'):
        sub, rows = rows_of(info.get(k))
        if rows is None:
            continue
        keep = []
        for z in rows:
            if empty(z.get('tuition')) or empty(z.get('admission')) and empty(z.get('first_year')):
                L(n, f'学費「{z.get("f")}」は授業料などの内訳が無いので落とした'); continue
            parts = [z.get(x) for x in ('admission', 'tuition', 'facility', 'practical', 'other')]
            if z.get('first_year') and all(isinstance(p, (int, float)) for p in parts[:2]):
                s = sum(p for p in parts if isinstance(p, (int, float)))
                if abs(s - z['first_year']) > 1000:
                    L(n, f'学費「{z.get("f")}」は内訳の合計（{s}）と初年度（{z["first_year"]}）が合わないので落とした'); continue
            keep.append(z)
        info[k][sub] = keep
    if 'money_replace' in info and any(z.get('first_year') for z in (cur.get('money') or {}).get('rows', [])):
        info.pop('money_replace'); L(n, '学費は既に学部別の額があるので外部AIの区分は足さない')

    # 6) 奨学金：金額・内容が無い行、在学中の給与・手当は落とす
    sub, rows = rows_of(info.get('scholar'))
    if rows is not None:
        keep = []
        for z in rows:
            if empty(z.get('amount')) or empty(z.get('kind')):
                L(n, f'奨学金「{z.get("name")}」は金額・種類が無いので落とした'); continue
            if re.search(r'給与|手当|公務員', str(z.get('name')) + str(z.get('amount'))):
                L(n, f'奨学金「{z.get("name")}」は給与・手当で奨学金ではないので落とした'); continue
            if re.search(r'2026年度実績|令和8年', str(z.get('amount')) + str(z.get('cond'))):
                L(n, f'奨学金「{z.get("name")}」は2026年度の値なので落とした'); continue
            keep.append(z)
        info['scholar'][sub] = keep

    # 7) 英語外部試験：級・試験名の無い行は落とす
    sub, rows = rows_of(info.get('eng'))
    if rows is not None:
        keep = [z for z in rows if not (empty(z.get('level')) and empty(z.get('tests')))]
        if len(keep) < len(rows):
            L(n, f'英語外部試験 {len(rows)-len(keep)} 行は級・試験名が無いので落とした')
        info['eng'][sub] = keep

    # 8) 科目：科目名の無い行は落とす
    sub, rows = rows_of(info.get('subjects'))
    if rows is not None:
        keep = [z for z in rows if not empty(z.get('subj'))]
        if len(keep) < len(rows):
            L(n, f'科目 {len(rows)-len(keep)} 行は科目名が無いので落とした')
        info['subjects'][sub] = keep

    # 9) OC：日付の無い回は落とす。URL が公式外なら OC ごと落とす
    oc = info.get('oc')
    if isinstance(oc, dict):
        ev = [e for e in (oc.get('events') or []) if e.get('date')]
        if len(ev) < len(oc.get('events') or []):
            L(n, 'オープンキャンパスの日付の無い回を落とした')
        oc['events'] = ev
        if oc.get('url') and reg and dom(oc['url']) != reg:
            info.pop('oc'); L(n, f'オープンキャンパスは URL が公式外（{dom(oc["url"])}）なので落とした')

    # 10) 手で決めた落とし
    for d in drops.get(n, []):
        if ':' in d:
            k, frag = d.split(':', 1)
            for kk in (k, k + '_replace'):
                sub, rows = rows_of(info.get(kk))
                if rows is not None:
                    b = len(rows); info[kk][sub] = [z for z in rows if frag not in str(z.get('name') or z.get('f'))]
                    if b != len(info[kk][sub]):
                        L(n, f'{kk} の「{frag}」の行を落とした（手で判断）')
        elif d in info:
            info.pop(d); L(n, f'{d} を落とした（手で判断）')

    # 空になった項目を消す
    for k in list(info):
        if k in ('_via', 'sources'):
            continue
        sub, rows = rows_of(info[k])
        if sub and not rows:
            info.pop(k)
        elif empty(info[k]):
            info.pop(k)

data = [r for r in data if set(r['info']) - {'_via', 'sources'}]
json.dump(data, open(path, 'w'), ensure_ascii=False, indent=1)
print('\n'.join(log))
print('残り', len(data), '校:', [r['name'] for r in data])
