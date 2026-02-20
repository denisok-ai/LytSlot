/**
 * @file: DashboardShell.tsx
 * @description: Оболочка дашборда — сайдбар + контент (навигация, UX).
 * @dependencies: next/link, lucide-react
 */
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Radio,
  Calendar,
  ShoppingBag,
  BarChart3,
  Settings,
  LogOut,
} from "lucide-react";
import { clsx } from "clsx";

const nav = [
  { href: "/dashboard", label: "Обзор", icon: LayoutDashboard },
  { href: "/dashboard/channels", label: "Каналы", icon: Radio },
  { href: "/dashboard/calendar", label: "Календарь", icon: Calendar },
  { href: "/dashboard/orders", label: "Заказы", icon: ShoppingBag },
  { href: "/dashboard/analytics", label: "Аналитика", icon: BarChart3 },
  { href: "/dashboard/settings", label: "Настройки", icon: Settings },
];

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="fixed inset-y-0 left-0 z-40 w-64 flex flex-col border-r border-slate-200/80 bg-white shadow-sm">
        <div className="flex h-16 items-center gap-2 border-b border-slate-100 px-6">
          <Link
            href="/"
            className="flex items-center gap-2 font-display text-xl font-bold text-slate-900"
          >
            LytSlot <span className="text-emerald-600">Pro</span>
          </Link>
        </div>
        <nav className="flex-1 space-y-0.5 p-3" aria-label="Основная навигация">
          {nav.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(href + "/");
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  active
                    ? "bg-emerald-50 text-emerald-700"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                )}
              >
                <Icon className="h-5 w-5 shrink-0" aria-hidden />
                {label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-slate-100 p-3">
          <button
            type="button"
            onClick={() => {
              if (typeof window !== "undefined") {
                localStorage.removeItem("token");
                window.location.href = "/";
              }
            }}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900"
          >
            <LogOut className="h-5 w-5 shrink-0" aria-hidden />
            Выход
          </button>
        </div>
      </aside>
      <main className="flex-1 pl-64">
        <div className="min-h-screen">{children}</div>
      </main>
    </div>
  );
}
