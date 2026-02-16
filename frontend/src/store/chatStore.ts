import { create } from "zustand";
import type { ChatMessage } from "../types";
import {
  sendChatMessage as apiSendMessage,
  fetchChatHistory as apiFetchHistory,
} from "../lib/api";

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  sendMessage: (text: string) => Promise<void>;
  fetchHistory: () => Promise<void>;
}

export const useChatStore = create<ChatState>()((set, get) => ({
  messages: [],
  isLoading: false,

  sendMessage: async (text: string) => {
    const userMessage: ChatMessage = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    set({ messages: [...get().messages, userMessage], isLoading: true });

    try {
      const response = await apiSendMessage(text);
      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.response,
        timestamp: new Date().toISOString(),
        intent: response.intent,
      };
      set({ messages: [...get().messages, assistantMessage], isLoading: false });
    } catch {
      const errorMessage: ChatMessage = {
        role: "assistant",
        content: "Sorry, something went wrong. Please try again.",
        timestamp: new Date().toISOString(),
      };
      set({ messages: [...get().messages, errorMessage], isLoading: false });
    }
  },

  fetchHistory: async () => {
    set({ isLoading: true });
    try {
      const messages = await apiFetchHistory();
      set({ messages, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },
}));
