import { pgTable, text, serial, integer, boolean, timestamp } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  email: text("email"),
  isAdmin: boolean("is_admin").default(false),
  createdAt: timestamp("created_at").defaultNow(),
});

export const concerns = pgTable("concerns", {
  id: serial("id").primaryKey(),
  title: text("title").notNull(),
  content: text("content").notNull(),
  category: text("category").notNull(),
  authorId: integer("author_id"), // Can be null for anonymous, or linked to user
  response: text("response"),
  status: text("status").default("open"), // open, resolved
  upvotes: integer("upvotes").default(0),
  createdAt: timestamp("created_at").defaultNow(),
});

export const chatMessages = pgTable("chat_messages", {
  id: serial("id").primaryKey(),
  userId: integer("user_id"), // Optional if guest
  role: text("role").notNull(), // user, assistant
  content: text("content").notNull(),
  createdAt: timestamp("created_at").defaultNow(),
});

// Zod Schemas
export const insertUserSchema = createInsertSchema(users).omit({ id: true, createdAt: true, isAdmin: true });
export const insertConcernSchema = createInsertSchema(concerns).omit({ id: true, createdAt: true, response: true, status: true, upvotes: true });
export const insertChatMessageSchema = createInsertSchema(chatMessages).omit({ id: true, createdAt: true });

// Types
export type User = typeof users.$inferSelect;
export type InsertUser = z.infer<typeof insertUserSchema>;

export type Concern = typeof concerns.$inferSelect;
export type InsertConcern = z.infer<typeof insertConcernSchema>;

export type ChatMessage = typeof chatMessages.$inferSelect;
export type InsertChatMessage = z.infer<typeof insertChatMessageSchema>;

// Request/Response Types
export type CreateConcernRequest = InsertConcern;
export type UpdateConcernRequest = Partial<InsertConcern>;
export type AddResponseRequest = { response: text };

export const CATEGORIES = [
  "General Health",
  "Mental Health",
  "Maternal Health",
  "Pediatrics",
  "Nutrition",
  "Sexual Health",
  "Chronic Diseases"
] as const;
