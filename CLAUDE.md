# 飯村システム（tiimura6/lesson-swap）

GitHub Pages: https://tiimura6.github.io/lesson-swap/

## 構成
- `index.html`：飯村システム本体。1ファイル構成。タブは ホーム／授業・時間割（中で 授業交換／クラス別時間割 を切り替え）／大学・進路／清掃当番作成／試験監督割当。1つのタブで複数画面を切り替える仕組みはタブ切替 script の `GROUP`（授業・時間割）と、大学・進路の script（Searchuniv）。
- `searchuniv/`：大学検索アプリ Searchuniv 一式（2026-11-07 に tiimura6/searchuniv から統合。旧リポジトリは 2026-11-08 に削除）。飯村システムの「🎓 大学・進路」タブの中身（中で 大学検索／進路面談／大学比較／出題内容 を切り替える）。
  - 画面とロジックの元：`searchuniv/tools/template.html`。データ：`searchuniv/data/*.json`。
  - `python3 searchuniv/tools/build.py` で `searchuniv/index.html`（単体ページ）・`searchuniv/su-module.js`（飯村システム用）・`detail.json` などを生成する。生成物は直接編集しない。
  - データ収集の手順は `searchuniv/PIPELINE.md`（毎時の定期実行「Searchuniv データ拡充」がこれに従う）。
  - Claude のアーティファクト版（slug 8174544a-a178-4a35-a835-6e4a0156f302）も `searchuniv/` の生成物から公開する（index.html・detail.json・world.json・muni.json）。

- 「🏫 短大・専門」タブ（`#ts`、`index.html` の「短大・専門タブ」script）：短期大学・専門学校の名前と場所だけの地図。`searchuniv/ts-module.js`（`TanSenModule.mount(host)`、Shadow DOM）を読み込む。元は `searchuniv/tools/ts_template.js`、データは `searchuniv/data/ts_raw/*.txt`（文部科学省「学校コード一覧」）→ `python3 tools/ts_import.py`（座標）→ `python3 tools/build_ts.py`。専門学校は定期実行が少しずつ読み取る（PIPELINE.md）。アーティファクト版「短大・専門学校マップ」（slug 54b601c1-ec32-4c21-9a37-793f9e5745ab）は ts.html と ts-module.js から公開する。

## Searchuniv を直すとき（不具合を防ぐ決まり）
1. `searchuniv/tools/template.html` か `searchuniv/tools/build.py` を直す。
2. `cd searchuniv && python3 tools/build.py && python3 tools/smoke_test.py` を実行し、「すべて合格」を確認してからコミットする。不合格なら生成物をコミットしない。画面や機能を変えたときは `python3 tools/feature_check.py`（先生から依頼された改良点59項目の確認）も通す。
3. 飯村システム側の読み込み部分は `index.html` の「大学・進路タブ（…Searchuniv を直接組み込み）」の script。`SearchunivModule.apiVersion`（いまは 1）・`mount()` の引数・`Searchuniv` の関数名を変えるときは、両方を同時に直す。
4. Searchuniv の中は Shadow DOM。飯村システムの CSS・要素ID と混ざらない。Searchuniv 側で `location.hash` や `document.getElementById` を直接使わない（`NAV`・`ROOT` を使う）。モジュールの最上位の名前は `SU_` で始める。
5. 大学の画面：学部が2つ以上ある大学の「大学全体」は、最初に「学部・学科の要点」（各学部・学科タブの要点の一覧）、続いて 指導のポイント／大学の基本情報／入試（全学部共通）／学費・奨学金（全学部共通）／オープンキャンパス・出典。学部名を含む日程・方式・科目・学科別難易度・学部別学費などは `commonRecord()` で学部タブへ回す（学部タブは `facRecord()`）。
6. 日付は `withYear()` で年を付けて表示し、入試年度（`CUR_FY`。4月で切り替わる）より古い年度の入試情報は `staleYear()` でオレンジ色＋「更新待ち」の印。自動収集で year が新しくなると戻る。動作確認は localStorage `searchuniv:today` に日付を入れる。
7. 進路面談の志望校は 大学（st-uN）＞学部（st-fN）＞学科（st-dN）＞入試区分・方式（st-mN、値は「区分|方式名」）。`stFill()` が選択肢を作り、`stRoutes(name,fac,dep,meth)` がその募集単位の方式だけで戦略を作る。
8. 「共通テスト」画面（Searchuniv の view `kyotsu`、飯村システムの #univ-kyotsu）は `searchuniv/data/kyotsu_test.json`（大学入試センターの資料）から作る。
9. 比較候補は localStorage の `searchuniv:cands`（両方で共通）。進路面談の生徒の記録は `searchuniv:students:<操作者名>`（クラス＋出席番号がキー、個人名は持たない）。CSV の列名は「表示名[項目ID]」で、読み込みは[]の中で照合する。

10. 検索画面の項目（2026-11-11 先生の依頼でパスナビの検索項目にならった）：学びたい内容 `#q-learn`（文章。`learnGroups()` が言葉を概念に分け、`LEARN_SYN`＋`SYN` で学部・学科名／研究分野／特色と照らす `xLearn()`）／学部・学科 `#q-fac`／学問 `#q-study`／将来の職業 `#q-job`（対応表は `JOBS`）／取得できる資格 `#q-lic`／都道府県・地域 `#q-area`／学部系統 `#f-kei`／偏差値 `#f-hmin`〜`#f-hmax`／共テ得点率 `#f-kt`、「詳しい条件」に 入試方式・共テ教科数・一般入試の試験日 `#f-date`・英語外部試験・R:L・倍率 `#f-ratio`・学費 `#f-fee`・情報が載っている学校だけ `#f-theme`。入力した項目すべてに合う学校だけを `passFilters()`（`xHits()`・`passExtra()`）で残す。偏差値・共テ得点率は学部・学科別（fdiff）があればその値（学部などを入れたときはその言葉を含む行）、無ければ大学全体の中央値で判定する。一覧は最初から偏差値の高い順（`#msort` の既定 hd、学部などを入れたときは `listHen()` の学科の偏差値で並べ「（学科）」と表示）。
11. 興味のテーマ（2026-11-11 先生の依頼「いろいろな検索語に対応し、関連して学べることを提案」）：辞書は `searchuniv/data/topics.json`（say＝生徒が使う言葉、f＝関連して学べる分野 {n,w,why}、g＝将来の適性学問診断に使う系統）。build.py が `TOPICS` として埋め込む。大学名・キーワード欄 `#mq` と「学びたい内容」でテーマの言葉に当たると、`topicFieldHits()`（学部・学科名と研究分野に分野の言葉があるか。`美術+教育` は両方を含むときだけ）で関連分野を学べる学校も候補にし、一覧の上に「〇〇に関心がある人は、こんな分野でも学べます」（分野ボタン＝`TSEL` で絞り込み）、各行に「関連」を出す。1分野だけ当たる学校は、学部名などにテーマの言葉そのものがあるときだけ候補にする。何も見つからないときは `fuzzyUnivs()`（説明文の文字の並び）→ テーマ一覧を提案。検索欄の下の「興味のテーマから探す」と、大学の基本情報の「関連して学べるテーマ」（`topicsOfUniv()`、2分野以上）からも同じ検索に入れる。テーマを足すときは topics.json だけ直せばよい。
12. 「取得できる資格」の候補は、各大学の licenses（公式・Kei-Net の「取得できる資格」）から `tools/lic_names.py` が資格名をそろえて作る（build.py の `LICN`。2校以上、または1校でも「〜士・〜師」など資格名らしいもの）。データ収集で資格が増えると候補も自動で増える。`xLic()` は表記ゆれ（「高等学校教諭」と「教員免許（中・高）」など）を `LICN.by` で照らす。「将来の職業」の候補は template.html の `JOBS`（呼び名 a・資格 lic・学部 fac・進路 car・校名 nm の正規表現）。

## 操作者
- タイトル横の「👤 操作者」で選ぶ（localStorage `ttOperator`）。PINは `opPins`／GAS。
- 時間割に名前が無い人は、一覧の最後の「＋ 新規作成」（または検索欄で該当なしのまま Enter）で名前を決める。作成した名前はこの端末の localStorage `opCustomNames` に保存し、一覧の最後に並ぶ（新規作成の画面から削除できる）。作成後は通常どおり初回PINを設定する。
- 作成・削除は操作ログ（`操作者を新規作成`／`新規作成した操作者を削除`、内容＝名前）で GAS の log シートに送られる。スプレッドシート「飯村システム」の「新規作成した操作者」シートが log・pins シートから数式で一覧にする（名前・作成日時・作成した人・端末・Googleアカウント・PIN設定日時・最終操作日時・操作回数・状態）。この操作名を変えるときは、そのシートの数式も直す。
- 他の端末で作成された名前は、GAS の `action=op_names`（`gas/op_names.gs` を GAS に追加・再デプロイしたもの）から読み、localStorage `opSharedNames` に覚えて一覧に出す。GAS が古い版なら何もしない。

## 保存した記録（授業交換・清掃当番・試験監督）
- `index.html` の「保存した記録」script（`window.ttRecords`）。localStorage の `ttRecords:<操作者名>` に、名前付きの記録を種類ごとに最大60件残す。
- 授業交換は印刷用の選択（`window.ttPrintCart`）を保存・復元。清掃当番は `seisou_touban_app_v6_proposal`、試験監督は `examProctor_v1` の中身を丸ごと保存し、開くときはそのキーに戻して再読み込みする。これらのキーや保存形式を変えるときは、古い記録が開けるか確かめる。

## 用語
- 進路面談では「滑り止め」を使わず「安全校」に統一する。

## コミット
作者は `tiimura6 <tiimura6@icc.ac.jp>`。
