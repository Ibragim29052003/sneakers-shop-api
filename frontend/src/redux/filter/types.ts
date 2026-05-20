export type Filters = {
    fabrics: string[];
    sizes: string[];
    colors: string[];
    brands: string[];
    styles: string[];
    seasons: string[];
    purposes: string[];
    minPrice?: number;
    maxPrice?: number;
    isNew?: boolean;
    sortBy?: 'price_asc' | 'price_desc' | 'new';
    category?: string;
}

export interface FiltersState {
    filters: Filters;
}
