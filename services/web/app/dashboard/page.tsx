/**
 * @file: page.tsx
 * @description: Dashboard — обзор каналов, плейсхолдеры аналитики и заказов.
 * @dependencies: next, @tanstack/react-query
 * @created: 2025-02-19
 */
"use client";

import { useQuery } from "@tanstack/react-query";
import { Radio, TrendingUp, ShoppingBag, Calendar, Eye } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { Card, CardTitle, CardDescription } from "@/components/ui/Card";
import { ButtonLink } from "@/components/ui/Button";

async function fetchChannels(token: string) {
  const r = await fetch("/api/proxy/api/channels", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!r.ok) throw new Error("Failed to fetch channels");
  return r.json();
}

async function fetchSummary(token: string) {
  const r = await fetch("/api/proxy/api/analytics/summary", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!r.ok) throw new Error("Failed to fetch summary");
  return r.json();
}

export default function DashboardPage() {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const {
    data: channels,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["channels", token],
    queryFn: () => fetchChannels(token || ""),
    enabled: !!token,
  });

  const { data: summary } = useQuery({
    queryKey: ["analytics-summary", token],
    queryFn: () => fetchSummary(token || ""),
    enabled: !!token,
  });

  return (
    <DashboardShell>
      <div className="border-b border-slate-200/80 bg-white">
        <div className="px-4 py-4 sm:px-6 sm:py-5 md:px-8 md:py-6">
          <h1 className="font-display text-2xl font-bold text-slate-900">Обзор</h1>
          <p className="mt-1 text-slate-500">Каналы, слоты и заказы в одном месте.</p>
        </div>
      </div>

      <div>
        {!token && (
          <Card className="border-amber-200 bg-amber-50/50">
            <CardTitle>Требуется вход</CardTitle>
            <CardDescription>
              Войдите через Telegram, чтобы видеть каналы и управлять слотом.
            </CardDescription>
            <ButtonLink href="/login" variant="primary" size="md" className="mt-4">
              Войти через Telegram
            </ButtonLink>
          </Card>
        )}

        {token && (
          <>
            <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                {
                  label: "Каналы",
                  value: channels?.length ?? summary?.channels_count ?? "—",
                  icon: Radio,
                },
                { label: "Заказы", value: summary?.orders_count ?? "—", icon: ShoppingBag },
                { label: "Просмотров", value: summary?.views_total ?? "—", icon: Eye },
                { label: "Выручка (₽)", value: summary?.revenue_total ?? "—", icon: TrendingUp },
              ].map(({ label, value, icon: Icon }) => (
                <Card key={label} hover className="flex items-center gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-600">
                    <Icon className="h-6 w-6" aria-hidden />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-500">{label}</p>
                    <p className="text-2xl font-semibold text-slate-900">{value}</p>
                  </div>
                </Card>
              ))}
            </div>

            <div className="grid gap-8 lg:grid-cols-2">
              <Card hover>
                <CardTitle className="flex items-center gap-2">
                  <Radio className="h-5 w-5 text-emerald-600" />
                  Мои каналы
                </CardTitle>
                <CardDescription>Добавленные Telegram-каналы и настройки слотов.</CardDescription>
                {isLoading && <p className="mt-4 text-sm text-slate-500">Загрузка каналов...</p>}
                {error && (
                  <p className="mt-4 text-sm text-red-600">
                    Ошибка загрузки. Проверьте токен и API.
                  </p>
                )}
                {channels && channels.length === 0 && (
                  <p className="mt-4 text-sm text-slate-500">
                    Пока нет каналов. Добавьте первый в разделе «Каналы».
                  </p>
                )}
                {channels && channels.length > 0 && (
                  <ul className="mt-4 space-y-2" role="list">
                    {channels.map((c: { id: string; username: string }) => (
                      <li
                        key={c.id}
                        className="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50/50 px-4 py-3 text-sm"
                      >
                        <span className="font-medium text-slate-900">@{c.username}</span>
                        <span className="text-slate-500">ID: {c.id.slice(0, 8)}…</span>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>

              <Card className="border-dashed border-slate-200 bg-slate-50/30">
                <CardTitle>Ближайшие слоты и заказы</CardTitle>
                <CardDescription>
                  Календарь и список заказов будут на этой странице.
                </CardDescription>
                <div className="mt-6 flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-200 py-12 text-center">
                  <Calendar className="h-12 w-12 text-slate-300" aria-hidden />
                  <p className="mt-2 text-sm font-medium text-slate-500">Календарь слотов</p>
                  <p className="mt-1 text-xs text-slate-400">FullCalendar Pro — в разработке</p>
                </div>
              </Card>
            </div>
          </>
        )}
      </div>
    </DashboardShell>
  );
}
