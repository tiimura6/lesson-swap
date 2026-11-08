#!/usr/bin/env python3
"""短大・専門の地図（名前と場所だけ）を組み立てる：data/tanki_senmon.json ＋ tools/ts_template.js → ts-module.js（飯村システム用）と ts.html（単体ページ）。
使い方：python3 tools/build_ts.py（先に python3 tools/ts_import.py で data/tanki_senmon.json を作る）"""
import json, os, re, sys, datetime
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
from build import project
P = lambda *a: os.path.join(HERE, *a)
d = json.load(open(P('data', 'tanki_senmon.json'), encoding='utf-8'))
prefs = json.load(open(P('data', 'map_prefs.json'), encoding='utf-8'))
S = []
for s in d['schools']:
    xy = None
    if s.get('ll'):
        x, y = project(s['ll'][0], s['ll'][1]); xy = [round(x, 2), round(y, 2)]
    S.append({'kind': s['kind'], 'type': s['type'], 'name': s['name'], 'addr': s['addr'], 'pref': s['pref'], 'xy': xy})
built = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M')
data = {'source': d.get('source', ''), 'source_url': d.get('source_url', ''), 'built': built, 'prefs': prefs, 'schools': S}
for k in ('rail', 'road'):
    f = P('data', 'map_' + k + '.json')
    if os.path.exists(f): data[k] = json.load(open(f, encoding='utf-8'))
t = open(P('tools', 'ts_template.js'), encoding='utf-8').read()
js = re.sub(r'/\*TSDATA\*/.*?/\*END_TSDATA\*/', lambda m: '/*TSDATA*/' + json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + '/*END_TSDATA*/', t, count=1, flags=re.S)
open(P('ts-module.js'), 'w', encoding='utf-8').write(js)
html = '''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>短大・専門学校マップ</title>
<style>body{margin:0;padding:16px;background:#f5f5f7}h1{font:700 20px -apple-system,BlinkMacSystemFont,"Hiragino Sans",sans-serif;margin:0 0 10px}</style></head>
<body><h1>短大・専門学校マップ</h1><div id="ts"></div><script src="ts-module.js"></script><script>TanSenModule.mount(document.getElementById("ts"));</script></body></html>'''
open(P('ts.html'), 'w', encoding='utf-8').write(html)
k = {}
for s in S: k[s['kind']] = k.get(s['kind'], 0) + 1
print('built ts-module.js (%dKB): %s / 位置なし %d' % (len(js.encode()) // 1024, k, sum(1 for s in S if not s['xy'])))
