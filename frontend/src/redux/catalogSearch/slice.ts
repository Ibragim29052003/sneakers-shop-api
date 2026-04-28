import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { CatalogSearchState } from "./types";

const initialState: CatalogSearchState = {
  query: "",
};

const catalogSearchSlice = createSlice({
  name: "catalogSearch",
  initialState,
  reducers: {
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.query = action.payload;
    },
    clearSearchQuery: (state) => {
      state.query = "";
    },
  },
});

export const { setSearchQuery, clearSearchQuery } = catalogSearchSlice.actions;

export default catalogSearchSlice.reducer;
