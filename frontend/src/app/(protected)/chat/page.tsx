'use client';

import { MessageSquare } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent } from '@/components/ui/card';
import { useActiveKb } from '@/lib/stores/kb-store';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { ChatContainer } from '@/components/chat/chat-container';

export default function ChatPage() {
  const activeKb = useActiveKb();

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

        {/* Chat Card with ChatContainer */}
        <Card className="flex-1 flex flex-col overflow-hidden">
          <CardContent className="flex-1 flex flex-col overflow-hidden p-0">
            <ChatContainer kbId={activeKb.id} kbName={activeKb.name} />
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
