#!/usr/bin/env python3
"""国土数値情報「鉄道データ(N02)」から、地図に重ねる新幹線・JR在来線の線を作る。
使い方: python3 tools/make_rail.py <sections.json>
  sections.json は https://github.com/antfu/mlit-json の data/sections.json（N02 令和6年を JSON にしたもの）。
出力: data/map_rail.json（地図の座標に投影し、細かい点を間引いた SVG の path 文字列）
出典表示：「国土数値情報（鉄道データ）」（国土交通省）を加工して作成"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import project, ROOT

def simplify(pts, tol):
    if len(pts) < 3: return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1; L = (dx*dx + dy*dy) ** 0.5 or 1e-9
    i, dmax = 0, -1
    for k in range(1, len(pts) - 1):
        d = abs(dy*(pts[k][0]-x1) - dx*(pts[k][1]-y1)) / L
        if d > dmax: i, dmax = k, d
    if dmax <= tol: return [pts[0], pts[-1]]
    return simplify(pts[:i+1], tol)[:-1] + simplify(pts[i:], tol)

def chains(secs):
    # 端点が同じ区間をつないで長い線にする（path の文字数を減らす）
    segs = [[tuple(project(lat, lon)) for lon, lat in s] for s in secs if len(s) > 1]
    ends = {}
    for i, s in enumerate(segs):
        for e in (s[0], s[-1]): ends.setdefault(e, []).append(i)
    used, out = set(), []
    for i in range(len(segs)):
        if i in used: continue
        used.add(i); line = list(segs[i])
        for _ in range(2):
            while True:
                nxt = [j for j in ends.get(line[-1], []) if j not in used]
                if not nxt: break
                j = nxt[0]; used.add(j); s = segs[j]
                line += (s[1:] if s[0] == line[-1] else s[::-1][1:])
            line.reverse()
        out.append(line)
    return out

def path(secs, tol):
    out = []
    for p in chains(secs):
        p = simplify(p, tol)
        if len(p) == 2 and abs(p[0][0]-p[1][0]) + abs(p[0][1]-p[1][1]) < tol: continue
        out.append('M' + ' '.join('%g %g' % (x, y) for x, y in p))
    return ''.join(out)

if __name__ == '__main__':
    secs = json.load(open(sys.argv[1], encoding='utf-8'))
    shin = [s['coordinates'] for s in secs if '新幹線' in s['line']]
    jr = [s['coordinates'] for s in secs if '旅客鉄道' in s['operator'] and '新幹線' not in s['line']]
    other = [s['coordinates'] for s in secs if '旅客鉄道' not in s['operator']]
    res = {'shin': path(shin, 0.15), 'jr': path(jr, 0.6), 'other': path(other, 0.6),
           'credit': '「国土数値情報（鉄道データ）」（国土交通省）を加工して作成'}
    json.dump(res, open(os.path.join(ROOT, 'data', 'map_rail.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print({k: len(v) for k, v in res.items()})
