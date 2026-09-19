// 两幕剧验收 v2 (RTK 骨架): 记账暴毙 → rehydrate 复活恰齐 → P 的上下文切片示例
const fs = require("fs"), path = require("path");
const LOG = path.join(__dirname, "bus-test.ndjson");
try { fs.unlinkSync(LOG); } catch (e) {}
const { makeBus } = require("../src/bus");
const b1 = makeBus({ logPath: LOG });
b1.store.dispatch({ type: "world/receipt", payload: { id: "spring", status: "done", sha: "s8" }, meta: { origin: "k" } });
b1.store.dispatch({ type: "world/receipt", payload: { id: "summer", status: "done", sha: "s6" }, meta: { origin: "k" } });
b1.store.dispatch({ type: "agents/scratch", payload: { note: "盯 kaggle" }, meta: { origin: "p" } });
b1.store.dispatch({ type: "world/receipt", payload: { id: "ghost", status: "done" }, meta: { origin: "hacker" } }); // 无票者
console.log("幕一账本:", fs.readFileSync(LOG, "utf8").trim().split("\n").length, "行 | 状态 byId:", Object.keys(b1.store.getState().world.byId).join(","));
const b2 = makeBus({ logPath: LOG });
const st = b2.store.getState();
const ok = Object.keys(st.world.byId).length === 2 && st.world.byId.spring.sha === "s8" && !!st.agents.p;
console.log("幕二复活:", Object.keys(st.world.byId).join(","), "| P 草稿:", JSON.stringify(st.agents.p.scratch));
console.log("P 的上下文(导出物,非寄存物):", JSON.stringify(b2.selectors.ctxFor("p")(st).worldLog));
console.log(ok ? "两幕剧 v2 ✔ (guard 拒 ghost / persist 无漏 / rehydrate 恰齐)" : "❌ 验收未过");
process.exit(ok ? 0 : 1);
