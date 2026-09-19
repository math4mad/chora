const { createSlice } = require("@reduxjs/toolkit");
const agents = createSlice({
  name: "agents",
  initialState: {},
  reducers: {
    scratch(s, a) { const id = a.meta && a.meta.origin; if (!id) return;
      if (!s[id]) s[id] = { scratch: {}, lastSeenLen: 0 };
      s[id].scratch = { ...s[id].scratch, ...a.payload }; },
    seen(s, a) { const id = a.meta && a.meta.origin;
      if (id && s[id]) s[id].lastSeenLen = a.payload.len; },
  },
});
module.exports = agents;
