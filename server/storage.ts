import { users, concerns, chatMessages, type User, type InsertUser, type Concern, type InsertConcern, type ChatMessage, type InsertChatMessage } from "@shared/schema";
import { users as authUsers, type User as AuthUser, type UpsertUser } from "@shared/models/auth";
import { db } from "./db";
import { eq, ilike, and, desc, sql } from "drizzle-orm";
import { IAuthStorage } from "./replit_integrations/auth/storage";

export interface IStorage extends IAuthStorage {
  // Users (extended)
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;

  // Concerns
  getConcerns(filters?: { category?: string; status?: string; search?: string }): Promise<Concern[]>;
  getConcern(id: number): Promise<Concern | undefined>;
  createConcern(concern: InsertConcern): Promise<Concern>;
  updateConcern(id: number, updates: Partial<InsertConcern>): Promise<Concern>;
  upvoteConcern(id: number): Promise<Concern>;

  // Chat
  createChatMessage(message: InsertChatMessage): Promise<ChatMessage>;
  getChatHistory(userId?: number): Promise<ChatMessage[]>;
}

export class DatabaseStorage implements IStorage {
  // Auth Storage Implementation
  async getUser(id: string): Promise<AuthUser | undefined> {
      const [user] = await db.select().from(authUsers).where(eq(authUsers.id, id));
      return user;
  }

  async upsertUser(userData: UpsertUser): Promise<AuthUser> {
      const [user] = await db
        .insert(authUsers)
        .values(userData)
        .onConflictDoUpdate({
          target: authUsers.id,
          set: {
            ...userData,
            updatedAt: new Date(),
          },
        })
        .returning();
      return user;
  }

  // App User Implementation
  async getUserByUsername(username: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.username, username));
    return user;
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const [user] = await db.insert(users).values(insertUser).returning();
    return user;
  }

  // Concerns Implementation
  async getConcerns(filters?: { category?: string; status?: string; search?: string }): Promise<Concern[]> {
    let conditions = [];
    if (filters?.category) conditions.push(eq(concerns.category, filters.category));
    if (filters?.status) conditions.push(eq(concerns.status, filters.status));
    if (filters?.search) conditions.push(ilike(concerns.title, `%${filters.search}%`)); // Simple title search

    return await db.select()
      .from(concerns)
      .where(and(...conditions))
      .orderBy(desc(concerns.createdAt));
  }

  async getConcern(id: number): Promise<Concern | undefined> {
    const [concern] = await db.select().from(concerns).where(eq(concerns.id, id));
    return concern;
  }

  async createConcern(concern: InsertConcern): Promise<Concern> {
    const [newConcern] = await db.insert(concerns).values(concern).returning();
    return newConcern;
  }

  async updateConcern(id: number, updates: Partial<InsertConcern>): Promise<Concern> {
    const [updated] = await db.update(concerns)
      .set(updates)
      .where(eq(concerns.id, id))
      .returning();
    return updated;
  }

  async upvoteConcern(id: number): Promise<Concern> {
    const [updated] = await db.update(concerns)
      .set({ upvotes: sql`${concerns.upvotes} + 1` })
      .where(eq(concerns.id, id))
      .returning();
    return updated;
  }

  // Chat Implementation
  async createChatMessage(message: InsertChatMessage): Promise<ChatMessage> {
    const [msg] = await db.insert(chatMessages).values(message).returning();
    return msg;
  }

  async getChatHistory(userId?: number): Promise<ChatMessage[]> {
    // For now, if no userId, return empty or session based?
    // Let's assume we might show last 50 messages for context if user logged in
    if (!userId) return [];
    return await db.select()
      .from(chatMessages)
      .where(eq(chatMessages.userId, userId))
      .orderBy(chatMessages.createdAt);
  }
}

export const storage = new DatabaseStorage();
