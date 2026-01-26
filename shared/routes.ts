import { z } from 'zod';
import { insertConcernSchema, concerns, chatMessages, insertChatMessageSchema, CATEGORIES } from './schema';

// Re-export schema items that frontend might be looking for here
export { insertConcernSchema, concerns, chatMessages, insertChatMessageSchema, CATEGORIES };
export * from './schema';

export const errorSchemas = {
  validation: z.object({
    message: z.string(),
    field: z.string().optional(),
  }),
  notFound: z.object({
    message: z.string(),
  }),
  internal: z.object({
    message: z.string(),
  }),
};

export const api = {
  concerns: {
    list: {
      method: 'GET' as const,
      path: '/api/concerns',
      input: z.object({
        category: z.enum(CATEGORIES).optional(),
        status: z.enum(['open', 'resolved']).optional(),
        search: z.string().optional()
      }).optional(),
      responses: {
        200: z.array(z.custom<typeof concerns.$inferSelect>()),
      },
    },
    get: {
      method: 'GET' as const,
      path: '/api/concerns/:id',
      responses: {
        200: z.custom<typeof concerns.$inferSelect>(),
        404: errorSchemas.notFound,
      },
    },
    create: {
      method: 'POST' as const,
      path: '/api/concerns',
      input: insertConcernSchema,
      responses: {
        201: z.custom<typeof concerns.$inferSelect>(),
        400: errorSchemas.validation,
      },
    },
    respond: {
      method: 'PATCH' as const,
      path: '/api/concerns/:id/respond',
      input: z.object({ response: z.string() }),
      responses: {
        200: z.custom<typeof concerns.$inferSelect>(),
        404: errorSchemas.notFound,
      },
    },
    upvote: {
      method: 'POST' as const,
      path: '/api/concerns/:id/upvote',
      responses: {
        200: z.object({ upvotes: z.number() }),
        404: errorSchemas.notFound,
      },
    },
  },
  chat: {
    send: {
      method: 'POST' as const,
      path: '/api/chat',
      input: z.object({ message: z.string() }),
      responses: {
        200: z.object({ response: z.string() }),
        500: errorSchemas.internal,
      },
    },
    history: {
        method: 'GET' as const,
        path: '/api/chat/history',
        responses: {
            200: z.array(z.custom<typeof chatMessages.$inferSelect>()),
        }
    }
  },
  categories: {
    list: {
        method: 'GET' as const,
        path: '/api/categories',
        responses: {
            200: z.array(z.string())
        }
    }
  }
};

export function buildUrl(path: string, params?: Record<string, string | number>): string {
  let url = path;
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (url.includes(`:${key}`)) {
        url = url.replace(`:${key}`, String(value));
      }
    });
  }
  return url;
}
