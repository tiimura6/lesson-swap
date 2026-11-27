// 合同化の判定エンジン（index.html の <script id="mergeEngine">）のテスト
// 実行：node tests/merge_engine.test.js
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const m = html.match(/<script id="mergeEngine">([\s\S]*?)<\/script>/);
if (!m) { console.error('mergeEngine script not found'); process.exit(1); }
const ctx = { window: {} };
vm.runInNewContext(m[1], ctx);
const find = ctx.window.MergeEngine.find;

const sig = l => [l.school, l.day, l.period, l.grade, l.class, l.course || '', l.subject].join('|');
function L(teacher, grade, cls, day, period, subject, course, school){
  return { teacher, school: school || 'HS', grade, class: cls, course: course || '', day, period, subject };
}
function makeEnv(lessons, opt){
  opt = opt || {};
  const events = new Set(opt.events || []);
  const part = new Set(opt.parttime || []);
  return {
    lessons,
    teacherHasSlot: (t, d, p) => lessons.some(l => l.teacher === t && l.day === d && l.period === p),
    hasAnyEvent: (t, d, p) => events.has(t + '|' + d + '|' + p),
    isParttimeTeacher: t => part.has(t),
    getAllTeachersForLesson: l => Array.from(new Set(lessons.filter(x => sig(x) === sig(l)).map(x => x.teacher))).sort(),
    infoRoomConflict: () => !!opt.info
  };
}

const tests = {
  test_same_slot(){
    const me = L('A',1,1,'Mon',1,'英語');
    const ls = [me, L('B',1,2,'Mon',1,'英語')];
    const r = find(me, makeEnv(ls));
    assert.strictEqual(r.length, 1);
    assert.strictEqual(r[0].kind, 'same');
    assert.strictEqual(r[0].moved, null);
    assert.deepStrictEqual(Array.from(r[0].targetTeachers), ['B']);
  },
  test_move(){
    const me = L('A',1,1,'Mon',1,'英語');
    const ls = [me, L('B',1,2,'Tue',2,'英語'), L('C',1,1,'Tue',2,'数学'), L('X',1,2,'Mon',1,'国語')];
    const r = find(me, makeEnv(ls));
    assert.strictEqual(r.length, 1);
    assert.strictEqual(r[0].kind, 'move');
    assert.strictEqual(r[0].moved.teacher, 'C');
    assert.deepStrictEqual(Array.from(r[0].movedTeachers), ['C']);
    assert.strictEqual(r[0].target.day, 'Tue');
  },
  test_move_blocked(){
    const me = L('A',1,1,'Mon',1,'英語');
    const ls = [me, L('B',1,2,'Tue',2,'英語'), L('C',1,1,'Tue',2,'数学'), L('C',1,3,'Mon',1,'数学')];
    assert.strictEqual(find(me, makeEnv(ls)).length, 0);
  },
  test_dedup_coteach(){
    const me = L('A',1,1,'Mon',1,'英語');
    const ls = [me, L('B',1,2,'Tue',2,'英語'), L('D',1,2,'Tue',2,'英語'), L('C',1,1,'Tue',2,'数学')];
    const r = find(me, makeEnv(ls));
    assert.strictEqual(r.length, 1);
    assert.deepStrictEqual(Array.from(r[0].targetTeachers), ['B','D']);
  },
  test_bunri_mismatch(){
    const me = L('A',2,1,'Mon',1,'英語','文');
    const ls = [me, L('B',2,2,'Mon',1,'英語','理')];
    assert.strictEqual(find(me, makeEnv(ls)).length, 0);
  },
  test_bunri_blank_ok(){
    const me = L('A',2,1,'Mon',1,'英語','文');
    const ls = [me, L('B',2,2,'Mon',1,'英語','')];
    assert.strictEqual(find(me, makeEnv(ls)).length, 1);
  },
  test_ambiguous_q(){
    const me = L('A',2,1,'Mon',1,'英語','');
    const ls = [me, L('B',2,2,'Tue',2,'英語',''), L('C',2,1,'Tue',2,'物理','理'), L('E',2,1,'Tue',2,'日本史','文')];
    assert.strictEqual(find(me, makeEnv(ls)).length, 0);
  },
  test_self_in_q(){
    const me = L('A',1,1,'Mon',1,'英語');
    const ls = [me, L('B',1,2,'Tue',2,'英語'), L('A',1,1,'Tue',2,'英語表現')];
    const r = find(me, makeEnv(ls));
    assert.strictEqual(r.length, 1);
    assert.strictEqual(r[0].moved.teacher, 'A');
  },
  test_joint_q_excluded(){
    const me = L('A',1,1,'Mon',1,'英語');
    const ls = [me, L('B',1,2,'Tue',2,'英語'), L('C',1,1,'Tue',2,'体育'), L('C',1,3,'Tue',2,'体育')];
    assert.strictEqual(find(me, makeEnv(ls)).length, 0);
  },
  test_joint_me(){
    const me = L('A',1,1,'Mon',1,'英語');
    const ls = [me, L('A',1,3,'Mon',1,'英語'), L('B',1,2,'Mon',1,'英語')];
    assert.strictEqual(find(me, makeEnv(ls)).length, 0);
  },
  test_target_has_me_teacher_excluded(){
    const me = L('A',1,1,'Mon',1,'英語');
    const ls = [me, L('A',1,2,'Tue',2,'英語'), L('C',1,1,'Tue',2,'数学')];
    assert.strictEqual(find(me, makeEnv(ls)).length, 0);
  },
  test_no_slot_for_class(){
    const me = L('A',1,1,'Mon',1,'英語');
    const ls = [me, L('B',1,2,'Sat',5,'英語')];
    assert.strictEqual(find(me, makeEnv(ls)).length, 0);
  },
  test_warnings(){
    const me = L('A',1,1,'Mon',1,'英語');
    const ls = [me, L('B',1,2,'Tue',2,'英語'), L('C',1,1,'Tue',2,'数学')];
    const r = find(me, makeEnv(ls, { events:['C|Mon|1'], parttime:['B'] }));
    assert.strictEqual(r[0].eventWarn, true);
    assert.strictEqual(r[0].parttime, true);
    assert.strictEqual(r[0].infoWarn, false);
  },
  test_sort(){
    const me = L('A',1,1,'Wed',3,'英語');
    const ls = [me,
      L('B',1,2,'Mon',1,'英語'), L('C',1,1,'Mon',1,'数学'),   // 警告あり（C に研修）
      L('D',1,3,'Fri',2,'英語'), L('E',1,1,'Fri',2,'国語'),   // 警告なし
      L('F',1,4,'Wed',3,'英語')];                               // 同じコマ
    const r = find(me, makeEnv(ls, { events:['C|Wed|3'] }));
    assert.deepStrictEqual(Array.from(r.map(c => c.kind + ':' + c.target.teacher)), ['same:F','move:D','move:B']);
  }
};

let fail = 0;
for (const [name, fn] of Object.entries(tests)) {
  try { fn(); } catch (e) { fail++; console.error('FAIL ' + name + ': ' + e.message); }
}
if (fail) { console.error(fail + ' failed'); process.exit(1); }
console.log('all passed (' + Object.keys(tests).length + ')');
