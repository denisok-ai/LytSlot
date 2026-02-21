/**
 * @file: DashboardShell.tsx
 * @description: Оболочка дашборда — сайдбар + контент; на мобильных — верхняя полоса и выдвижное меню.
 * @dependencies: next/link, lucide-react
 */
"use client";

import { useState } from "react";
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
  Menu,
  X,
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

function SidebarContent({ onLinkClick }: { onLinkClick?: () => void }) {
  const pathname = usePathname();
  return (
    <>
      <div className="flex h-16 items-center justify-between gap-2 border-b border-slate-100 px-4 md:px-6">
        <Link
          href="/"
          className="flex items-center gap-2 font-display text-xl font-bold text-slate-900"
          onClick={onLinkClick}
        >
          LytSlot <span className="text-emerald-600">Pro</span>
        </Link>
        {onLinkClick && (
          <button
            type="button"
            onClick={onLinkClick}
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 md:hidden"
            aria-label="Закрыть меню"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>
      <nav className="flex-1 space-y-0.5 p-3" aria-label="Основная навигация">
        {nav.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              onClick={onLinkClick}
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
    </>
  );
}

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Мобильная верхняя полоса */}
      <header className="fixed top-0 left-0 right-0 z-30 flex h-14 items-center justify-between border-b border-slate-200/80 bg-white px-4 shadow-sm md:hidden">
        <button
          type="button"
          onClick={() => setMobileMenuOpen(true)}
          className="rounded-lg p-2 text-slate-600 hover:bg-slate-100"
          aria-label="Открыть меню"
        >
          <Menu className="h-6 w-6" />
        </button>
        <Link
          href="/"
          className="font-display text-lg font-bold text-slate-900"
          onClick={() => setMobileMenuOpen(false)}
        >
          LytSlot <span className="text-emerald-600">Pro</span>
        </Link>
        <div className="w-10" aria-hidden />
      </header>

      {/* Выдвижное меню (мобильные) */}
      {mobileMenuOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-slate-900/50 md:hidden"
            aria-hidden
            onClick={() => setMobileMenuOpen(false)}
          />
          <aside
            className="fixed inset-y-0 left-0 z-50 w-72 max-w-[85vw] flex flex-col border-r border-slate-200/80 bg-white shadow-xl md:hidden"
            role="dialog"
            aria-label="Меню навигации"
          >
            <SidebarContent onLinkClick={() => setMobileMenuOpen(false)} />
          </aside>
        </>
      )}

      {/* Десктоп: постоянный сайдбар */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-slate-200/80 bg-white shadow-sm md:flex">
        <SidebarContent />
      </aside>

      {/* Контент: отступ сверху на мобильных (под верхнюю полосу), слева — только на md+ */}
      <main className="min-w-0 flex-1 pt-14 md:pl-64 md:pt-0">
        <div className="min-h-screen p-4 sm:p-6 md:p-8">{children}</div>
      </main>
    </div>
  );
}
