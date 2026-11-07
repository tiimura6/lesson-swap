# 飯村システム（tiimura6/lesson-swap）

GitHub Pages: https://tiimura6.github.io/lesson-swap/

## 構成
- `index.html`：飯村システム本体。1ファイル構成。タブは ホーム／授業・時間割（中で 授業交換／クラス別時間割 を切り替え）／大学・進路／清掃当番作成／試験監督割当。1つのタブで複数画面を切り替える仕組みはタブ切替 script の `GROUP`（授業・時間割）と、大学・進路の script（Searchuniv）。
- `searchuniv/`：大学検索アプリ Searchuniv 一式（2026-11-07 に tiimura6/searchuniv から統合）。飯村システムの「🎓 大学・進路」タブの中身（中で 大学検索／進路面談／大学比較／出題内容 を切り替える）。
  - 画面とロジックの元：`searchuniv/tools/template.html`。データ：`searchuniv/data/*.json`。
  - `python3 searchuniv/tools/build.py` で `searchuniv/index.html`（単体ページ）・`searchuniv/su-module.js`（飯村システム用）・`detail.json` などを生成する。生成物は直接編集しない。
  - データ収集の手順は `searchuniv/PIPELINE.md`（毎時の定期実行「Searchuniv データ拡充」がこれに従う）。
  - Claude のアーティファクト版（slug 8174544a-a178-4a35-a835-6e4a0156f302）も `searchuniv/` の生成物から公開する（index.html・detail.json・world.json・muni.json）。

## Searchuniv を直すとき（不具合を防ぐ決まり）
1. `searchuniv/tools/template.html` か `searchuniv/tools/build.py` を直す。
2. `cd searchuniv && python3 tools/build.py && python3 tools/smoke_test.py` を実行し、「すべて合格」を確認してからコミットする。不合格なら生成物をコミットしない。
3. 飯村システム側の読み込み部分は `index.html` の「大学・進路タブ（…Searchuniv を直接組み込み）」の script。`SearchunivModule.apiVersion`（いまは 1）・`mount()` の引数・`Searchuniv` の関数名を変えるときは、両方を同時に直す。
4. Searchuniv の中は Shadow DOM。飯村システムの CSS・要素ID と混ざらない。Searchuniv 側で `location.hash` や `document.getElementById` を直接使わない（`NAV`・`ROOT` を使う）。モジュールの最上位の名前は `SU_` で始める。
5. 比較候補は localStorage の `searchuniv:cands`（両方で共通）。

## コミット
作者は `tiimura6 <tiimura6@icc.ac.jp>`。
