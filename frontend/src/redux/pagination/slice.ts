import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { PaginationState } from "./types";

const initialState: PaginationState = {
  currentPage: 1,
  itemsPerPage: 12,
};

const paginationSlice = createSlice({
  name: "pagination",
  initialState,
  reducers: {
    setCurrentPage: (state, action: PayloadAction<number>) => {
      state.currentPage = action.payload;
    },

    setItemsPerPage: (state, action: PayloadAction<number>) => {
      state.itemsPerPage = action.payload;
    },
  },
});

export const { setCurrentPage, setItemsPerPage } = paginationSlice.actions;

export default paginationSlice.reducer;
