import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { RootState } from '..';
import { ATSLevel } from '../../types/triage';

interface TriageCase {
  id: string;
  name: string;
  date: string;
  priority: ATSLevel;
}

interface TriageState {
  cases: TriageCase[];
}

const initialState: TriageState = {
  cases: [],
};

export const name = "triage";

export const triageSlice = createSlice({
  name,
  initialState,
  reducers: {
    addTriageCase: (state, action: PayloadAction<TriageCase>) => {
      state.cases.push(action.payload);
    },
  },
});

export const { addTriageCase } = triageSlice.actions;

export const getTriageCases = (state: RootState) => state[name].cases;

export default triageSlice.reducer;
