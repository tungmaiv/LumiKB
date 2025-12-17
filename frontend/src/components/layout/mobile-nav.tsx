'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Database,
  FileText,
  Home,
  Search,
  MessageSquare,
  Activity,
  FileSearch,
  Server,
  Settings,
  Users,
  Users2,
  ChevronUp,
  ChevronDown,
  Wrench,
  Shield,
  Cpu,
  Bot,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useIsOperator, useIsAdministrator } from '@/lib/stores/auth-store';

interface MobileNavProps {
  onSidebarOpen?: () => void;
  onCitationsOpen?: () => void;
}

interface MobileNavLinkProps {
  href: string;
  icon: React.ElementType;
  label: string;
  isActive: boolean;
}

function MobileNavLink({
  href,
  icon: Icon,
  label,
  isActive,
}: MobileNavLinkProps): React.ReactElement {
  return (
    <Link
      href={href}
      className={cn(
        'flex flex-col items-center justify-center gap-1 h-auto py-2 px-3 min-w-[56px] min-h-[44px]',
        'rounded-md transition-colors',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        isActive
          ? 'text-primary bg-accent'
          : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
      )}
      aria-current={isActive ? 'page' : undefined}
      aria-label={label}
    >
      <Icon className="h-5 w-5" aria-hidden="true" />
      <span className="text-[10px]">{label}</span>
    </Link>
  );
}

/**
 * MobileNav - Bottom navigation bar for mobile viewports (<768px)
 *
 * Features:
 * - Core links: Dashboard, Search, Chat with real routing
 * - KBs button opens KB sidebar sheet
 * - Citations button opens citations sheet
 * - Operations section: Expandable menu for Operators (level 2+)
 * - Admin section: Expandable menu for Administrators (level 3)
 * - Touch-friendly tap targets (min 44x44px per WCAG 2.5.5)
 * - Active route highlighting
 *
 * AC-7.11.1: Administrators see both "Operations" and "Admin" sections
 * AC-7.11.2: Operators see only "Operations" section
 * AC-7.11.3: Basic Users see neither section
 * AC-5.17.5: Mobile navigation
 * AC-5.17.6: Accessibility
 */
export function MobileNav({ onSidebarOpen, onCitationsOpen }: MobileNavProps): React.ReactElement {
  const pathname = usePathname();
  const isOperator = useIsOperator();
  const isAdministrator = useIsAdministrator();
  const [menuOpen, setMenuOpen] = useState<'operations' | 'admin' | null>(null);

  // Check if route is active
  const isActive = (href: string): boolean => {
    if (href === '/dashboard') {
      return pathname === '/dashboard' || pathname === '/';
    }
    return pathname === href || pathname?.startsWith(href + '/');
  };

  // Check if on operations or admin routes
  const isOnOperationsRoute = pathname?.startsWith('/operations') ?? false;
  const isOnAdminRoute = pathname?.startsWith('/admin') ?? false;

  // Operations menu items (AC-7.11.4)
  const operationsLinks = [
    { href: '/operations', icon: Wrench, label: 'Overview' },
    { href: '/operations/audit', icon: FileSearch, label: 'Audit' },
    { href: '/operations/queue', icon: Activity, label: 'Queue' },
    { href: '/operations/kb-stats', icon: Database, label: 'KB Stats' },
  ];

  // Admin menu items (AC-7.11.5)
  const adminLinks = [
    { href: '/admin', icon: Server, label: 'Overview' },
    { href: '/admin/users', icon: Users, label: 'Users' },
    { href: '/admin/groups', icon: Users2, label: 'Groups' },
    { href: '/admin/kb-permissions', icon: Shield, label: 'KB Perms' },
    { href: '/admin/config', icon: Settings, label: 'Config' },
    { href: '/admin/config/llm', icon: Bot, label: 'LLM' },
    { href: '/admin/models', icon: Cpu, label: 'Models' },
  ];

  const toggleMenu = (menu: 'operations' | 'admin') => {
    setMenuOpen(menuOpen === menu ? null : menu);
  };

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50 border-t bg-background"
      role="navigation"
      aria-label="Mobile navigation"
    >
      {/* Operations Section Expandable (slides up from bottom nav) */}
      {isOperator && menuOpen === 'operations' && (
        <div
          className="border-t bg-background/95 backdrop-blur animate-in slide-in-from-bottom-2 duration-200"
          role="region"
          aria-label="Operations navigation"
        >
          <div className="flex items-center justify-around px-2 py-2">
            {operationsLinks.map((link) => (
              <MobileNavLink
                key={link.href}
                href={link.href}
                icon={link.icon}
                label={link.label}
                isActive={isActive(link.href)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Admin Section Expandable (slides up from bottom nav) */}
      {isAdministrator && menuOpen === 'admin' && (
        <div
          className="border-t bg-background/95 backdrop-blur animate-in slide-in-from-bottom-2 duration-200"
          role="region"
          aria-label="Admin navigation"
        >
          <div className="flex items-center justify-around px-2 py-2">
            {adminLinks.map((link) => (
              <MobileNavLink
                key={link.href}
                href={link.href}
                icon={link.icon}
                label={link.label}
                isActive={isActive(link.href)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Main Bottom Navigation */}
      <div className="flex h-16 items-center justify-around px-2">
        {/* KB Sidebar Button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onSidebarOpen}
          className={cn('flex flex-col gap-1 h-auto py-2 min-w-[56px] min-h-[44px]')}
          aria-label="Open Knowledge Bases"
        >
          <Database className="h-5 w-5" aria-hidden="true" />
          <span className="text-[10px]">KBs</span>
        </Button>

        {/* Core Navigation Links */}
        <MobileNavLink
          href="/dashboard"
          icon={Home}
          label="Home"
          isActive={isActive('/dashboard')}
        />

        <MobileNavLink href="/search" icon={Search} label="Search" isActive={isActive('/search')} />

        <MobileNavLink
          href="/chat"
          icon={MessageSquare}
          label="Chat"
          isActive={isActive('/chat')}
        />

        {/* Operations Toggle Button (for Operators level 2+) */}
        {isOperator && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => toggleMenu('operations')}
            className={cn(
              'flex flex-col gap-1 h-auto py-2 min-w-[56px] min-h-[44px]',
              isOnOperationsRoute && 'text-primary'
            )}
            aria-label={
              menuOpen === 'operations' ? 'Close operations menu' : 'Open operations menu'
            }
            aria-expanded={menuOpen === 'operations'}
          >
            <Wrench className="h-5 w-5" aria-hidden="true" />
            <span className="text-[10px] flex items-center gap-0.5">
              Ops
              {menuOpen === 'operations' ? (
                <ChevronDown className="h-3 w-3" aria-hidden="true" />
              ) : (
                <ChevronUp className="h-3 w-3" aria-hidden="true" />
              )}
            </span>
          </Button>
        )}

        {/* Admin Toggle Button (for Administrators level 3) */}
        {isAdministrator && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => toggleMenu('admin')}
            className={cn(
              'flex flex-col gap-1 h-auto py-2 min-w-[56px] min-h-[44px]',
              isOnAdminRoute && 'text-primary'
            )}
            aria-label={menuOpen === 'admin' ? 'Close admin menu' : 'Open admin menu'}
            aria-expanded={menuOpen === 'admin'}
          >
            <Shield className="h-5 w-5" aria-hidden="true" />
            <span className="text-[10px] flex items-center gap-0.5">
              Admin
              {menuOpen === 'admin' ? (
                <ChevronDown className="h-3 w-3" aria-hidden="true" />
              ) : (
                <ChevronUp className="h-3 w-3" aria-hidden="true" />
              )}
            </span>
          </Button>
        )}

        {/* Citations Button (only show if no permission menus, to save space) */}
        {!isOperator && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onCitationsOpen}
            className={cn('flex flex-col gap-1 h-auto py-2 min-w-[56px] min-h-[44px]')}
            aria-label="Open Citations"
          >
            <FileText className="h-5 w-5" aria-hidden="true" />
            <span className="text-[10px]">Citations</span>
          </Button>
        )}
      </div>
    </nav>
  );
}
