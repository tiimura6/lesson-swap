"""data/info.json の licenses（Kei-Net・各大学公式の「取得できる資格」から集めたもの）から、
資格名を取り出して表記をそろえる。build.py が「取得できる資格」のプルダウン候補を作るのに使う。"""
import re, unicodedata, collections
SCH = '幼稚園|小学校|中学校|高等学校|特別支援学校|中学|高校|中|高|小|幼'
CANON = {'高校教諭': '高等学校教諭', '中学教諭': '中学校教諭', '中教諭': '中学校教諭', '高教諭': '高等学校教諭', '小教諭': '小学校教諭', '幼教諭': '幼稚園教諭',
         '第1種衛生管理者': '第一種衛生管理者', '准学校心理士': '学校心理士', '教員': '教員免許', '教諭': '教員免許', 'はり師': 'はり師・きゅう師', 'きゅう師': 'はり師・きゅう師',
         '学校図書館司書教諭': '司書教諭', '衣料管理士1級': '衣料管理士', '操縦士': '事業用操縦士', '図書館司書': '司書', 'パイロット': '事業用操縦士'}
SUF = re.compile(r'(国家試験受験資格|国家試験|試験受験資格|受験資格|任用資格|免許状|免許|資格|一種|二種|専修|1種|2種|1級|2級|認定試験|養成課程|・)+$')
BAD = re.compile(r'[0-9]{2}|など|ほか|多数|各種|取得可|目指せ|受験可|対策|支援|講座|科目|単位|課程|コース|学科|学部|専攻|選択|希望|一部|免除|実務|カリキュラム|取得|申請|対応|登録|等$')
def _full(s):
    s = {'中': '中学校', '高': '高等学校', '小': '小学校', '幼': '幼稚園', '中学': '中学校', '高校': '高等学校'}.get(s, s)
    return s
def parts(s):
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'（[^）]*）|\([^)]*\)|【[^】]*】|\[[^\]]*\]', '', s)
    out = []
    for seg in re.split(r'[、,;；/／]|および|及び|または|又は', s):
        seg = seg.strip()
        if not seg: continue
        m = re.match(r'^((?:[一二]級|木造)(?:・(?:[一二]級|木造))+)建築士', seg)
        if m:
            out += [g + '建築士' for g in m.group(1).split('・')]; continue
        m = re.match(r'^((?:%s)(?:・(?:%s))+)(?:学校)?教諭' % (SCH, SCH), seg)
        if m:
            out += [_full(g) + '教諭' for g in m.group(1).split('・')]; continue
        segs = seg.split('・') if re.search(r'(師|士|員|者|官|司|事|技師)[^・]*・', seg) else [seg]
        for z in segs:
            z = SUF.sub('', z.strip())
            z = re.sub(r'^(国家試験|受験資格)', '', z).strip()
            z = re.sub(r'(教諭).*$', r'\1', z)          # 「中学校教諭一種・英語」→「中学校教諭」
            z = re.sub(r'の$', '', z)
            z = CANON.get(z, z)
            if 2 <= len(z) <= 14 and not BAD.search(z): out.append(z)
    return out
def license_names(info, min_univ=2):
    c = collections.Counter()
    for v in info.values():
        s = set()
        for l in v.get('licenses') or []: s.update(parts(l))
        c.update(s)
    # 2校以上にある名前と、1校だけでも資格名らしい（〜士・〜師・〜者など）名前を候補にする
    ok = re.compile(r'(士|師|者|員|主任者|アーキビスト|プランナー|パスポート試験)$')
    return [k for k, n in c.most_common() if n >= min_univ or ok.search(k)]
if __name__ == '__main__':
    import json, os
    info = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'data', 'info.json'), encoding='utf-8'))
    L = license_names(info); print(len(L)); print('、'.join(L))
