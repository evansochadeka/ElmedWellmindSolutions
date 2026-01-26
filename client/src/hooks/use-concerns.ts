import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, buildUrl, type InsertConcern, type CATEGORIES } from "@shared/routes";

// GET /api/concerns
export function useConcerns(filters?: { category?: typeof CATEGORIES[number]; status?: 'open' | 'resolved'; search?: string }) {
  // Construct query string for key uniqueness
  const queryString = new URLSearchParams(filters as Record<string, string>).toString();
  
  return useQuery({
    queryKey: [api.concerns.list.path, queryString],
    queryFn: async () => {
      let url = api.concerns.list.path;
      if (queryString) {
        url += `?${queryString}`;
      }
      const res = await fetch(url, { credentials: "include" });
      if (!res.ok) throw new Error("Failed to fetch concerns");
      return api.concerns.list.responses[200].parse(await res.json());
    },
  });
}

// GET /api/concerns/:id
export function useConcern(id: number) {
  return useQuery({
    queryKey: [api.concerns.get.path, id],
    queryFn: async () => {
      const url = buildUrl(api.concerns.get.path, { id });
      const res = await fetch(url, { credentials: "include" });
      if (res.status === 404) return null;
      if (!res.ok) throw new Error("Failed to fetch concern");
      return api.concerns.get.responses[200].parse(await res.json());
    },
    enabled: !!id,
  });
}

// POST /api/concerns
export function useCreateConcern() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: InsertConcern) => {
      // Validate with input schema first
      const validated = api.concerns.create.input.parse(data);
      
      const res = await fetch(api.concerns.create.path, {
        method: api.concerns.create.method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(validated),
        credentials: "include",
      });
      
      if (!res.ok) {
        if (res.status === 400) {
           const error = api.concerns.create.responses[400].parse(await res.json());
           throw new Error(error.message);
        }
        throw new Error("Failed to create concern");
      }
      return api.concerns.create.responses[201].parse(await res.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [api.concerns.list.path] });
    },
  });
}

// POST /api/concerns/:id/upvote
export function useUpvoteConcern() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const url = buildUrl(api.concerns.upvote.path, { id });
      const res = await fetch(url, {
        method: api.concerns.upvote.method,
        credentials: "include",
      });
      
      if (!res.ok) throw new Error("Failed to upvote");
      return api.concerns.upvote.responses[200].parse(await res.json());
    },
    onSuccess: (data, id) => {
      queryClient.invalidateQueries({ queryKey: [api.concerns.list.path] });
      queryClient.invalidateQueries({ queryKey: [api.concerns.get.path, id] });
    },
  });
}

// GET /api/categories
export function useCategories() {
    return useQuery({
        queryKey: [api.categories.list.path],
        queryFn: async () => {
            const res = await fetch(api.categories.list.path, { credentials: "include" });
            if (!res.ok) throw new Error("Failed to fetch categories");
            return api.categories.list.responses[200].parse(await res.json());
        }
    })
}
