#!/usr/bin/env python3
"""国土数値情報「高速道路時系列データ(N06)」から、地図に重ねる高速道路の線を作る。
使い方: python3 tools/make_road.py <N06-xx_HighwaySection.geojson>
  例：https://github.com/shiwaku/ksj-change-map の data/N06-21_HighwaySection.geojson（令和3年）
出力: data/map_road.json（設置期間の終了年が 9999＝現存の区間だけ。地図の座標に投影して間引いた SVG の path 文字列）"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import ROOT
from make_rail import path

src = sys.argv[1]
g = json.load(open(src, encoding='utf-8'))
secs = [f['geometry']['coordinates'] for f in g['features'] if f['properties'].get('N06_003') == 9999 and f['geometry']['type'] == 'LineString']
yr = re.search(r'N06-(\d\d)', src); yr = ('20' + yr.group(1)) if yr else ''
res = {'hw': path(secs, 0.5), 'credit': '「国土数値情報（高速道路時系列データ）」（国土交通省）を加工して作成' + ('（%s年時点）' % yr if yr else '')}
json.dump(res, open(os.path.join(ROOT, 'data', 'map_road.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print({k: len(v) for k, v in res.items()})
