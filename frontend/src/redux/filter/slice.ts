import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { Filters, FiltersState } from "./types";

const initialFilters: Filters = {
  fabrics: [],
  sizes: [],
  colors: [],
  minPrice: undefined,
  maxPrice: undefined,
  isNew: undefined,
  sortBy: undefined,
  category: undefined,
};

const initialState: FiltersState = {
  filters: initialFilters,
};

const filtersSlice = createSlice({
  name: "filters",
  initialState,
  reducers: {

    setFabrics: (state, action: PayloadAction<string[]>) => {
        state.filters.fabrics = action.payload
    },

    setSizes: (state, action: PayloadAction<string[]>) => {
      state.filters.sizes = action.payload;
    },

    setColors: (state, action: PayloadAction<string[]>) => {
      state.filters.colors = action.payload;
    },

    setMinPrice: (state, action: PayloadAction<number | undefined>) => {
      state.filters.minPrice = action.payload;
    },

    setMaxPrice: (state, action: PayloadAction<number | undefined>) => {
      state.filters.maxPrice = action.payload;
    },

    setIsNew: (state, action: PayloadAction<boolean | undefined>) => {
        state.filters.isNew = action.payload
    },

    setSortBy: (state, action: PayloadAction<Filters['sortBy']>) => {
        state.filters.sortBy = action.payload
    },

    setCategories: (state, action: PayloadAction<string | undefined>) => {
      state.filters.category = action.payload;
    },

    // Partial делает все поля опциональными, чтобы при изменении одного фильтра, не приходилось передавать и остальные неопциональные параметры
    updateFilters: (state, action: PayloadAction<Partial<Filters>>) => {
        // берем старые фильтры -  ...state.filters
        // накладываем новые значения сверху -  ...action.payload
        state.filters = {...state.filters, ...action.payload}
    },

    clearFilters: (state) => {
        state.filters = initialFilters
    }
  },
});


export const {
    setCategories,
    setFabrics,
    setSizes,
    setColors,
    setMinPrice,
    setMaxPrice,
    setSortBy,
    setIsNew,
    updateFilters,
    clearFilters
} = filtersSlice.actions

export default filtersSlice.reducer // для подключения к стору
