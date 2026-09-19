// enhancer — 时间旅行: 每 20 票一快照, jump(i) 回车间 (物种正解: 动 store 者非 middleware)
const timeTravel = (createStore) => (reducer, pre) => {
  const store = createStore(reducer, pre);
  const snaps = []; let n = 0;
  return Object.assign({}, store, {
    dispatch(action) {
      const r = store.dispatch(action);
      if (!String(action.type).startsWith("@@") && ++n % 20 === 0) {
        snaps.push({ at: n, state: store.getState() });
        if (snaps.length > 50) snaps.shift();
      }
      return r;
    },
    jump(i) { const s = snaps[i]; if (s) store.dispatch({ type: "HYDRATE", payload: s.state }); },
    history: () => snaps.map((s) => s.at),
  });
};
module.exports = timeTravel;
