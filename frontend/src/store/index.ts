import { configureStore } from "@reduxjs/toolkit";
import triageReducer, { name as triageName } from "./triage/triageSlice";

export const store = configureStore({
  reducer: {
    [triageName]: triageReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
