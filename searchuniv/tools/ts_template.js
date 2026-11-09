/* 短大・専門（名前と場所だけの地図）。tools/build_ts.py が ts-module.js と ts.html を作る。直接編集しない元ファイル。
   飯村システムの「🏫 短大・専門」タブが TanSenModule.mount(host) で Shadow DOM の中に表示する。 */
(function(){
const DATA = /*TSDATA*/{}/*END_TSDATA*/;
const CSS = `
:host{all:initial}
.ts{font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP","Meiryo",sans-serif;color:#1d1d1f;font-size:14px;-webkit-font-smoothing:antialiased}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 8px}
.bar input[type=search]{flex:1;min-width:12em;border:1px solid #d2d2d7;border-radius:10px;padding:8px 12px;font:inherit;font-size:15px;background:#fff}
.bar select{border:1px solid #d2d2d7;border-radius:10px;padding:7px 10px;font:inherit;background:#fff}
.seg{display:inline-flex;gap:2px;padding:3px;background:#ececf0;border-radius:10px}
.seg button{border:none;background:transparent;border-radius:8px;padding:5px 12px;font:600 13px inherit;font-family:inherit;cursor:pointer;color:#1d1d1f}
.seg button.on{background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.14)}
.cnt{font-size:12.5px;color:#6e6e73}
.wrap{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(260px,1fr);gap:12px}
@media (max-width:820px){.wrap{grid-template-columns:1fr}}
.mapbox{position:relative;background:#eef3f8;border-radius:14px;box-shadow:0 0 0 1px #e5e5ea;overflow:hidden;touch-action:none}
svg{display:block;width:100%;height:auto;aspect-ratio:490/450;cursor:grab;user-select:none}
svg.drag{cursor:grabbing}
.pref path{fill:#fff;stroke:#c7cfd9;stroke-width:.6;vector-effect:non-scaling-stroke}
.dot{stroke:#fff;vector-effect:non-scaling-stroke;stroke-width:1;cursor:pointer}
.dot.t{fill:#d4553a}.dot.s{fill:#2a7f62}
.dot.hl{stroke:#1d1d1f;stroke-width:2.5}
.lbl{font-size:11px;paint-order:stroke;stroke:#fff;stroke-width:3px;stroke-linejoin:round;fill:#1d1d1f;pointer-events:none}
.lbl.hl{font-weight:700;fill:#0071e3}
.rail path{fill:none;stroke-linejoin:round;stroke-linecap:round;vector-effect:non-scaling-stroke;pointer-events:none}
.rail .r-hw{stroke:#2e7d32;stroke-width:1.8px;stroke-opacity:.85}.rail .r-shin{stroke:#c62828;stroke-width:2.2px}.rail .r-jr{stroke:#1e5aa8;stroke-width:1.3px}.rail .r-other{stroke:#8fb3dc;stroke-width:.9px}
.layers{position:absolute;left:8px;top:8px;display:flex;gap:4px}
.layers button{border:none;border-radius:8px;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.2);font:600 12px inherit;font-family:inherit;padding:6px 10px;cursor:pointer;color:#1d1d1f}
.layers button[aria-pressed="true"]{background:#1f4e79;color:#fff}
.lkey{display:inline-flex;gap:8px;align-items:center}.lkey i{display:inline-block;width:14px;height:0;border-top:3px solid;margin-right:3px;vertical-align:3px}
.zoom{position:absolute;right:8px;top:8px;display:flex;flex-direction:column;gap:4px}
.zoom button{width:32px;height:32px;border:none;border-radius:8px;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.2);font-size:18px;cursor:pointer}
.legend{position:absolute;left:8px;bottom:8px;background:rgba(255,255,255,.9);border-radius:8px;padding:4px 8px;font-size:12px;display:flex;gap:10px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:4px;vertical-align:-1px}
.list{background:#fff;border-radius:14px;box-shadow:0 0 0 1px #e5e5ea;max-height:640px;overflow:auto}
.list .it{padding:8px 12px;border-bottom:1px solid #f2f2f7;cursor:pointer}
.list .it:hover,.list .it.on{background:#f0f6ff}
.list .nm{font-weight:700}
.tag{display:inline-block;font-size:11px;font-weight:700;color:#fff;border-radius:6px;padding:0 6px;margin-right:6px;vertical-align:1px}
.tag.t{background:#d4553a}.tag.s{background:#2a7f62}
.sub{font-size:12px;color:#6e6e73}
.more{padding:10px 12px;font-size:12.5px;color:#6e6e73}
.card{margin-top:8px;background:#fff;border-radius:14px;box-shadow:0 0 0 1px #e5e5ea;padding:12px 14px}
.card[hidden]{display:none}
.card h3{margin:0 0 4px;font-size:16px}
.card a{color:#0071e3;text-decoration:none;margin-right:12px;font-size:13px}
.note{font-size:12px;color:#6e6e73;margin-top:8px;line-height:1.6}
.note a{color:#0071e3}
`;
const ESC = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
const HOME = [170, 0, 490, 450];
const PREFS = ['北海道','青森県','岩手県','宮城県','秋田県','山形県','福島県','茨城県','栃木県','群馬県','埼玉県','千葉県','東京都','神奈川県','新潟県','富山県','石川県','福井県','山梨県','長野県','岐阜県','静岡県','愛知県','三重県','滋賀県','京都府','大阪府','兵庫県','奈良県','和歌山県','鳥取県','島根県','岡山県','広島県','山口県','徳島県','香川県','愛媛県','高知県','福岡県','佐賀県','長崎県','熊本県','大分県','宮崎県','鹿児島県','沖縄県'];

function mount(host, opt){
  opt = opt || {};
  const root = host.shadowRoot || host.attachShadow({ mode: 'open' });
  const S = (DATA.schools || []).map((x, i) => Object.assign({ i }, x));
  const nT = S.filter(s => s.kind === '短大').length, nS = S.filter(s => s.kind === '専門').length;
  root.innerHTML = '<style>' + CSS + '</style><div class="ts">' +
    '<div class="bar"><input type="search" id="q" placeholder="🔍 学校名・市区町村で探す（例：看護、仙台）" aria-label="学校名で探す">' +
    '<span class="seg" id="kind"><button type="button" data-k="" class="on">すべて</button><button type="button" data-k="短大">短大（' + nT + '）</button><button type="button" data-k="専門">専門学校（' + nS + '）</button></span>' +
    '<select id="pref" aria-label="都道府県"><option value="">全国</option>' + PREFS.map(p => '<option>' + p + '</option>').join('') + '</select>' +
    '<span class="cnt" id="cnt"></span></div>' +
    '<div class="wrap"><div><div class="mapbox"><svg id="map" viewBox="' + HOME.join(' ') + '" role="img" aria-label="短大・専門学校の地図"><g class="pref" id="prefs"></g><g class="rail" id="rail"></g><g id="dots"></g><g id="lbls"></g></svg>' +
    '<div class="layers"><button type="button" id="tgrail" aria-pressed="false">🚃 鉄道</button><button type="button" id="tgroad" aria-pressed="false">🛣 高速道路</button></div>' +
    '<div class="zoom"><button type="button" id="zin" aria-label="拡大">＋</button><button type="button" id="zout" aria-label="縮小">－</button><button type="button" id="zhome" aria-label="全国を表示" style="font-size:13px">全</button></div>' +
    '<div class="legend"><span><i style="background:#d4553a"></i>短大</span><span><i style="background:#2a7f62"></i>専門学校</span><span class="lkey" id="rkey"></span></div></div>' +
    '<div class="card" id="card" hidden></div>' +
    '<div class="note">学校名と所在地の出典：' + ESC(DATA.source || '') + '。予備校・高等課程だけの専修学校は載せていません。地図の位置は所在地の町・市区町村の代表地点の目安です。' +
    (nS ? '' : '専門学校は自動収集で順に追加しています。') + '入試・学費などは各学校の公式サイトで確認してください。<a href="' + ESC(DATA.source_url || '#') + '" target="_blank" rel="noopener">学校コード一覧 ↗</a><span id="rcred"></span></div></div>' +
    '<div class="list" id="list"></div></div></div>';
  const $ = id => root.getElementById(id);
  const svg = $('map');
  $('prefs').innerHTML = (DATA.prefs || []).map(p => '<path d="' + p.d + '"/>').join('');
  let vb = HOME.slice(), kind = '', sel = null;
  // 鉄道・高速道路（大学検索の地図と同じデータ。表示する・しないは大学検索と共通でこの端末に覚える）
  const LY = { rail: false, road: false };
  try { LY.rail = localStorage.getItem('searchuniv:rail') === '1'; LY.road = localStorage.getItem('searchuniv:road') === '1'; } catch(e){}
  function drawRail(){
    const R = DATA.rail, H = DATA.road, P = [], key = [], cred = [];
    if(H && LY.road){ P.push('<path class="r-hw" d="' + H.hw + '"/>'); key.push('<span><i style="border-color:#2e7d32"></i>高速道路</span>'); cred.push(H.credit); }
    if(R && LY.rail){ ['other', 'jr', 'shin'].filter(k => R[k]).forEach(k => P.push('<path class="r-' + k + '" d="' + R[k] + '"/>')); key.push('<span><i style="border-color:#c62828"></i>新幹線</span><span><i style="border-color:#1e5aa8"></i>JR</span><span><i style="border-color:#8fb3dc"></i>私鉄など</span>'); cred.push(R.credit); }
    $('rail').innerHTML = P.join('');
    [['tgrail', R, 'rail'], ['tgroad', H, 'road']].forEach(([id, D, k]) => { const b = $(id); b.hidden = !D; b.setAttribute('aria-pressed', LY[k] ? 'true' : 'false'); });
    $('rkey').innerHTML = key.join(''); $('rcred').textContent = cred.length ? '　鉄道・道路の出典：' + cred.join('／') : '';
  }
  [['tgrail', 'rail'], ['tgroad', 'road']].forEach(([id, k]) => { $(id).onclick = () => { LY[k] = !LY[k]; try { localStorage.setItem('searchuniv:' + k, LY[k] ? '1' : '0'); } catch(e){} drawRail(); }; });
  drawRail();
  const pts = S.filter(s => s.xy);
  const dotsG = $('dots');
  dotsG.innerHTML = pts.map(s => '<circle class="dot ' + (s.kind === '短大' ? 't' : 's') + '" data-i="' + s.i + '" cx="' + s.xy[0] + '" cy="' + s.xy[1] + '" r="2"><title>' + ESC(s.name) + '</title></circle>').join('');
  const dotEl = {}; dotsG.querySelectorAll('circle').forEach(c => { dotEl[c.dataset.i] = c; });
  function match(s){
    if(kind && s.kind !== kind) return false;
    const p = $('pref').value; if(p && s.pref !== p) return false;
    const q = $('q').value.trim().normalize('NFKC'); if(!q) return true;
    const t = (s.name + ' ' + s.addr).normalize('NFKC');
    return q.split(/\s+/).every(w => t.includes(w));
  }
  function ppu(){ const r = svg.getBoundingClientRect(); return r.width / vb[2]; }
  function inView(s){ return s.xy && s.xy[0] >= vb[0] && s.xy[0] <= vb[0] + vb[2] && s.xy[1] >= vb[1] && s.xy[1] <= vb[1] + vb[3]; }
  function draw(){
    svg.setAttribute('viewBox', vb.join(' '));
    const k = 1 / Math.max(ppu(), 0.01);
    const L = S.filter(match);
    const on = new Set(L.map(s => String(s.i)));
    for(const id in dotEl){ const c = dotEl[id]; const v = on.has(id); c.style.display = v ? '' : 'none'; c.setAttribute('r', (sel === +id ? 5 : 3.2) * k); c.classList.toggle('hl', sel === +id); }
    // 名前：見えている学校が少ないとき（拡大したとき）だけ、重ならないように出す
    const vis = L.filter(inView);
    const lb = $('lbls'); let h = '';
    if(vis.length <= 70 || sel != null){
      const boxes = [], fs = 11 * k;
      const order = vis.slice().sort((a, b) => (b.i === sel) - (a.i === sel));
      for(const s of order){ if(vis.length > 70 && s.i !== sel) continue;
        const w = s.name.length * fs, x = s.xy[0] + 4 * k, y = s.xy[1] + fs * 0.35;
        const bx = [x, y - fs, x + w, y + fs * 0.2];
        if(s.i !== sel && boxes.some(b => !(bx[2] < b[0] || bx[0] > b[2] || bx[3] < b[1] || bx[1] > b[3]))) continue;
        boxes.push(bx);
        h += '<text class="lbl' + (s.i === sel ? ' hl' : '') + '" x="' + x.toFixed(2) + '" y="' + y.toFixed(2) + '" style="font-size:' + fs.toFixed(2) + 'px;stroke-width:' + (3 * k).toFixed(2) + 'px">' + ESC(s.name) + '</text>';
      }
    }
    lb.innerHTML = h;
    // 一覧：地図に見えている学校を先に
    const list = L.slice().sort((a, b) => (inView(b) - inView(a)) || (PREFS.indexOf(a.pref) - PREFS.indexOf(b.pref)) || a.name.localeCompare(b.name, 'ja'));
    const MAX = 200;
    $('list').innerHTML = list.slice(0, MAX).map(s => '<div class="it' + (s.i === sel ? ' on' : '') + '" data-i="' + s.i + '"><div class="nm"><span class="tag ' + (s.kind === '短大' ? 't' : 's') + '">' + ESC(s.kind) + '</span>' + ESC(s.name) + '</div><div class="sub">' + ESC(s.type) + '・' + ESC(s.addr) + '</div></div>').join('') +
      (list.length > MAX ? '<div class="more">ほか ' + (list.length - MAX) + '校（地図を拡大するか、名前・都道府県で絞り込んでください）</div>' : '') + (list.length ? '' : '<div class="more">該当する学校がありません。</div>');
    $('cnt').textContent = L.length + '校' + (vis.length !== L.length ? '（地図の範囲に ' + vis.length + '校）' : '');
  }
  function pick(i, fly){
    sel = i; const s = S[i]; if(!s) return;
    const c = $('card'); c.hidden = false;
    const gm = 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(s.name + ' ' + s.addr);
    const gs = 'https://www.google.com/search?q=' + encodeURIComponent(s.name + ' 公式');
    c.innerHTML = '<h3><span class="tag ' + (s.kind === '短大' ? 't' : 's') + '">' + ESC(s.kind) + '</span>' + ESC(s.name) + '</h3><div class="sub">' + ESC(s.type) + '・' + ESC(s.addr) + '</div><div style="margin-top:6px"><a href="' + gm + '" target="_blank" rel="noopener">地図で見る ↗</a><a href="' + gs + '" target="_blank" rel="noopener">公式サイトを探す ↗</a></div>';
    if(fly && s.xy){ const w = Math.min(vb[2], 40), hh = w * HOME[3] / HOME[2]; vb = [s.xy[0] - w / 2, s.xy[1] - hh / 2, w, hh]; }
    draw();
    if(opt.onLog) try { opt.onLog('短大・専門を表示', s.name); } catch(e){}
  }
  // 操作：検索・種別・都道府県
  let qt = null;
  $('q').addEventListener('input', () => { clearTimeout(qt); qt = setTimeout(() => { sel = null; $('card').hidden = true; fitToMatches(); }, 200); });
  $('kind').addEventListener('click', e => { const b = e.target.closest('button'); if(!b) return; kind = b.dataset.k; $('kind').querySelectorAll('button').forEach(x => x.classList.toggle('on', x === b)); draw(); });
  $('pref').addEventListener('change', () => { sel = null; $('card').hidden = true; fitToMatches(); });
  function fitToMatches(){
    const L = S.filter(match).filter(s => s.xy);
    if(!L.length || (!$('q').value.trim() && !$('pref').value)){ vb = HOME.slice(); draw(); return; }
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for(const s of L){ x0 = Math.min(x0, s.xy[0]); y0 = Math.min(y0, s.xy[1]); x1 = Math.max(x1, s.xy[0]); y1 = Math.max(y1, s.xy[1]); }
    let w = Math.max(x1 - x0, 24) * 1.3, h = Math.max(y1 - y0, 24) * 1.3; const r = HOME[3] / HOME[2];
    if(h / w > r) w = h / r; else h = w * r;
    vb = [(x0 + x1) / 2 - w / 2, (y0 + y1) / 2 - h / 2, w, h]; draw();
  }
  $('list').addEventListener('click', e => { const it = e.target.closest('.it'); if(it) pick(+it.dataset.i, true); });
  dotsG.addEventListener('click', e => { const c = e.target.closest('circle'); if(c){ e.stopPropagation(); pick(+c.dataset.i, false); } });
  // 拡大・縮小・移動（ホイール、ドラッグ、ピンチ、ボタン）
  function zoomAt(px, py, f){ const w = Math.min(Math.max(vb[2] * f, 2), 600), r = w / vb[2]; vb = [px - (px - vb[0]) * r, py - (py - vb[1]) * r, w, vb[3] * r]; draw(); }
  function svgPt(cx, cy){ const r = svg.getBoundingClientRect(); return [vb[0] + (cx - r.left) / r.width * vb[2], vb[1] + (cy - r.top) / r.height * vb[3]]; }
  svg.addEventListener('wheel', e => { e.preventDefault(); const [x, y] = svgPt(e.clientX, e.clientY); zoomAt(x, y, e.deltaY > 0 ? 1.25 : 0.8); }, { passive: false });
  const ptr = new Map(); let start = null, moved = false;
  svg.addEventListener('pointerdown', e => { svg.setPointerCapture(e.pointerId); ptr.set(e.pointerId, [e.clientX, e.clientY]); start = { vb: vb.slice(), pts: [...ptr.values()].map(p => p.slice()) }; moved = false; svg.classList.add('drag'); });
  svg.addEventListener('pointermove', e => {
    if(!ptr.has(e.pointerId) || !start) return; ptr.set(e.pointerId, [e.clientX, e.clientY]);
    const r = svg.getBoundingClientRect(), P = [...ptr.values()];
    if(P.length === 1 && start.pts.length === 1){ const dx = (P[0][0] - start.pts[0][0]) / r.width * start.vb[2], dy = (P[0][1] - start.pts[0][1]) / r.height * start.vb[3]; if(Math.abs(dx) + Math.abs(dy) > 0.3) moved = true; vb = [start.vb[0] - dx, start.vb[1] - dy, start.vb[2], start.vb[3]]; draw(); }
    else if(P.length === 2 && start.pts.length === 2){ const d0 = Math.hypot(start.pts[0][0] - start.pts[1][0], start.pts[0][1] - start.pts[1][1]), d1 = Math.hypot(P[0][0] - P[1][0], P[0][1] - P[1][1]);
      if(d0 > 0 && d1 > 0){ moved = true; const f = d0 / d1, cx = (start.pts[0][0] + start.pts[1][0]) / 2, cy = (start.pts[0][1] + start.pts[1][1]) / 2;
        const px = start.vb[0] + (cx - r.left) / r.width * start.vb[2], py = start.vb[1] + (cy - r.top) / r.height * start.vb[3]; const w = Math.min(Math.max(start.vb[2] * f, 2), 600), k = w / start.vb[2];
        vb = [px - (px - start.vb[0]) * k, py - (py - start.vb[1]) * k, w, start.vb[3] * k]; draw(); } }
  });
  const end = e => { ptr.delete(e.pointerId); svg.classList.remove('drag'); start = ptr.size ? { vb: vb.slice(), pts: [...ptr.values()].map(p => p.slice()) } : null; };
  svg.addEventListener('pointerup', end); svg.addEventListener('pointercancel', end);
  svg.addEventListener('click', e => { if(moved) return; if(!e.target.closest('circle')){ sel = null; $('card').hidden = true; draw(); } });
  $('zin').onclick = () => zoomAt(vb[0] + vb[2] / 2, vb[1] + vb[3] / 2, 0.6);
  $('zout').onclick = () => zoomAt(vb[0] + vb[2] / 2, vb[1] + vb[3] / 2, 1.6);
  $('zhome').onclick = () => { vb = HOME.slice(); draw(); };
  new ResizeObserver(() => draw()).observe(svg);
  draw();
  return { apiVersion: 1, count: S.length, search: q => { $('q').value = q || ''; fitToMatches(); } };
}
const API = { apiVersion: 1, built: DATA.built || '', mount };
if(typeof window !== 'undefined') window.TanSenModule = API;
})();
