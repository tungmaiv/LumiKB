"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useActiveKb } from "@/lib/stores/kb-store";
import { DashboardLayout } from "@/components/layout/dashboard-layout";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Array<{
    number: number;
    document_name: string;
    page?: number;
    excerpt?: string;
  }>;
}

export default function ChatPage() {
  const activeKb = useActiveKb();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || !activeKb || isStreaming) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsStreaming(true);

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: "",
      citations: [],
    };

    setMessages((prev) => [...prev, assistantMessage]);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          kb_id: activeKb.id,
          message: userMessage.content,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error("No response body");
      }

      // Buffer for incomplete SSE lines that span across chunks
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // Append decoded chunk to buffer (use stream: true for proper handling)
        buffer += decoder.decode(value, { stream: true });

        // Split by newlines, keeping incomplete line in buffer
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // Keep last (potentially incomplete) line in buffer

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const jsonStr = line.slice(6);
            try {
              const event = JSON.parse(jsonStr);

              if (event.type === "token") {
                setMessages((prev) => {
                  const lastIdx = prev.length - 1;
                  const lastMsg = prev[lastIdx];
                  if (lastMsg.role === "assistant") {
                    // Create new array with new message object (immutable update)
                    return [
                      ...prev.slice(0, lastIdx),
                      { ...lastMsg, content: lastMsg.content + event.content },
                    ];
                  }
                  return prev;
                });
              } else if (event.type === "citation") {
                setMessages((prev) => {
                  const lastIdx = prev.length - 1;
                  const lastMsg = prev[lastIdx];
                  if (lastMsg.role === "assistant") {
                    // Create new array with new message object (immutable update)
                    return [
                      ...prev.slice(0, lastIdx),
                      {
                        ...lastMsg,
                        citations: [...(lastMsg.citations || []), event.data],
                      },
                    ];
                  }
                  return prev;
                });
              } else if (event.type === "error") {
                throw new Error(event.message);
              }
            } catch (e) {
              console.error("Failed to parse SSE event:", e);
            }
          }
        }
      }

      // Process any remaining data in buffer after stream ends
      if (buffer.startsWith("data: ")) {
        try {
          const event = JSON.parse(buffer.slice(6));
          if (event.type === "token") {
            setMessages((prev) => {
              const lastIdx = prev.length - 1;
              const lastMsg = prev[lastIdx];
              if (lastMsg.role === "assistant") {
                // Create new array with new message object (immutable update)
                return [
                  ...prev.slice(0, lastIdx),
                  { ...lastMsg, content: lastMsg.content + event.content },
                ];
              }
              return prev;
            });
          }
        } catch {
          // Ignore parse errors on final buffer
        }
      }
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => {
        const lastIdx = prev.length - 1;
        const lastMsg = prev[lastIdx];
        if (lastMsg.role === "assistant" && !lastMsg.content) {
          // Create new array with new message object (immutable update)
          return [
            ...prev.slice(0, lastIdx),
            { ...lastMsg, content: "Error: Failed to get response. Please try again." },
          ];
        }
        return prev;
      });
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (!activeKb) {
    return (
      <DashboardLayout>
        <div className="container mx-auto py-8">
          <Alert>
            <AlertDescription>
              Please select a Knowledge Base from the sidebar to start chatting.
            </AlertDescription>
          </Alert>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto h-[calc(100vh-8rem)] flex flex-col p-6">
        {/* Page Header - outside the card */}
        <div className="mb-4">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-8 w-8" />
            <h1 className="text-2xl font-bold">Chat with {activeKb.name}</h1>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Ask questions about your knowledge base
          </p>
        </div>

        {/* Chat Card */}
        <Card className="flex-1 flex flex-col overflow-hidden">
          <CardContent className="flex-1 flex flex-col gap-4 overflow-hidden p-4">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-4">
            {messages.length === 0 && (
              <div className="text-center text-muted-foreground py-8">
                Ask a question about this Knowledge Base
              </div>
            )}
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted"
                  }`}
                >
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-border/50 text-sm">
                      <div className="font-medium mb-1">Sources:</div>
                      {msg.citations.map((cit) => (
                        <div key={cit.number} className="text-xs">
                          [{cit.number}] {cit.document_name}
                          {cit.page && ` - Page ${cit.page}`}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isStreaming && (
              <div className="flex justify-start">
                <div className="bg-muted rounded-lg px-4 py-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="flex gap-2">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question..."
              disabled={isStreaming}
              className="resize-none"
              rows={3}
            />
            <Button
              onClick={sendMessage}
              disabled={!input.trim() || isStreaming}
              size="icon"
            >
              {isStreaming ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
      </div>
    </DashboardLayout>
  );
}
