'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '../../contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  FileText,
  Users,
  BarChart3,
  Bot,
  Hammer,
  Settings,
  Zap,
  UsersRound,
  User,
  LogOut,
  Rocket,
  Shield
} from 'lucide-react'

interface NavItemProps {
  href: string
  icon: React.ComponentType<{ className?: string }>
  label: string
  isActive: boolean
  badge?: string
}

function NavItem({ href, icon: Icon, label, isActive, badge }: NavItemProps) {
  return (
    <Link href={href}>
      <Button
        variant={isActive ? "secondary" : "ghost"}
        className={cn(
          "w-full justify-start gap-3 h-10 px-3",
          isActive 
            ? "bg-primary/10 text-primary border-r-2 border-primary" 
            : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
        )}
      >
        <Icon className="h-4 w-4 flex-shrink-0" />
        <span className="flex-1 text-left">{label}</span>
        {badge && (
          <Badge variant="secondary" className="ml-auto text-xs">
            {badge}
          </Badge>
        )}
      </Button>
    </Link>
  )
}

export default function Navigation() {
  const pathname = usePathname()
  const { user, signOut } = useAuth()
  
  const isActive = (path: string) => pathname === path

  const handleSignOut = async () => {
    await signOut()
  }

  const mainNavItems = [
    { href: '/admin', icon: LayoutDashboard, label: 'Dashboard' },
    { href: '/admin/templates', icon: FileText, label: 'Templates' },
    { href: '/admin/tenants', icon: Users, label: 'Tenants' },
    { href: '/admin/metrics', icon: BarChart3, label: 'Métricas' },
    { href: '/mcp', icon: Bot, label: 'MCP Protocol', badge: 'Beta' }
  ]

  const adminNavItems = [
    { href: '/admin/builder', icon: Hammer, label: 'Builder' },
    { href: '/admin/configuration/apis', icon: Settings, label: 'Config APIs' },
    { href: '/admin/agents', icon: Zap, label: 'Agentes IA' },
    { href: '/admin/agents/teams', icon: UsersRound, label: 'Equipos' }
  ]

  return (
    <nav className="flex h-screen w-64 flex-col border-r bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      {/* Header */}
      <div className="p-6 pb-4">
        <div className="flex items-center gap-2 mb-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <Rocket className="h-4 w-4 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight">TauseStack</h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">
            v1.0.0
          </Badge>
          <Badge variant="secondary" className="text-xs">
            Multi-Tenant
          </Badge>
        </div>
      </div>

      {/* Main Navigation */}
      <div className="flex-1 px-4 pb-4">
        <div className="space-y-1 mb-6">
          {mainNavItems.map((item) => (
            <NavItem
              key={item.href}
              href={item.href}
              icon={item.icon}
              label={item.label}
              isActive={isActive(item.href)}
              badge={item.badge}
            />
          ))}
        </div>

                 <div className="my-4 h-px bg-border" />

        {/* Admin Section */}
        <div className="space-y-1">
          <div className="px-3 py-2">
            <h3 className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Administración
            </h3>
          </div>
          {adminNavItems.map((item) => (
            <NavItem
              key={item.href}
              href={item.href}
              icon={item.icon}
              label={item.label}
              isActive={isActive(item.href)}
            />
          ))}
        </div>
      </div>

      {/* User Section */}
      <div className="p-4 border-t">
        {/* User Info */}
        <div className="mb-4 p-3 rounded-lg bg-muted/50">
          <div className="flex items-center gap-3 mb-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary">
              <User className="h-4 w-4 text-primary-foreground" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">
                {user?.email || 'admin@tausestack.dev'}
              </p>
              <div className="flex items-center gap-2 mt-1">
                <Shield className="h-3 w-3 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">Admin Access</span>
              </div>
            </div>
          </div>
        </div>

        {/* Logout Button */}
        <Button
          variant="outline"
          className="w-full justify-start gap-3 h-10 text-muted-foreground hover:text-foreground"
          onClick={handleSignOut}
        >
          <LogOut className="h-4 w-4" />
          Cerrar Sesión
        </Button>

        {/* Version Info */}
        <div className="mt-4 p-2 text-center">
          <p className="text-xs text-muted-foreground">
            AI-Powered Multi-Tenant Platform
          </p>
        </div>
      </div>
    </nav>
  )
} 