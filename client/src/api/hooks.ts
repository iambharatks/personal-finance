import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { api, type Params } from "./client";
import type { Account, Category, Meta } from "./types";

/** GET a filtered resource. While a refetch runs, the previous result stays on screen. */
export function useApiQuery<T>(path: string, params: Params = {}) {
  return useQuery({
    queryKey: [path, params],
    queryFn: () => api<T>(path, { params }),
    placeholderData: keepPreviousData,
  });
}

const LOOKUP = { staleTime: 5 * 60 * 1000 };

export const useAccounts = () =>
  useQuery({ queryKey: ["/accounts"], queryFn: () => api<Account[]>("/accounts"), ...LOOKUP });

export const useCategories = () =>
  useQuery({ queryKey: ["/categories"], queryFn: () => api<Category[]>("/categories"), ...LOOKUP });

export const useMeta = () =>
  useQuery({ queryKey: ["/meta"], queryFn: () => api<Meta>("/meta"), ...LOOKUP });
