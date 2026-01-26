import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@shared/routes";

// POST /api/chat
export function useChat() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (message: string) => {
      const validated = api.chat.send.input.parse({ message });
      
      const res = await fetch(api.chat.send.path, {
        method: api.chat.send.method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(validated),
        credentials: "include",
      });
      
      if (!res.ok) throw new Error("Failed to send message");
      return api.chat.send.responses[200].parse(await res.json());
    },
    onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: [api.chat.history.path] });
    }
  });
}

// GET /api/chat/history
export function useChatHistory() {
    return useQuery({
        queryKey: [api.chat.history.path],
        queryFn: async () => {
            const res = await fetch(api.chat.history.path, { credentials: "include" });
            if(!res.ok) throw new Error("Failed to fetch history");
            return api.chat.history.responses[200].parse(await res.json());
        }
    });
}
