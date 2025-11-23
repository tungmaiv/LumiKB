'use client';

import { useUser } from '@/lib/stores/auth-store';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Database, FileText, Search, MessageSquare } from 'lucide-react';

export default function DashboardPage(): React.ReactElement {
  const user = useUser();

  return (
    <DashboardLayout>
      <div className="p-6">
        {/* Welcome Message */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold">
            Welcome back{user?.email ? `, ${user.email.split('@')[0]}` : ''}!
          </h2>
          <p className="text-muted-foreground">Your knowledge base dashboard</p>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Knowledge Bases</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">4</div>
              <p className="text-xs text-muted-foreground">placeholder count</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Documents</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">311</div>
              <p className="text-xs text-muted-foreground">placeholder count</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Searches</CardTitle>
              <Search className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">-</div>
              <p className="text-xs text-muted-foreground">Coming in Epic 3</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Conversations</CardTitle>
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">-</div>
              <p className="text-xs text-muted-foreground">Coming in Epic 4</p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Area */}
        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Getting Started</CardTitle>
              <CardDescription>
                Welcome to LumiKB - your AI-powered knowledge base management system
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 text-sm text-muted-foreground">
                <p>
                  <strong className="text-foreground">1. Create a Knowledge Base</strong> - Use the
                  sidebar to create your first knowledge base (coming in Epic 2)
                </p>
                <p>
                  <strong className="text-foreground">2. Upload Documents</strong> - Add PDFs, Word
                  docs, and text files to your knowledge base
                </p>
                <p>
                  <strong className="text-foreground">3. Search & Ask Questions</strong> - Use
                  semantic search to find answers with citations (coming in Epic 3)
                </p>
                <p>
                  <strong className="text-foreground">4. Generate Content</strong> - Create new
                  documents based on your knowledge (coming in Epic 4)
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
