import { createSlice } from '@reduxjs/toolkit';
import { RootState } from '..';

interface TriageState {
  cases: any[];
}

const initialState: TriageState = {
  cases: [],
};

export const name = "triage";

export const triageSlice = createSlice({
  name,
  initialState,
  reducers: {
    addTriageCase: (state, action) => {
      state.cases.push(action.payload);
    },
  },
});

export const { addTriageCase } = triageSlice.actions;

export const getTriageCases = (state: RootState) => state[name].cases;

export default triageSlice.reducer;
