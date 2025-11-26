'use client';

import { useUser } from '@/lib/stores/auth-store';
import { useActiveKb, useKbs } from '@/lib/stores/kb-store';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { DocumentsPanel } from '@/components/documents';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Database, FileText, Search, MessageSquare, FolderOpen } from 'lucide-react';

export default function DashboardPage(): React.ReactElement {
  const user = useUser();
  const activeKb = useActiveKb();
  const kbs = useKbs();

  return (
    <DashboardLayout>
      <div className="p-6">
        {/* Active KB Header or Welcome Message */}
        {activeKb ? (
          <div className="mb-6">
            <h2 className="text-2xl font-bold">{activeKb.name}</h2>
            <p className="text-muted-foreground">
              {activeKb.description || 'Manage documents in this knowledge base'}
            </p>
          </div>
        ) : (
          <div className="mb-8">
            <h2 className="text-2xl font-bold">
              Welcome back{user?.email ? `, ${user.email.split('@')[0]}` : ''}!
            </h2>
            <p className="text-muted-foreground">Your knowledge base dashboard</p>
          </div>
        )}

        {/* Show Documents Panel when KB is active */}
        {activeKb ? (
          <DocumentsPanel kbId={activeKb.id} userPermission={activeKb.permission_level || 'READ'} />
        ) : kbs.length === 0 ? (
          /* No KBs - Show Getting Started */
          <>
            {/* Quick Stats Grid */}
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Knowledge Bases</CardTitle>
                  <Database className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">0</div>
                  <p className="text-xs text-muted-foreground">Create your first KB</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Documents</CardTitle>
                  <FileText className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">0</div>
                  <p className="text-xs text-muted-foreground">Upload documents to search</p>
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
                      <strong className="text-foreground">1. Create a Knowledge Base</strong> - Use
                      the sidebar to create your first knowledge base
                    </p>
                    <p>
                      <strong className="text-foreground">2. Upload Documents</strong> - Add PDFs,
                      Word docs, and Markdown files to your knowledge base
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
          </>
        ) : (
          /* KBs exist but none selected - prompt to select */
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <FolderOpen className="h-16 w-16 text-muted-foreground/50 mb-4" />
            <h3 className="text-xl font-medium mb-2">Select a Knowledge Base</h3>
            <p className="text-muted-foreground max-w-md">
              Choose a knowledge base from the sidebar to view and manage its documents.
            </p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
