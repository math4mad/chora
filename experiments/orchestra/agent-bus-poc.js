// GRAPHIA agent-bus PoC v2 — 主人提案 #2/#3 的证据机 (正解版)
// redux store(=共享信念状态/上下文) + saga(=agent工人编排) + 持久中间件(=通讯账本, 无漏)
const { createStore, applyMiddleware } = require('redux');
const createSagaMiddleware = require('redux-saga').default;
const { takeEvery, put, delay, select } = require('redux-saga/effects');
const fs = require('fs');
const LOG = __dirname + '/bus.ndjson';

function reducer(state = { jobs: {} }, a) {
  switch (a.type) {
    case 'JOB_DISPATCH': return { ...state, jobs: { ...state.jobs, [a.id]: { arm: a.arm, status: 'pending' } } };
    case 'JOB_STARTED':  return { ...state, jobs: { ...state.jobs, [a.id]: { ...state.jobs[a.id], status: 'running' } } };
    case 'JOB_DONE':     return { ...state, jobs: { ...state.jobs, [a.id]: { ...state.jobs[a.id], status: 'done', sha: a.sha } } };
    case 'NOTE_ARCHIVED':return { ...state, jobs: { ...state.jobs, [a.id]: { ...state.jobs[a.id], archived: true } } };
    default: return state;
  }
}
// —— agent 1: 计算工 (T4/Kaggle/训练器皆其化身) ——
function* worker(action) {
  const { id } = action;
  const cur = yield select(s => s.jobs[id]);
  if (cur && cur.status === 'done') { yield put({ type: 'JOB_DONE', id, sha: cur.sha }); return; } // 幂等: 已完成的只补归档事件
  yield put({ type: 'JOB_STARTED', id });
  yield delay(700);
  yield put({ type: 'JOB_DONE', id, sha: 'sha256:' + id.length + '-stub' });
}
// —— agent 2: 归档工 (打条入 manifest) ——
function* archivist(action) {
  if (action.type === 'JOB_DONE' && !action.sha) return;
  yield delay(200);
  fs.appendFileSync(__dirname + '/artifacts.log', `archived ${action.id} ${action.sha}\n`);
  yield put({ type: 'NOTE_ARCHIVED', id: action.id });
}
function* root() {
  yield takeEvery('JOB_DISPATCH', worker);
  yield takeEvery('JOB_DONE', archivist);
}
const sagaM = createSagaMiddleware();
// ★ 账本中间件居链底: 任何来源 (外部 dispatch 或 saga put) 的 action 无一能绕
const persistM = () => next => a => { fs.appendFileSync(LOG, JSON.stringify(a) + '\n'); return next(a); };
const store = createStore(reducer, applyMiddleware(persistM, sagaM));

if (fs.existsSync(LOG)) for (const line of fs.readFileSync(LOG, 'utf8').split('\n'))
  if (line.trim()) store.dispatch(JSON.parse(line));   // 重放复活 (reducer 幂等)

const JOBS = [['k-spring', 'spring'], ['k-summer', 'summer'], ['k-mid', 'mid']];
if (process.argv.includes('--crash-mid'))
  store.subscribe(() => { const j = store.getState().jobs['k-spring'];
    if (j && j.status === 'running') { console.log('☠ 暴毙于飞行中'); process.exit(9); } });
sagaM.run(root);                                        // 先架耳朵
for (const [id, arm] of JOBS) {
  const j = store.getState().jobs[id];
  if (!j || !j.archived) { console.log((j ? '» resume ' : '» dispatch ') + id); store.dispatch({ type: 'JOB_DISPATCH', id, arm }); }
}
const iv = setInterval(() => {
  const st = store.getState();
  if (JOBS.every(([id]) => st.jobs[id] && st.jobs[id].archived)) {
    clearInterval(iv);
    console.log('── 共享上下文 (=agent 的 context, 提案#3) ──');
    console.log(JSON.stringify(st.jobs));
    process.exit(0);
  }
}, 120);
