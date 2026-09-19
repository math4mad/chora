const { createSlice } = require("@reduxjs/toolkit");
const world = createSlice({
  name: "world",
  initialState: { byId: {}, log: [] },
  reducers: {
    receipt(s, a) { s.byId[a.payload.id] = { ...a.payload };
                    s.log.push(`${a.payload.id}:${a.payload.status}`); },
  },
});
module.exports = world;
