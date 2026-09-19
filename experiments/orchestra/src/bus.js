// ORCHESTRA 组装台: slices + 插座序 guard(00)→saga(10)→persist(90); replay 造种子
const fs = require("fs");
const { configureStore } = require("@reduxjs/toolkit");
const createSagaMiddleware = require("redux-saga").default;
const guard = require("./middlewares/guard");
const persist = require("./middlewares/persist");
const world = require("./slices/world"), agents = require("./slices/agents"), clarif = require("./slices/clarif");

const reducerMap = { world: world.reducer, agents: agents.reducer, clarif: clarif.reducer };
const rawReduce = (s, a) => ({ world: world.reducer(s.world, a), agents: agents.reducer(s.agents, a), clarif: clarif.reducer(s.clarif, a) });

function makeBus({ rootSaga, logPath }) {
  const saga = createSagaMiddleware();
  let seed;
  const replayed = persist.read(logPath);
  if (replayed) { seed = { world: undefined, agents: undefined, clarif: undefined }; for (const a of replayed.__replay) seed = rawReduce(seed, a); }
  const reducer = (state, action) => (action.type === "HYDRATE" && action.payload) ? action.payload : reducerRawWrap(state, action);
  function reducerRawWrap(state, action) {
    const s = state || { world: world.getInitialState(), agents: agents.getInitialState(), clarif: clarif.getInitialState() };
    return rawReduce(s, action);
  }
  const store = configureStore({ reducer: reducerMap, preloadedState: seed,
    middleware: (gd) => gd({ serializableCheck: false }).concat(guard, saga, persist.writer(logPath)), devTools: true });
  if (rootSaga) saga.run(rootSaga);
  return { store, saga, selectors: { ctxFor: (id) => (s) => ({ worldLog: s.world.log.slice(-20), mine: s.agents[id] || null, pendingClarify: s.clarif.pending }) } };
}
module.exports = { makeBus };
