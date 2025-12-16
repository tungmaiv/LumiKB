/**
 * Chat container component - orchestrates messages, input, and streaming
 * Epic 4, Stories 4.2 and 4.3
 */

'use client';

import { useRef, useEffect, useState } from 'react';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import { useChatStream } from '@/lib/hooks/use-chat-stream';
import { useChatManagement } from '@/hooks/useChatManagement';
import type { ChatMessage as ChatMessageType } from '@/lib/api/chat';
import { ChatMessage } from './chat-message';
import { ChatInput } from './chat-input';
import { ClearChatDialog } from './clear-chat-dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertCircle, MessageSquarePlus, Trash2, Undo2 } from 'lucide-react';

export interface ChatContainerProps {
  kbId: string;
  kbName?: string;
  conversationId?: string;
}

/**
 * Main chat interface component
 * Manages message list, streaming, and input
 */
export function ChatContainer({ kbId, kbName, conversationId }: ChatContainerProps) {
  const {
    messages,
    isStreaming,
    sendMessage,
    error,
    clearMessages,
    restoreMessages,
    abortStream,
  } = useChatStream({
    kbId,
    conversationId,
  });

  // Undo buffer state (stores cleared messages for 30s)
  // Initialize from localStorage to survive page reload (Option A fix)
  const [undoBuffer, setUndoBuffer] = useState<ChatMessageType[]>(() => {
    if (typeof window === 'undefined') return [];
    const stored = localStorage.getItem('chat-undo-buffer');
    if (!stored) return [];
    try {
      const parsed = JSON.parse(stored) as Array<{
        role: 'user' | 'assistant';
        content: string;
        timestamp: string;
        citations?: Array<{
          number: number;
          documentId: string;
          documentName: string;
          pageNumber?: number;
          sectionHeader?: string;
          excerpt: string;
          confidence?: number;
        }>;
        confidence?: number;
      }>;
      // Convert timestamp strings back to Date objects
      return parsed.map((msg) => ({
        ...msg,
        timestamp: new Date(msg.timestamp),
        citations: msg.citations || [],
      }));
    } catch {
      return [];
    }
  });

  // Clear chat dialog state
  const [clearDialogOpen, setClearDialogOpen] = useState(false);

  const {
    startNewChat,
    clearChat,
    undoClear,
    undoAvailable,
    undoSecondsRemaining,
    isLoading: isManagementLoading,
  } = useChatManagement({
    onMessagesClear: () => {
      // Store messages in undo buffer before clearing (persist to localStorage)
      const bufferCopy = [...messages];
      setUndoBuffer(bufferCopy);
      // Persist to localStorage for page reload survival (Option A fix)
      localStorage.setItem('chat-undo-buffer', JSON.stringify(bufferCopy));
      clearMessages();
    },
    onMessagesRestore: () => {
      // Restore messages from undo buffer
      restoreMessages(undoBuffer);
      setUndoBuffer([]);
      // Clear localStorage buffer after restore
      localStorage.removeItem('chat-undo-buffer');
    },
    onAbortStream: () => {
      abortStream();
    },
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleNewChat = async () => {
    try {
      await startNewChat(kbId);
      // Clear undo buffer when starting new chat
      setUndoBuffer([]);
      localStorage.removeItem('chat-undo-buffer');
    } catch (err) {
      // Error handled in hook
      console.error('Failed to start new chat:', err);
    }
  };

  // Keyboard shortcut: Cmd/Ctrl+Shift+N for New Chat
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.shiftKey && event.key === 'N') {
        event.preventDefault();
        void handleNewChat();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [kbId]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleClearChat = () => {
    setClearDialogOpen(true);
  };

  const handleConfirmClear = async () => {
    try {
      await clearChat(kbId);

      // Show undo toast with countdown
      toast('Chat cleared', {
        description: `You can undo this action for ${undoSecondsRemaining} seconds`,
        duration: 30000,
        action: {
          label: 'Undo',
          onClick: handleUndoClear,
        },
      });
    } catch (err) {
      console.error('Failed to clear chat:', err);
      toast.error('Failed to clear chat', {
        description: err instanceof Error ? err.message : 'Unknown error',
      });
    }
  };

  const handleUndoClear = async () => {
    try {
      await undoClear(kbId);
      toast.success('Conversation restored');
    } catch (err) {
      console.error('Failed to undo clear:', err);
      toast.error('Failed to restore conversation', {
        description: err instanceof Error ? err.message : 'Unknown error',
      });
    }
  };

  return (
    <div className="flex flex-col h-full" data-testid="chat-container">
      {/* Header with management buttons */}
      <div className="border-b p-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleNewChat}
            disabled={isStreaming || isManagementLoading}
            data-testid="new-chat-button"
          >
            <MessageSquarePlus className="h-4 w-4 mr-1" />
            New Chat
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearChat}
            disabled={isStreaming || isManagementLoading || messages.length === 0}
            data-testid="clear-chat-button"
          >
            <Trash2 className="h-4 w-4 mr-1" />
            Clear Chat
          </Button>

          {undoAvailable && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleUndoClear}
              disabled={isStreaming || isManagementLoading}
              data-testid="undo-clear-button"
            >
              <Undo2 className="h-4 w-4 mr-1" />
              Undo Clear ({undoSecondsRemaining}s)
            </Button>
          )}
        </div>

        <div className="text-xs text-muted-foreground space-y-0.5">
          {kbName && <div className="font-medium">{kbName}</div>}
          {messages.length > 0 ? (
            <>
              <div>{Math.floor(messages.length / 2)} messages</div>
              {messages[0]?.timestamp && (
                <div>
                  Started {formatDistanceToNow(messages[0].timestamp, { addSuffix: true })}
                </div>
              )}
            </>
          ) : (
            <div>No messages yet</div>
          )}
        </div>
      </div>

      {/* Message List */}
      <div
        className="flex-1 overflow-y-auto p-4 space-y-4"
        data-testid="chat-messages-container"
      >
        {messages.length === 0 && (
          <div className="text-center text-muted-foreground mt-8">
            <p>Start a conversation by asking a question about this Knowledge Base.</p>
          </div>
        )}

        {messages.map((message, index) => (
          <ChatMessage
            key={`${message.role}-${index}-${message.timestamp.getTime()}`}
            role={message.role}
            content={message.content}
            timestamp={message.timestamp}
            citations={message.citations}
            confidence={message.confidence}
          />
        ))}

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput
        onSendMessage={sendMessage}
        disabled={isStreaming}
        placeholder="Ask a question about this Knowledge Base..."
      />

      {/* Clear Chat Dialog */}
      <ClearChatDialog
        open={clearDialogOpen}
        onOpenChange={setClearDialogOpen}
        onConfirm={handleConfirmClear}
      />
    </div>
  );
}
