// 00 guard — 写篱: 凡写 action 须持 meta.origin ∈ 注册名单; 违令拒账并留审计票
const REGISTRY = new Set(["p", "d", "k", "saga", "system", "owner"]);
const guard = (store) => (next) => (action) => {
  const writeish = !String(action.type).startsWith("@@") && action.type !== "HYDRATE";
  if (writeish && action.type !== "guard/rejected") {
    const who = action.meta && action.meta.origin;
    if (!who || !REGISTRY.has(who)) {
      console.warn(`[guard] 拒收无主票据: ${action.type} (origin=${who})`);
      return next({ type: "guard/rejected", payload: action, meta: { origin: "system" } });
    }
  }
  return next(action);
};
module.exports = guard;
