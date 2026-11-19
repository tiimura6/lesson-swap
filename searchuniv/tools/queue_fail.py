#!/usr/bin/env python3
"""取得に失敗した enrich 項目を記録し、キューのいちばん最後に回す（2026-11-19 先生の依頼）。

使い方（searchuniv/ で実行）:
  python3 tools/queue_fail.py "<大学名>" <need> "<今回わかったこと（出典で何が無かったか）>"
    例: python3 tools/queue_fail.py "札幌大学" fees "Kei-Net・パスナビとも2027年度の学費内訳なし"
  python3 tools/queue_fail.py --list      いま後回しになっている項目を表示

- その大学の need を含む enrich 項目の fails を1増やし、note に「／YYYY-MM-DD 内容」を足し、
  last_fail に日付を入れて enrich の末尾へ移す。
- fails が DEFER（2）以上になった項目は deferred: true（後回し）。選ぶときは deferred でない項目を先に使い切る。
- 後回しの項目は build.py が NOGET として埋め込み、大学の画面に「自動収集で取得できなかった項目」として出る。
- 取得できたら、これまでどおりその項目を done に移す（画面の表示も消える）。
"""
import datetime, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QP = os.path.join(ROOT, 'data', 'queue.json')
DEFER = 2


def load():
    return json.load(open(QP, encoding='utf-8'))


def save(q):
    json.dump(q, open(QP, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)


def today():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d')


def reorder(q):
    """後回し（deferred）の項目を enrich の最後にまとめる（それ以外の並びは変えない）。"""
    q['enrich'] = [e for e in q['enrich'] if not e.get('deferred')] + [e for e in q['enrich'] if e.get('deferred')]


def fail(name, need, text):
    q = load()
    hit = [e for e in q['enrich'] if e.get('name') == name and need in e.get('need', [])]
    if not hit:
        sys.exit('enrich に %s（%s）が見つかりません' % (name, need))
    e = hit[0]
    q['enrich'].remove(e)
    d = today()
    e['fails'] = int(e.get('fails', 0)) + 1
    e['last_fail'] = d
    if text:
        e['note'] = (e.get('note', '') + '／' if e.get('note') else '') + d + ' ' + text
    if e['fails'] >= DEFER:
        e['deferred'] = True
    q.setdefault('fail_count', {})[name] = max(q.get('fail_count', {}).get(name, 0), e['fails'])
    q['enrich'].append(e)
    reorder(q)
    save(q)
    print('%s（%s）：%d回目の失敗%s' % (name, '・'.join(e['need']), e['fails'], '→ 後回し（画面に表示）' if e.get('deferred') else '→ 末尾へ'))


def show():
    q = load()
    L = [e for e in q['enrich'] if e.get('deferred')]
    print('後回し %d件 / enrich %d件' % (len(L), len(q['enrich'])))
    for e in L:
        print(' ', e['name'], e['need'], e.get('fails'), e.get('last_fail', ''))


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['--list']:
        show()
    elif len(a) >= 2:
        fail(a[0], a[1], a[2] if len(a) > 2 else '')
    else:
        print(__doc__)
