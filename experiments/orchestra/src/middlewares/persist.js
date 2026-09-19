// 90 persist 写端(middleware) + read 读端(rehydrate 素材) — 鸳鸯腿
const fs = require("fs");
function writer(logPath) {
  return (store) => (next) => (action) => {
    if (action.type !== "HYDRATE" && !String(action.type).startsWith("@@") && action.type !== "guard/rejected")
      fs.appendFileSync(logPath, JSON.stringify({ type: action.type, payload: action.payload || null, meta: action.meta || null }) + "\n");
    return next(action);
  };
}
function read(logPath) {
  if (!fs.existsSync(logPath)) return null;
  return { __replay: fs.readFileSync(logPath, "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l)) };
}
module.exports = { writer, read };
