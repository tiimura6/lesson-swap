/**
 * 飯村システム：新規作成した操作者の名前を全端末で共有する（action=op_names）
 *
 * 使い方（Apps Script エディタで、飯村システムの GAS（操作ログ・PIN を受けているもの）を開いて）
 *  1. このファイルの関数 opNames_ と opNamesOut_ を、そのプロジェクトに貼り付ける（新しいファイルにしてよい）。
 *  2. doGet(e) の最初に次の1行を足す：
 *       if (e && e.parameter && e.parameter.action === 'op_names') return opNamesOut_(e);
 *  3. 「デプロイ」→「デプロイを管理」→ 鉛筆 →「バージョン：新バージョン」→「デプロイ」。（URL は変わらない）
 *
 * 返すもの：スプレッドシート「飯村システム」の「新規作成した操作者」シートで、状態が「使用中」の名前。
 * （そのシートは log・pins シートから数式で作っている。名前を消したいときは、作成した端末の新規作成画面で「削除」）
 */
var OP_SHEET_ID = '1DxrHZFOPULl204SyPEIfthLG6X7RdfI1u7ZcbeMMn14';

function opNames_() {
  var sh = SpreadsheetApp.openById(OP_SHEET_ID).getSheetByName('新規作成した操作者');
  if (!sh || sh.getLastRow() < 2) return { ok: true, names: [] };
  var v = sh.getRange(2, 1, sh.getLastRow() - 1, 9).getValues();   // A:名前 … I:状態
  var names = [];
  v.forEach(function (r) {
    var n = String(r[0] || '').trim();
    if (n && r[8] === '使用中' && names.indexOf(n) < 0 && n.length <= 20) names.push(n);
  });
  return { ok: true, names: names };
}

function opNamesOut_(e) {
  var cb = e.parameter.callback, body = JSON.stringify(opNames_());
  if (cb && /^[\w$.]+$/.test(cb)) return ContentService.createTextOutput(cb + '(' + body + ')').setMimeType(ContentService.MimeType.JAVASCRIPT);
  return ContentService.createTextOutput(body).setMimeType(ContentService.MimeType.JSON);
}
