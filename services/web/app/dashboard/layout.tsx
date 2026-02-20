/**
 * @file: layout.tsx
 * @description: Layout дашборда — проверка токена, редирект на /login при отсутствии.
 * @dependencies: next
 * @created: 2025-02-20
 */
"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { DashboardShell } from "@/components/layout/DashboardShell";

const TOKEN_KEY = "token";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);
  const [hasToken, setHasToken] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      window.location.href = `/login?from=${encodeURIComponent(pathname || "/dashboard")}`;
      return;
    }
    setHasToken(true);
  }, [mounted, pathname]);

  if (!mounted || !hasToken) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <p className="text-slate-500">Загрузка...</p>
      </div>
    );
  }

  return <DashboardShell>{children}</DashboardShell>;
}
