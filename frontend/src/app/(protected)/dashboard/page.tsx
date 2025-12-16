'use client';

import { useState, Suspense } from 'react';
import { useUser } from '@/lib/stores/auth-store';
import { useActiveKb, useKbs } from '@/lib/stores/kb-store';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { DocumentsPanel } from '@/components/documents';
import { ProcessingTab } from '@/components/processing';
import { ArchivedTab } from '@/components/documents/archived-tab';

/** Loading skeleton for DocumentsPanel while Suspense resolves */
function DocumentsPanelSkeleton() {
  return (
    <div className="space-y-4">
      {/* Filter bar skeleton */}
      <div className="h-10 bg-muted/30 animate-pulse rounded-md" />
      {/* Document list skeleton */}
      <div className="rounded-md border">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center justify-between border-b px-4 py-3">
            <div className="space-y-2">
              <div className="h-4 w-48 bg-muted animate-pulse rounded" />
              <div className="h-3 w-32 bg-muted animate-pulse rounded" />
            </div>
            <div className="h-6 w-20 bg-muted animate-pulse rounded-full" />
          </div>
        ))}
      </div>
    </div>
  );
}
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Database, FileText, Search, MessageSquare, FolderOpen, Home, Tag, Pencil, Settings2, Archive, Settings } from 'lucide-react';
import Link from 'next/link';
import { OnboardingWizard } from '@/components/onboarding/onboarding-wizard';
import { useOnboarding } from '@/hooks/useOnboarding';
import { KbEditTagsModal } from '@/components/kb/kb-edit-tags-modal';
import { KbSettingsModal } from '@/components/kb/kb-settings-modal';
import { KBActionsMenu } from '@/components/kb/kb-actions-menu';

// Tooltip delay in ms (per AC-5.9.5)
const TOOLTIP_DELAY_MS = 200;

export default function DashboardPage(): React.ReactElement {
  const user = useUser();
  const activeKb = useActiveKb();
  const kbs = useKbs();
  const { isOnboardingComplete, markOnboardingComplete } = useOnboarding();
  const [isEditTagsModalOpen, setIsEditTagsModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);

  // Check if user has ADMIN permission on the active KB
  const isAdmin = activeKb?.permission_level === 'ADMIN';

  // Check if user has WRITE or higher permission (for Processing tab - AC-5.23.4)
  const canViewProcessing = activeKb?.permission_level === 'ADMIN' || activeKb?.permission_level === 'WRITE';

  return (
    <DashboardLayout>
      {/* Onboarding Wizard - Show for first-time users */}
      {!isOnboardingComplete && (
        <OnboardingWizard onComplete={markOnboardingComplete} />
      )}

      <div className="p-6">
        {/* Active KB Header or Welcome Message */}
        {activeKb ? (
          <div className="mb-6">
            <div className="flex items-center gap-2">
              <Database className="h-8 w-8" />
              <h2 className="text-2xl font-bold">{activeKb.name}</h2>
            </div>
            <p className="text-muted-foreground mt-1">
              {activeKb.description || 'Manage documents in this knowledge base'}
            </p>
            <TooltipProvider delayDuration={TOOLTIP_DELAY_MS}>
              <div className="flex items-center gap-2 mt-2">
                <Tag className="h-4 w-4 text-muted-foreground" />
                {activeKb.tags && activeKb.tags.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {activeKb.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="inline-block rounded-md bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary"
                      >
                        {tag}
                      </span>
                    ))}
                    {activeKb.tags.length > 3 && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="inline-block rounded-md bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground cursor-default">
                            +{activeKb.tags.length - 3} more
                          </span>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>{activeKb.tags.slice(3).join(', ')}</p>
                        </TooltipContent>
                      </Tooltip>
                    )}
                  </div>
                ) : (
                  <span className="text-xs text-muted-foreground">No tags</span>
                )}
                {isAdmin && (
                  <>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 ml-1"
                      aria-label="Edit tags"
                      onClick={() => setIsEditTagsModalOpen(true)}
                    >
                      <Pencil className="h-3 w-3" />
                    </Button>
                    {/* Story 7-10: KB Settings button (AC-7.10.5) */}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      aria-label="KB Settings"
                      onClick={() => setIsSettingsModalOpen(true)}
                    >
                      <Settings className="h-3 w-3" />
                    </Button>
                    {/* KB Actions Menu (archive/delete) */}
                    <KBActionsMenu
                      kb={activeKb}
                      onSettingsClick={() => setIsSettingsModalOpen(true)}
                    />
                  </>
                )}
              </div>
            </TooltipProvider>
          </div>
        ) : (
          <div className="mb-8">
            <div className="flex items-center gap-2">
              <Home className="h-8 w-8" />
              <h2 className="text-2xl font-bold">
                Welcome back{user?.email ? `, ${user.email.split('@')[0]}` : ''}!
              </h2>
            </div>
            <p className="text-muted-foreground mt-1">Your knowledge base dashboard</p>
          </div>
        )}

        {/* Quick Access Cards - Always show when KB is active */}
        {activeKb && (
          <TooltipProvider delayDuration={TOOLTIP_DELAY_MS}>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Link href="/search">
                    <Card className="cursor-pointer hover:bg-accent transition-colors">
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Search</CardTitle>
                        <Search className="h-4 w-4 text-muted-foreground" />
                      </CardHeader>
                      <CardContent>
                        <p className="text-xs text-muted-foreground">Find answers with citations</p>
                      </CardContent>
                    </Card>
                  </Link>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Tip: Use natural language queries for best results</p>
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Link href="/chat">
                    <Card className="cursor-pointer hover:bg-accent transition-colors">
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Chat</CardTitle>
                        <MessageSquare className="h-4 w-4 text-muted-foreground" />
                      </CardHeader>
                      <CardContent>
                        <p className="text-xs text-muted-foreground">Ask AI questions</p>
                      </CardContent>
                    </Card>
                  </Link>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Tip: Start a conversation to get detailed answers from your documents</p>
                </TooltipContent>
              </Tooltip>
            </div>
          </TooltipProvider>
        )}

        {/* Show Documents/Processing tabs when KB is active */}
        {activeKb ? (
          <Tabs defaultValue="documents" className="space-y-4">
            <TabsList>
              <TabsTrigger value="documents" className="gap-2">
                <FileText className="h-4 w-4" />
                Documents
              </TabsTrigger>
              {canViewProcessing && (
                <TabsTrigger value="processing" className="gap-2">
                  <Settings2 className="h-4 w-4" />
                  Processing
                </TabsTrigger>
              )}
              {canViewProcessing && (
                <TabsTrigger value="archived" className="gap-2">
                  <Archive className="h-4 w-4" />
                  Archived
                </TabsTrigger>
              )}
            </TabsList>

            <TabsContent value="documents" className="mt-0">
              <Suspense fallback={<DocumentsPanelSkeleton />}>
                <DocumentsPanel kbId={activeKb.id} userPermission={activeKb.permission_level || 'READ'} />
              </Suspense>
            </TabsContent>

            {canViewProcessing && (
              <TabsContent value="processing" className="mt-0">
                <ProcessingTab kbId={activeKb.id} />
              </TabsContent>
            )}

            {canViewProcessing && (
              <TabsContent value="archived" className="mt-0">
                <ArchivedTab kbId={activeKb.id} />
              </TabsContent>
            )}
          </Tabs>
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

              <Link href="/search">
                <Card className="cursor-pointer hover:bg-accent transition-colors">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Search Knowledge Base</CardTitle>
                    <Search className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <p className="text-xs text-muted-foreground">Semantic search with citations</p>
                  </CardContent>
                </Card>
              </Link>

              <Link href="/chat">
                <Card className="cursor-pointer hover:bg-accent transition-colors">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Chat</CardTitle>
                    <MessageSquare className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <p className="text-xs text-muted-foreground">Ask questions, get AI answers</p>
                  </CardContent>
                </Card>
              </Link>
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
                      semantic search to find answers with citations
                    </p>
                    <p>
                      <strong className="text-foreground">4. Chat with AI</strong> - Have conversations
                      about your knowledge base with AI-powered responses
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

      {/* Edit Tags Modal - Only for admin users */}
      {activeKb && isAdmin && (
        <KbEditTagsModal
          open={isEditTagsModalOpen}
          onOpenChange={setIsEditTagsModalOpen}
          kbId={activeKb.id}
          kbName={activeKb.name}
          currentTags={activeKb.tags || []}
        />
      )}

      {/* Story 7-10: KB Settings Modal - Only for admin users (AC-7.10.5-7) */}
      {activeKb && isAdmin && (
        <KbSettingsModal
          open={isSettingsModalOpen}
          onOpenChange={setIsSettingsModalOpen}
          kb={activeKb}
        />
      )}
    </DashboardLayout>
  );
}
