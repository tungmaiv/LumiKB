'use client';

import { useState } from 'react';
import { Header } from '@/components/layout/header';
import { KbSidebar } from '@/components/layout/kb-sidebar';
import { CitationsPanel } from '@/components/layout/citations-panel';
import { MobileNav } from '@/components/layout/mobile-nav';
import { useResponsiveLayout } from '@/hooks/use-responsive-layout';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps): React.ReactElement {
  const { isDesktop, isLaptop, isTablet, isMobile } = useResponsiveLayout();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [citationsOpen, setCitationsOpen] = useState(false);
  const [citationsCollapsed, setCitationsCollapsed] = useState(false);

  // Show three-panel on desktop
  const showSidebar = isDesktop || isLaptop;
  const showCitations = isDesktop;
  const showMobileNav = isMobile;
  const showMenuButton = isTablet || isMobile;

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <Header showMenuButton={showMenuButton} onMenuClick={() => setSidebarOpen(true)} />

      <div className="flex flex-1 overflow-hidden">
        {/* Desktop/Laptop Sidebar */}
        {showSidebar && (
          <aside className="hidden w-[260px] shrink-0 border-r lg:block">
            <KbSidebar />
          </aside>
        )}

        {/* Mobile/Tablet Sidebar Sheet */}
        <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
          <SheetContent side="left" className="w-[260px] p-0">
            <SheetHeader className="sr-only">
              <SheetTitle>Knowledge Bases</SheetTitle>
            </SheetHeader>
            <KbSidebar />
          </SheetContent>
        </Sheet>

        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          <div className={isMobile ? 'pb-16' : ''}>{children}</div>
        </main>

        {/* Desktop Citations Panel */}
        {showCitations && (
          <CitationsPanel
            isCollapsed={citationsCollapsed}
            onToggle={() => setCitationsCollapsed(!citationsCollapsed)}
          />
        )}

        {/* Laptop Citations Toggle Button */}
        {isLaptop && !citationsOpen && (
          <button
            onClick={() => setCitationsOpen(true)}
            className="fixed bottom-4 right-4 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transition-transform hover:scale-105"
            aria-label="Open citations"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          </button>
        )}

        {/* Laptop/Tablet Citations Sheet */}
        {(isLaptop || isTablet) && (
          <Sheet open={citationsOpen} onOpenChange={setCitationsOpen}>
            <SheetContent side="right" className="w-[320px] p-0">
              <SheetHeader className="sr-only">
                <SheetTitle>Citations</SheetTitle>
              </SheetHeader>
              <CitationsPanel onToggle={() => setCitationsOpen(false)} />
            </SheetContent>
          </Sheet>
        )}

        {/* Mobile Citations Sheet (full screen) */}
        {isMobile && (
          <Sheet open={citationsOpen} onOpenChange={setCitationsOpen}>
            <SheetContent side="bottom" className="h-[80vh] p-0">
              <SheetHeader className="sr-only">
                <SheetTitle>Citations</SheetTitle>
              </SheetHeader>
              <CitationsPanel onToggle={() => setCitationsOpen(false)} />
            </SheetContent>
          </Sheet>
        )}
      </div>

      {/* Mobile Bottom Navigation */}
      {showMobileNav && (
        <MobileNav
          onSidebarOpen={() => setSidebarOpen(true)}
          onCitationsOpen={() => setCitationsOpen(true)}
        />
      )}
    </div>
  );
}
