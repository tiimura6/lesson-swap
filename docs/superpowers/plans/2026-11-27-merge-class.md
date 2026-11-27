# 合同化（別クラスの授業に合流）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 授業・時間割タブに「合同化」画面を追加し、単独授業を別クラスの同じ科目の授業に合流させる候補を出す。

**Architecture:** 判定は画面から切り離した純粋関数 `MergeEngine.find(me, env)` にし、`<script id="mergeEngine">` に置く（node でテストできるように、DOM も本体の変数も直接使わない）。本体 script が `window.ttMergeEnv()` で判定に必要な部品を渡す。画面・選択・印刷は別の `<script>`（「合同化タブ」）が持ち、今の `printCart` とは共有しない。

**Tech Stack:** 1ファイルの HTML/JavaScript（ビルドなし）、テストは node 22 の `assert`。

**Spec:** `docs/superpowers/specs/2026-11-27-merge-class-design.md`

## Global Constraints
- `index.html` 1ファイル構成を保つ。外部ライブラリを足さない。
- 今の授業交換画面の判定・表示、`printCart`・`window.ttPrintCart`・`ttRecords` の形式は変えない。
- 研修・会議・非常勤は除外せず色分けの警告にする（既存と同じクラス名 `training-conflict`・`parttime-row`）。
- 全候補に「進度・教科書・教室の定員を確認」を添える。
- 並び順：同じコマでの合流 → 警告なし → 警告あり。
- コミットの作者は `tiimura6 <tiimura6@icc.ac.jp>`。終わったら GitHub へプッシュ。

## Review Focus
1. 時間割データ未読み込みで合同化画面を開く → 「時間割を読み込んでください」と出て、エラーにならない。
2. 高校2年以上で、文理の指定が無い授業と文理別の授業が混在 → 文理が合わない授業を合流先にしない（どちらか空欄なら学級全体として合う）。
3. 自分のクラスの移動先コマに授業が複数（文理別で別の授業）ある → 移す授業が1つに決まらないので候補にしない。
4. 合流先の授業を複数の先生で持っている（同じ授業が先生ごとに行で重複）→ 候補は1件にまとめる。
5. 移す授業の担当者に教員A本人が含まれる → Aのコマ P は空くので、空き判定でAは除く。

---

### Task 1: 判定エンジン `MergeEngine.find`

**Files:**
- Modify: `index.html`（本体 script の閉じタグの直後に `<script id="mergeEngine">` を新規追加）
- Test: `tests/merge_engine.test.js`

**Interfaces:**
- Produces: `window.MergeEngine.find(me, env) -> Candidate[]`
  - `me`：教員Aの授業の1行（`{teacher, school, grade, class, course, day, period, subject}`）
  - `env`：`{ lessons, teacherHasSlot(t,d,p), hasAnyEvent(t,d,p), isParttimeTeacher(t), getAllTeachersForLesson(l), infoRoomConflict(moves) }`
  - `Candidate`：`{ kind: 'same'|'move', target: Lesson, targetTeachers: string[], moved: Lesson|null, movedTeachers: string[], eventWarn: boolean, parttime: boolean, infoWarn: boolean }`
  - `me` が複数クラスの合同授業（同じ先生・同じコマ・同じ科目で2クラス以上）のときは `[]`。

判定（spec の「判定」をそのまま）：
- 合流先 o：`o.school===me.school && o.grade===me.grade && o.subject===me.subject && o.class!==me.class`、高校2年以上は文理が等しいかどちらか空欄。o の担当者に A を含まない。同じ signature（school|day|period|grade|class|course|subject）は1件にまとめる。
- o が `me` と同じコマ → `kind:'same'`、`moved:null`。
- 別のコマY → Y にある自分のクラス（同じ学校・学年・組、文理は上と同じ規則）の行を集める。0件、または signature が2種類以上 → 除外。その授業（q）が複数クラスの合同（`getAllTeachersForLesson` の先生の誰かが、Y に同じ科目で別クラスを持つ）→ 除外。q の担当者（A を除く）の誰かが P で `teacherHasSlot` → 除外。
- 警告：`eventWarn` = q の担当者の誰かが P に `hasAnyEvent`（same は false）。`parttime` = o か q の担当者に非常勤。`infoWarn` = `infoRoomConflict([{lesson: me, toDay: Y, toPeriod: Yp}, {lesson: q, toDay: P.day, toPeriod: P.period}])`（same は `[]` を渡して false）。
- 並び：same → 警告なし → 警告あり、同順位は曜日・時限順。

- [ ] **Step 1: テストを書く** `tests/merge_engine.test.js`：`index.html` から `<script id="mergeEngine">…</script>` を正規表現で取り出し `vm.runInNewContext(code, {window:{}})`。小さな時間割（高校1年1組・2組、英語・数学）と偽の env で：
  - `test_same_slot`：1組英語(A, Mon1) と 2組英語(B, Mon1) → 1件、`kind==='same'`、`moved===null`
  - `test_move`：1組英語(A, Mon1)、2組英語(B, Tue2)、1組数学(C, Tue2)、C は Mon1 空き → 1件 `kind==='move'`、`moved.teacher==='C'`
  - `test_move_blocked`：同上で C が Mon1 に授業あり → 0件
  - `test_dedup_coteach`：2組英語(Tue2) を B・D の2行 → 1件、`targetTeachers` が `['B','D']`
  - `test_bunri`：高校2年、me は文系、合流先が理系 → 0件；合流先の文理が空欄 → 1件
  - `test_ambiguous_q`：高校2年、自クラスの Tue2 に文系・理系で別科目 → 0件
  - `test_self_in_q`：q の担当者が A（A は Mon1 に me を持つ）→ 除外されず1件
  - `test_joint_me`：me が A の 1組・2組合同 → `[]`
  - `test_sort`：same・警告あり move・警告なし move が並びの通り
- [ ] **Step 2: 実行して失敗を確認** `node tests/merge_engine.test.js` → `mergeEngine script not found` で失敗
- [ ] **Step 3: `MergeEngine.find` を実装**（`<script id="mergeEngine">`、`window.MergeEngine = { find }` だけを定義）
- [ ] **Step 4: 実行して通過を確認** `node tests/merge_engine.test.js` → `all passed`
- [ ] **Step 5: コミット** `git add index.html tests/merge_engine.test.js && git commit -m "合同化：判定エンジンを追加"`

### Task 2: 合同化画面（入力・一覧・専用の印刷）

**Files:**
- Modify: `index.html`
  - `views`（1977行付近）に `merge: 'viewMerge'`、`GROUP` に `merge: 'tt'`
  - `.ttg-seg` の2か所（1573行・1643行付近）に `<button type="button" role="tab" data-go="merge" aria-selected="false">🤝 合同化</button>`、`#viewClass` の後に同じ切替を持つ `<div id="viewMerge" class="view hidden">`
  - 本体 script の末尾近くに `window.ttMergeEnv = () => ({ lessons, teacherHasSlot, hasAnyEvent, isParttimeTeacher, getAllTeachersForLesson, infoRoomConflict })` と `window.ttTeacherList = () => [...]`（今の教員Aの選択肢と同じ並び）
  - 新しい `<script>`（「合同化タブ」）

**Interfaces:**
- Consumes: `window.MergeEngine.find`、`window.ttMergeEnv()`、`window.ttTeacherList()`
- Produces: なし（画面のみ）

画面：
- 教員A の選択 → その先生の単独授業の選択（`曜日 時限 学年-組 科目`、曜日・時限順）→ 候補表。
- 表の列：選択／種類（同じコマ・コマ移動）／合流先（コマ・クラス・科目・担当者）／移す授業（クラス・科目・担当者 ➔ 元のコマ。same は「移動なし」）／警告。行のクラスは警告に応じて `training-conflict`・`parttime-row`、情報教室は既存の `INFO_WARN_HTML` と同じ文言。
- 表の上に「※ 進度・教科書・教室の定員を確認してください（選択科目・習熟度別は時間割から判別できません）」。
- 候補0件：「合流できる授業はありません」。データ未読み込み：「時間割を読み込んでください」。
- 専用の選択（`Map`、キー `merge_<day><period>_<target signature>`）と「選んだ候補を印刷」ボタン。印刷は選んだ行だけの表を新しいウィンドウに書いて `print()`。教員や授業を選び直しても選択は残す。

- [ ] **Step 1: 画面を実装**（上の通り）
- [ ] **Step 2: 構文確認** `node -e` で `index.html` の全 `<script>` を取り出し `new Function(code)` が例外を出さないこと → `syntax ok`
- [ ] **Step 3: テスト再実行** `node tests/merge_engine.test.js` → `all passed`
- [ ] **Step 4: ブラウザ確認**（ローカルで `python3 -m http.server`、CSV を手動読み込み）：合同化に切り替わる／授業交換・クラス別時間割に戻れる／候補が出る／印刷画面に選んだ行だけ出る／授業交換の印刷カートの件数が変わらない
- [ ] **Step 5: コミット・プッシュ** `CLAUDE.md` の構成に「合同化」画面（`viewMerge`、`MergeEngine`、テスト `node tests/merge_engine.test.js`）を1項目追記して `git commit -m "合同化：画面と専用の印刷を追加" && git push`
