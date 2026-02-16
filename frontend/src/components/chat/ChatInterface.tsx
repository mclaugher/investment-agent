import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import { useChatStore } from "@/store/chatStore";
import { ChatMessage } from "./ChatMessage";
import { SuggestionChips } from "./SuggestionChips";

export function ChatInterface() {
  const messages = useChatStore((s) => s.messages);
  const sendMessage = useChatStore((s) => s.sendMessage);
  const isLoading = useChatStore((s) => s.isLoading);

  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;
    sendMessage(trimmed);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestion = (text: string) => {
    setInput(text);
    inputRef.current?.focus();
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-xl border border-gray-200">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center py-12">
            <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center mb-4">
              <Send className="h-6 w-6 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              Chat with Alpha Fund
            </h3>
            <p className="text-sm text-gray-500 max-w-md">
              Ask about portfolio status, request analysis, review decisions, or get market updates.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
              <div className="flex gap-1">
                <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.15s]" />
                <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.3s]" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-200 p-4 space-y-3">
        {messages.length === 0 && <SuggestionChips onSelect={handleSuggestion} />}

        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your portfolio..."
            className="flex-1 px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="h-10 w-10 rounded-lg bg-blue-600 text-white flex items-center justify-center disabled:opacity-50 hover:bg-blue-700 transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
