import type { RootState } from "../store";

export const selectCatalogSearchQuery = (state: RootState) =>
  state.catalogSearch.query;
