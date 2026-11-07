#!/usr/bin/env python3
"""先生から依頼された改良点が、いまも動いているかをまとめて確かめる（smoke_test.py より詳しい機能確認）。
使い方: cd searchuniv && python3 tools/feature_check.py   （飯村システム側の確認は ../index.html を使う）"""
import os, sys, json, threading, http.server, functools, socketserver
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # searchuniv/
TOP = os.path.dirname(HERE)                                           # lesson-swap/
res = []
def ck(group, name, ok, note=''):
    res.append((group, name, bool(ok), note)); print(('OK  ' if ok else 'NG  ') + group + '｜' + name + ('（' + str(note) + '）' if note != '' else ''))

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=TOP)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
U = 'http://127.0.0.1:%d/' % port
chrome = next((p for p in ('/usr/bin/google-chrome', '/usr/bin/chromium') if os.path.exists(p)), None)
tpl = open(os.path.join(HERE, 'tools', 'template.html'), encoding='utf-8').read()
pipe = open(os.path.join(HERE, 'PIPELINE.md'), encoding='utf-8').read()

with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': chrome} if chrome else {}), args=['--no-sandbox'])
    pg = b.new_page(viewport={'width': 1300, 'height': 900}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    J = pg.evaluate
    pg.goto(U + 'searchuniv/index.html'); pg.wait_for_function('document.querySelector("#updline").textContent.length>0'); pg.wait_for_timeout(2500)
    def search(q):
        J('(q)=>{const e=document.getElementById("mq"); e.value=q; document.getElementById("mgo").click()}', q); pg.wait_for_timeout(350)
        return J('document.querySelectorAll(".ritem").length')

    G = '検索・地図'
    J('(()=>{const s=document.getElementById("f-kyoka"); s.value="le3"; s.dispatchEvent(new Event("change"))})()'); pg.wait_for_timeout(400)
    ck(G, '共テ教科数の絞り込みは学部・方式ごとに表示（勘違い防止）', J('document.querySelectorAll(".ritem .kyf").length') == J('document.querySelectorAll(".ritem").length') > 0 and J('document.querySelectorAll(".ritem .kypart").length') > 0)
    J('(()=>{const s=document.getElementById("f-kyoka"); s.value=""; s.dispatchEvent(new Event("change"))})()'); pg.wait_for_timeout(300)
    ck(G, '設置区分のチェックが最初から全部オン', J('[...document.querySelectorAll(".fk")].every(e=>e.checked)'), J('document.querySelectorAll(".fk").length'))
    ck(G, '共テ教科数・R:L・系統・入試方式・英語外部試験の絞り込み', all(J('!!document.getElementById("%s")' % i) for i in ('f-kyoka', 'f-rl', 'f-kei', 'f-meth', 'f-eng')))
    n = search('獣医'); vis = J('[...document.querySelectorAll("#jmap .dot")].filter(c=>getComputedStyle(c).display!=="none").length')
    ck(G, '「獣医」で関係する大学だけ・地図も同じ数だけ表示', 5 <= n <= 30 and vis == n, '%d件・地図%d点' % (n, vis))
    J('document.getElementById("mby").value="name"; document.getElementById("mby").dispatchEvent(new Event("change"))')
    nn = search('茨城'); J('document.getElementById("mby").value="pref"; document.getElementById("mby").dispatchEvent(new Event("change"))'); np_ = search('茨城')
    J('document.getElementById("mby").value=""; document.getElementById("mby").dispatchEvent(new Event("change"))')
    ck(G, '何で探すか（大学名・学部・地域・資格・研究・奨学金）を指定できる', J('document.querySelectorAll("#mby option").length') >= 7 and nn != np_, '大学名%d件・地域%d件' % (nn, np_))
    ck(G, '学科・専攻の言葉で探せる（例：理学療法）', search('理学療法') > 0, J('document.querySelectorAll(".ritem").length'))
    ck(G, '地方で探せる（例：東北）', search('東北') > 3)
    search('看護'); J('(()=>{const s=document.getElementById("msort"); s.value="hd"; s.dispatchEvent(new Event("change"))})()'); pg.wait_for_timeout(300)
    hs = J('[...document.querySelectorAll(".ritem")].map(r=>{const m=r.textContent.match(/偏差値([0-9.]+)/); return m?+m[1]:null}).filter(v=>v!=null)')
    ck(G, '偏差値の高い順に並べ替え', len(hs) > 2 and hs == sorted(hs, reverse=True), hs[:5])
    pg.locator('.ritem').first.click(); pg.wait_for_timeout(500)
    ck(G, '大学を選ぶとポップアップ表示', J('!document.getElementById("uov").hidden'))
    ck(G, '比較候補ボタンが分かりやすい表示', '比較に追加' in J('document.querySelector("#mpanel .cbtn").textContent'))
    ck(G, '出題内容へ飛ぶボタン', J('!!document.querySelector("#mpanel [data-trend]")'))
    ck(G, '情報の充実度の表示', J('!!document.querySelector("#mpanel .full")'), J('(document.querySelector("#mpanel .full")||{}).textContent'))
    ck(G, '誤りを報告する欄', J('!!document.querySelector("#mpanel .rep")'))
    J('document.getElementById("uclose").click()'); pg.wait_for_timeout(200)
    J('Searchuniv.selectUniv("東北大学")'); pg.wait_for_timeout(700)
    others = J('[...document.querySelectorAll("#labels .ulbl")].filter(t=>getComputedStyle(t).display!=="none"&&t.textContent!=="東北大学").length')
    ck(G, '選択中は他の大学名を地図に出さない', others == 0, others)
    r = J('(()=>{const c=document.querySelector("#jmap .dot"); const b=c.getBoundingClientRect(); return Math.round(b.width)})()')
    ck(G, '大学の丸が9px以上（クリックしやすい）', r >= 9 or J('dotR' in 'x') , '%dpx' % r)
    ck(G, '市町村の表示なし', 'const SHOW_MUNI=false' in tpl)
    ck(G, '空いた所をクリックで選択解除・ホバーで大学名', 'clearSelection' in tpl and 'ctip' in tpl)
    ck(G, '最新ニュースをタイトルと同じ行に流して表示', J('document.getElementById("nticker").closest(".hrow") && !document.getElementById("nticker").hidden && document.querySelectorAll("#nt-track .nt-i").length>0 && getComputedStyle(document.getElementById("nt-track")).animationName==="ntscroll"'))
    ck(G, '更新日時を検索欄の下に表示', '更新' in J('document.getElementById("updline").textContent'), J('document.getElementById("updline").textContent')[:30])
    ck(G, '詳しいデータは後から読み込む（ページを軽く）', J('typeof Searchuniv')=='object' and 'fetch(BASE+"detail.json")' in tpl)

    G = '大学の情報（ポップアップ）'
    t = J('document.getElementById("mpanel").innerText')
    for k, w in (('学部・学科（専攻まで）', '学部・学科'), ('学部別の難易度', '学部・学科別の難易度'), ('入試日程', '入試日程'), ('費用と奨学金', '費用と奨学金'),
                 ('出典と確認日', '出典と確認日'), ('倍率の推移（入試結果）', '倍率'), ('英語外部試験', '英語'), ('最新ニュース', 'ニュース')):
        ck(G, k, w in t)
    J('document.getElementById("uclose").click(); Searchuniv.selectUniv("京都大学")'); pg.wait_for_timeout(700)
    J('document.querySelector("#mpanel .wmapwrap") && document.querySelector("#mpanel .wmapwrap").click()'); pg.wait_for_timeout(400)
    sch = J('(document.querySelector("#mpanel .sch")||{innerText:""}).innerText')
    ck(G, '入試日程（出願・試験日・合格発表・手続締切）を上の方に表示', all(w in sch for w in ('出願', '試験日', '合格発表', '手続締切')) and J('(()=>{const a=document.querySelector("#mpanel .sch"), g=document.querySelector("#mpanel .guide"); return !!a && (!g || (a.compareDocumentPosition(g) & 4))})()'))
    J('document.getElementById("uclose").click(); Searchuniv.selectUniv("茨城キリスト教大学")'); pg.wait_for_timeout(700)
    ck(G, '学部・方式ごとの入試科目（私立の多様な方式）', '学部・方式ごとの入試科目' in J('document.getElementById("mpanel").innerText') and J('!!document.querySelector("#mpanel .subj-f")'))
    ck(G, '奨学金を学部・学科ごとに表示する仕組み', 'function scholarBlock' in tpl and 'scholar' in open(os.path.join(HERE,'tools','build.py'),encoding='utf-8').read())
    ck(G, '海外協定校の世界地図（拡大できる）', J('!!document.getElementById("wmodal") && !document.getElementById("wmodal").hidden'), '京都大学')
    pg.keyboard.press('Escape')
    ck(G, 'オープンキャンパス欄（データがある学校）', 'ocBlock' in tpl, 'データあり %d校' % sum(1 for v in json.load(open(os.path.join(HERE, 'data', 'info.json'), encoding='utf-8')).values() if v.get('oc')))
    sh = J('''(()=>{ for(const n of ["東北大学","早稲田大学","明治大学","法政大学","中央大学","日本大学","東洋大学","駒澤大学","専修大学"]){ } return document.body.innerHTML.includes("非公開（在籍高校に届く要項で確認）")||true })()''')
    ck(G, '指定校は情報がなければ「非公開」', 'hiddenShitei' in tpl and '非公開（在籍高校に届く要項で確認）' in tpl)
    ck(G, 'フラッシュカード機能は削除済み', 'v-cards' not in tpl and 'flip(' not in tpl)
    J('document.getElementById("uclose").click()')

    G = '面談'
    J('Searchuniv.showView("ai")'); pg.wait_for_timeout(400)
    ck(G, '生徒名の入力欄なし（個人を特定しない）', not J('!!document.querySelector("#v-ai input[id*=name]")') and '個人名は入れず' in J('document.getElementById("v-ai").innerText'))
    ck(G, '河合・進研の模試を選べる', J('[...document.querySelectorAll("#ai-moshi option")].map(o=>o.textContent).join()').count('模試') >= 2)
    J('document.getElementById("ai-study").value="心理"; document.getElementById("ai-level").value="55"; document.getElementById("ai-go").click()'); pg.wait_for_timeout(600)
    bands = J('[...new Set([...document.querySelectorAll("#ai-out .band")].map(e=>e.textContent))]')
    ck(G, '希望の学問の中で挑戦〜安全を表示', any('挑戦' in x for x in bands) and any('安全' in x for x in bands), bands)
    ck(G, '国公立・私立などで絞り込み・並べ替え', J('document.querySelectorAll("#ai-out .mk").length') >= 3 and J('!!document.getElementById("msort2")'))
    ck(G, 'AIを使わず規則で判定', 'AIは使わない' in tpl or 'AI不使用' in tpl)
    J('document.getElementById("st-u1").value="東北大学"; document.getElementById("st-u2").value="早稲田大学"; document.getElementById("st-u3").value="明治大学"; document.getElementById("st-go").click()'); pg.wait_for_timeout(700)
    st = J('document.getElementById("st-out").innerText')
    ck(G, '第1〜3志望から受験戦略案', '第1志望' in st and '第3志望' in st)
    ck(G, '安全校の自動候補', '安全校の候補' in st)
    ck(G, '科目の重なり（負担軽減・二次の内容被り）', '対策の重なり' in st)
    ck(G, '受験費用の目安', '受験費用の目安' in st)
    ck(G, '「滑り止め」を使わず「安全校」に統一', '滑り止め' not in tpl and '滑り止め' not in J('document.getElementById("v-ai").innerText'))
    ck(G, '日程の衝突・連戦・移動の警告', '日連続で試験' in tpl and '前泊が必要' in tpl)
    J('document.getElementById("ktbox").open=true; document.getElementById("kt-score").value="74"; document.getElementById("kt-go").click()'); pg.wait_for_timeout(600)
    kt = J('document.getElementById("kt-out").innerText')
    ck(G, '共テ後の出願判断（ボーダー・足切り・前後期の組み合わせ）', 'ボーダー' in kt and '二段階選抜' in kt and '組み合わせ案' in kt)

    J('document.getElementById("stu-c").value="3A"; document.getElementById("stu-n").value="7"; document.getElementById("ai-study").value="教育"; document.getElementById("stu-save").click(); document.getElementById("stu-new").click(); document.getElementById("stu-c").value="3a"; document.getElementById("stu-n").value="７"; document.getElementById("stu-load").click()')
    ck(G, 'クラス・出席番号で記録を保存・呼び出し', J('document.getElementById("ai-study").value') == '教育')
    ck(G, 'CSVの書き出し・読み込み', J('!!document.getElementById("stu-exp") && !!document.getElementById("stu-imp")'))
    J('document.getElementById("st-u1").value="茨城キリスト教大学"; document.getElementById("st-u1").dispatchEvent(new Event("change"))')
    ck(G, '生徒の志望校の出願締切を表示', 'あと' in J('document.getElementById("stu-dl").innerText'))
    G = '比較'
    J('localStorage.setItem("searchuniv:cands", JSON.stringify(["東北大学","早稲田大学"]))'); pg.reload(); pg.wait_for_timeout(2500)
    J('Searchuniv.showView("plan")'); pg.wait_for_timeout(600)
    pl = J('document.getElementById("v-plan").innerText')
    for w in ('一般', '共テ利用', '推薦', '総合型', '共通テストの科目', '英語外部試験', '倍率'):
        ck(G, '比較の行：' + w, w in pl)
    ck(G, '倍率の年度比較のグラフ', 'ratioChart' in tpl)
    ck(G, '比較候補の出願締切を表示', J('!!document.querySelector("#plan-out .dlbox")'))

    G = '出題内容'
    J('Searchuniv.openTrend("京都大学")'); pg.wait_for_timeout(600)
    ck(G, '出題内容タブ（大学ごと・教科ごと）', '京都大学' in J('document.getElementById("trend-out").innerText') and J('!!document.getElementById("tsub")'))
    ck(G, 'エラーなし（単体ページ）', not errs, errs[:2])

    G = '飯村システムへの統合'
    pg2 = b.new_page(viewport={'width': 1300, 'height': 900}); e2 = []
    pg2.on('pageerror', lambda e: e2.append(str(e)))
    pg2.goto(U + 'index.html'); pg2.wait_for_timeout(1500)
    tabs = pg2.inner_text('#viewTabs').replace('\n', '｜')
    ck(G, 'タブ：授業・時間割と大学・進路にまとめた', '授業・時間割' in tabs and '大学・進路' in tabs and '進路面談' not in tabs and 'クラス別時間割' not in tabs, tabs)
    pg2.evaluate('document.querySelector("#viewTabs [data-view=univ]").click()'); pg2.wait_for_timeout(3000)
    ck(G, 'iframe ではなく直接組み込み', pg2.evaluate('!document.querySelector("#viewUniv iframe") && !!document.getElementById("univHost").shadowRoot'))
    ck(G, '大学・進路の中で4画面を切り替え', pg2.evaluate('document.querySelectorAll("#univSeg [data-sub]").length') == 4)
    ck(G, 'エラーなし（飯村システム）', not e2, e2[:2])

    G = '自動収集・運用'
    ck(G, 'パスナビも巡回', 'パスナビ' in pipe)
    ck(G, '出典の信頼度（大学HP＞Kei-Net・パスナビ、複数一致）', '出典の信頼度' in pipe)
    ck(G, '全校がそろってから再確認を始める', '`add` が空になったら' in pipe)
    ck(G, '誤り報告を毎回最初に処理', '誤り報告' in pipe)
    ck(G, '公開前の自動テストが必須', 'smoke_test.py' in pipe)
    b.close()
srv.shutdown()
ng = [r for r in res if not r[2]]
print('\n%d項目中 %d項目OK' % (len(res), len(res) - len(ng)) + ('' if not ng else '｜NG：' + '、'.join(r[1] for r in ng)))
sys.exit(1 if ng else 0)
