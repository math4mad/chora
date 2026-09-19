const { createSlice } = require("@reduxjs/toolkit");
const clarif = createSlice({
  name: "clarif",
  initialState: { pending: null, round: 0 },
  reducers: {
    ask(s, a) { s.pending = { questions: a.payload.questions, taskId: a.payload.taskId }; s.round += 1; },
    answer(s) { s.pending = null; s.round = 0; },
  },
});
module.exports = clarif;
