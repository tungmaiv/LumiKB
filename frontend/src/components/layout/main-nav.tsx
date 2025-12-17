'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home,
  Search,
  MessageSquare,
  Activity,
  FileSearch,
  Server,
  Settings,
  Database,
  ChevronDown,
  Shield,
  Users,
  Users2,
  Wrench,
  Cpu,
  Bot,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { useIsOperator, useIsAdministrator } from '@/lib/stores/auth-store';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface NavLinkProps {
  href: string;
  icon: React.ElementType;
  label: string;
  isActive: boolean;
}

function NavLink({ href, icon: Icon, label, isActive }: NavLinkProps): React.ReactElement {
  return (
    <Link
      href={href}
      className={cn(
        'flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors',
        'hover:bg-accent hover:text-accent-foreground',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
        isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground'
      )}
      aria-current={isActive ? 'page' : undefined}
      aria-label={label}
      title={label}
    >
      <Icon className="h-4 w-4" aria-hidden="true" />
      <span className="hidden lg:inline">{label}</span>
    </Link>
  );
}

interface MainNavProps {
  className?: string;
}

/**
 * MainNav - Horizontal navigation component for desktop/laptop viewports
 *
 * Features:
 * - Core links: Dashboard, Search, Chat (visible to all authenticated users)
 * - Operations dropdown: Visible to Operators (level 2+) - AC-7.11.2, AC-7.11.4
 * - Admin dropdown: Visible to Administrators (level 3) - AC-7.11.1, AC-7.11.5
 * - Active route highlighting with usePathname()
 * - Tooltips for accessibility
 * - Responsive: icons-only on tablet, icons+labels on desktop
 *
 * AC-7.11.1: Administrators see both "Operations" and "Admin" dropdowns
 * AC-7.11.2: Operators see only "Operations" dropdown
 * AC-7.11.3: Basic Users see neither dropdown (only core links)
 * AC-7.11.4: Operations dropdown items
 * AC-7.11.5: Admin dropdown items
 */
export function MainNav({ className }: MainNavProps): React.ReactElement {
  const pathname = usePathname();
  const isOperator = useIsOperator();
  const isAdministrator = useIsAdministrator();

  // Check if currently on operations or admin routes
  const isOnOperationsRoute = pathname?.startsWith('/operations') ?? false;
  const isOnAdminRoute = pathname?.startsWith('/admin') ?? false;

  // Check if route is active (exact match or starts with for subroutes)
  const isActive = (href: string): boolean => {
    if (href === '/dashboard') {
      return pathname === '/dashboard' || pathname === '/';
    }
    return pathname === href || pathname?.startsWith(href + '/');
  };

  const coreLinks = [
    { href: '/dashboard', icon: Home, label: 'Dashboard' },
    { href: '/search', icon: Search, label: 'Search' },
    { href: '/chat', icon: MessageSquare, label: 'Chat' },
  ];

  // Operations menu items (AC-7.11.4)
  const operationsLinks = [
    { href: '/operations', icon: Wrench, label: 'Operations Dashboard' },
    { href: '/operations/audit', icon: FileSearch, label: 'Audit Logs' },
    { href: '/operations/queue', icon: Activity, label: 'Processing Queue' },
    { href: '/operations/kb-stats', icon: Database, label: 'KB Statistics' },
  ];

  // Admin menu items (AC-7.11.5)
  const adminLinks = [
    { href: '/admin', icon: Server, label: 'Admin Dashboard' },
    { href: '/admin/users', icon: Users, label: 'Users' },
    { href: '/admin/groups', icon: Users2, label: 'Groups' },
    { href: '/admin/kb-permissions', icon: Shield, label: 'KB Permissions' },
    { href: '/admin/config', icon: Settings, label: 'System Config' },
    { href: '/admin/config/llm', icon: Bot, label: 'LLM Configuration' },
    { href: '/admin/models', icon: Cpu, label: 'Model Registry' },
  ];

  return (
    <nav
      className={cn('flex items-center gap-2', className)}
      role="navigation"
      aria-label="Main navigation"
    >
      {/* Core Navigation Links - visible to all authenticated users */}
      <ul className="flex items-center gap-1" role="list">
        {coreLinks.map((link) => (
          <li key={link.href}>
            <NavLink
              href={link.href}
              icon={link.icon}
              label={link.label}
              isActive={isActive(link.href)}
            />
          </li>
        ))}
      </ul>

      {/* Operations Dropdown - visible to Operators (level 2+) - AC-7.11.2, AC-7.11.4 */}
      {isOperator && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                'hover:bg-accent hover:text-accent-foreground',
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                isOnOperationsRoute ? 'bg-accent text-accent-foreground' : 'text-muted-foreground'
              )}
              aria-label="Operations menu"
            >
              <Wrench className="h-4 w-4" aria-hidden="true" />
              <span className="hidden lg:inline">Operations</span>
              <ChevronDown className="h-3 w-3" aria-hidden="true" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-48">
            {operationsLinks.map((link) => (
              <DropdownMenuItem key={link.href} asChild>
                <Link
                  href={link.href}
                  className={cn(
                    'flex items-center gap-2 w-full',
                    isActive(link.href) && 'bg-accent'
                  )}
                >
                  <link.icon className="h-4 w-4" aria-hidden="true" />
                  <span>{link.label}</span>
                </Link>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      )}

      {/* Admin Dropdown - visible to Administrators (level 3) - AC-7.11.1, AC-7.11.5 */}
      {isAdministrator && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                'hover:bg-accent hover:text-accent-foreground',
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                isOnAdminRoute ? 'bg-accent text-accent-foreground' : 'text-muted-foreground'
              )}
              aria-label="Admin menu"
            >
              <Shield className="h-4 w-4" aria-hidden="true" />
              <span className="hidden lg:inline">Admin</span>
              <ChevronDown className="h-3 w-3" aria-hidden="true" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-48">
            {adminLinks.map((link) => (
              <DropdownMenuItem key={link.href} asChild>
                <Link
                  href={link.href}
                  className={cn(
                    'flex items-center gap-2 w-full',
                    isActive(link.href) && 'bg-accent'
                  )}
                >
                  <link.icon className="h-4 w-4" aria-hidden="true" />
                  <span>{link.label}</span>
                </Link>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </nav>
  );
}
