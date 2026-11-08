#!/usr/bin/env python3
"""短大・専門学校の一覧（名前・場所だけ）を作る。
入力：data/ts_raw/*.txt（1行1校「学校コード|設置区分|学校名|学校所在地」。文部科学省「学校コード一覧」から）
  tandai.txt＝短期大学（学校種 F2・本校）、senmon_*.txt＝専門学校（学校種 H1 のうち専門課程を置く学校）
出力：data/tanki_senmon.json（build_ts.py が地図に使う）。座標は data/ts_coords.json にためる（geolonia/japanese-addresses の町丁目座標）。
使い方：python3 tools/ts_import.py"""
import json, os, re, sys, unicodedata, urllib.parse, urllib.request, glob
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(HERE, *a)
BASE = 'https://raw.githubusercontent.com/geolonia/japanese-addresses/master/api'
KN = {'〇':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
def kan2num(s):
    def conv(m):
        t = m.group(0); v = 0; cur = 0
        for ch in t:
            if ch == '十': v += (cur or 1) * 10; cur = 0
            else: cur = cur * 10 + KN[ch]
        return str(v + cur)
    return re.sub(r'[〇一二三四五六七八九十]+', conv, s)
def norm(s): return kan2num(unicodedata.normalize('NFKC', s)).replace('ヶ', 'ケ').replace('ｹ', 'ケ').replace('大字', '').replace('字', '')
_cache = {}
def get(url):
    if url in _cache: return _cache[url]
    try:
        with urllib.request.urlopen(url, timeout=40) as r: _cache[url] = json.load(r)
    except Exception as e:
        print('  取得できない', url, e, file=sys.stderr); _cache[url] = None
    return _cache[url]
def split_addr(addr, ja):
    m = re.match(r'^(東京都|北海道|京都府|大阪府|.{2,3}?県)', addr)
    if not m: return None, None, addr
    pref = m.group(1); rest = addr[len(pref):]
    cities = sorted(ja.get(pref, []), key=len, reverse=True)
    for c in cities:
        if rest.startswith(c): return pref, c, rest[len(c):]
    # 郡名を省いた書き方など
    for c in cities:
        short = re.sub(r'^.+?郡', '', c)
        if short != c and rest.startswith(short): return pref, c, rest[len(short):]
    # 新しい区（例：浜松市中央区）で住所データにまだ無いときは、同じ市の別の区で代用（市の中心付近）
    m2 = re.match(r'^(.+?市)', rest)
    if m2:
        alt = [c for c in cities if c.startswith(m2.group(1))]
        if alt: return pref, alt[0], ''
    return pref, None, rest
def geocode(pref, city, rest):
    rows = get('%s/ja/%s/%s.json' % (BASE, urllib.parse.quote(pref), urllib.parse.quote(city)))
    if not rows: return None, 'none'
    r = norm(rest); best = None
    for x in rows:
        t = norm(x.get('town', ''))
        if t and r.startswith(t) and x.get('lat') and (best is None or len(t) > len(norm(best.get('town', '')))): best = x
    if best: return [round(float(best['lat']), 4), round(float(best['lng']), 4)], 'town'
    pts = sorted((float(x['lat']), float(x['lng'])) for x in rows if x.get('lat'))
    if not pts: return None, 'none'
    la = sorted(p[0] for p in pts)[len(pts)//2]; lo = sorted(p[1] for p in pts)[len(pts)//2]
    return [round(la, 4), round(lo, 4)], 'city'
def main():
    ja = get(BASE + '/ja.json') or {}
    coords = json.load(open(P('data', 'ts_coords.json'), encoding='utf-8')) if os.path.exists(P('data', 'ts_coords.json')) else {}
    out = []; miss = []
    for f in sorted(glob.glob(P('data', 'ts_raw', '*.txt'))):
        kind = '短大' if os.path.basename(f).startswith('tandai') else '専門'
        for line in open(f, encoding='utf-8'):
            line = line.strip()
            if not line or line.startswith('#'): continue
            a = line.split('|')
            if len(a) < 4: continue
            code, typ, name, addr = [x.strip() for x in a[:4]]
            pref, city, rest = split_addr(addr, ja)
            key = code
            if key not in coords:
                ll, how = (geocode(pref, city, rest) if pref and city else (None, 'none'))
                if ll: coords[key] = {'ll': ll, 'how': how, 'addr': addr}
            c = coords.get(key)
            if not c: miss.append(name + ' ' + addr)
            out.append({'code': code, 'kind': kind, 'type': {'1': '国立', '2': '公立', '3': '私立'}.get(typ[:1], typ), 'name': name, 'addr': addr,
                        'pref': pref or '', 'city': city or '', 'll': c['ll'] if c else None})
    json.dump(coords, open(P('data', 'ts_coords.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    json.dump({'source': '文部科学省「学校コード一覧」（令和8年5月1日時点・暫定版）', 'source_url': 'https://www.mext.go.jp/b_menu/toukei/mext_01087.html',
               'schools': out}, open(P('data', 'tanki_senmon.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    k = {}
    for s in out: k[s['kind']] = k.get(s['kind'], 0) + 1
    print('短大・専門：', k, '／座標なし', len(miss), miss[:10])
    how = {}
    for v in coords.values(): how[v['how']] = how.get(v['how'], 0) + 1
    print('座標の精度：', how)
if __name__ == '__main__': main()
