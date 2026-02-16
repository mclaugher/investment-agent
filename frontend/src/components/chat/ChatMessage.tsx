import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";
import type { ChatMessage as ChatMessageType } from "@/types";

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[75%] rounded-2xl px-4 py-3",
          isUser
            ? "bg-blue-600 text-white rounded-br-md"
            : "bg-gray-100 text-gray-900 rounded-bl-md"
        )}
      >
        {isUser ? (
          <p className="text-sm">{message.content}</p>
        ) : (
          <div className="prose prose-sm max-w-none prose-p:text-gray-700 prose-headings:text-gray-900 prose-a:text-blue-600 prose-code:text-gray-800">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
        <div
          className={cn(
            "text-xs mt-1.5",
            isUser ? "text-blue-200" : "text-gray-400"
          )}
        >
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </div>
      </div>
    </div>
  );
}
