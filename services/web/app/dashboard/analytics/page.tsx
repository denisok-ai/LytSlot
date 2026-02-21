/**
 * @file: page.tsx
 * @description: Аналитика — сводка и графики просмотров (Recharts), данные из API.
 * @dependencies: next, @tanstack/react-query, recharts
 * @created: 2025-02-20
 */
"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, Radio, ShoppingBag, Eye, DollarSign } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card, CardTitle, CardDescription } from "@/components/ui/Card";

type Summary = {
  channels_count: number;
  orders_count: number;
  views_total: number;
  revenue_total: number;
};

type ViewDay = { date: string; views: number };

type Channel = { id: string; username: string };

function getToken(): string {
  return typeof window === "undefined" ? "" : localStorage.getItem("token") || "";
}

async function fetchSummary(token: string): Promise<Summary> {
  const r = await fetch("/api/proxy/api/analytics/summary", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!r.ok) throw new Error("Не удалось загрузить сводку");
  return r.json();
}

async function fetchViews(
  token: string,
  dateFrom?: string,
  dateTo?: string,
  channelId?: string
): Promise<ViewDay[]> {
  const url = new URL("/api/proxy/api/analytics/views", window.location.origin);
  if (dateFrom) url.searchParams.set("date_from", `${dateFrom}T00:00:00`);
  if (dateTo) url.searchParams.set("date_to", `${dateTo}T23:59:59`);
  if (channelId) url.searchParams.set("channel_id", channelId);
  const r = await fetch(url.toString(), { headers: { Authorization: `Bearer ${token}` } });
  if (!r.ok) throw new Error("Не удалось загрузить просмотры");
  return r.json();
}

async function fetchChannels(token: string): Promise<Channel[]> {
  const r = await fetch("/api/proxy/api/channels", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!r.ok) throw new Error("Не удалось загрузить каналы");
  return r.json();
}

function lastDays(days: number): { from: string; to: string } {
  const to = new Date();
  const from = new Date(to);
  from.setDate(from.getDate() - days);
  return {
    from: from.toISOString().slice(0, 10),
    to: to.toISOString().slice(0, 10),
  };
}

export default function AnalyticsPage() {
  const token = getToken();
  const [periodDays, setPeriodDays] = useState<number>(30);
  const range = lastDays(periodDays);
  const [channelId, setChannelId] = useState<string>("");

  const {
    data: summary,
    isLoading: summaryLoading,
    error: summaryError,
  } = useQuery({
    queryKey: ["analytics-summary", token],
    queryFn: () => fetchSummary(token),
    enabled: !!token,
  });

  const { data: channels } = useQuery({
    queryKey: ["channels", token],
    queryFn: () => fetchChannels(token),
    enabled: !!token,
  });

  const {
    data: viewsData,
    isLoading: viewsLoading,
    error: viewsError,
  } = useQuery({
    queryKey: ["analytics-views", token, range.from, range.to, channelId],
    queryFn: () => fetchViews(token, range.from, range.to, channelId || undefined),
    enabled: !!token,
  });

  return (
    <div>
      <div className="mb-8">
        <h1 className="font-display text-2xl font-bold text-slate-900">Аналитика</h1>
        <p className="mt-1 text-slate-500">Просмотры, заказы и выручка по каналам и периодам.</p>
      </div>

      {summaryLoading && <p className="text-sm text-slate-500">Загрузка сводки...</p>}
      {summaryError && <p className="text-sm text-red-600">Ошибка загрузки сводки</p>}

      {summary && (
        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Каналы", value: summary.channels_count, icon: Radio },
            { label: "Заказов", value: summary.orders_count, icon: ShoppingBag },
            { label: "Просмотров", value: summary.views_total, icon: Eye },
            { label: "Выручка", value: `${summary.revenue_total} ₽`, icon: DollarSign },
          ].map(({ label, value, icon: Icon }) => (
            <Card key={label} className="border-slate-100">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-emerald-50 p-2">
                  <Icon className="h-5 w-5 text-emerald-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-500">{label}</p>
                  <p className="text-xl font-semibold text-slate-900">{value}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Card>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-emerald-600" />
          Просмотры по дням
        </CardTitle>
        <CardDescription>Агрегат по таблице views (TimescaleDB)</CardDescription>

        <div className="mt-4 flex flex-wrap gap-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Период</label>
            <select
              value={periodDays}
              onChange={(e) => setPeriodDays(Number(e.target.value))}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              <option value={7}>Последние 7 дней</option>
              <option value={30}>Последние 30 дней</option>
              <option value={90}>Последние 90 дней</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Канал</label>
            <select
              value={channelId}
              onChange={(e) => setChannelId(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              <option value="">Все каналы</option>
              {(channels || []).map((ch) => (
                <option key={ch.id} value={ch.id}>
                  @{ch.username}
                </option>
              ))}
            </select>
          </div>
        </div>

        {viewsLoading && <p className="mt-4 text-sm text-slate-500">Загрузка графика...</p>}
        {viewsError && <p className="mt-4 text-sm text-red-600">Ошибка загрузки просмотров</p>}

        {viewsData && viewsData.length > 0 && (
          <div className="mt-6 h-[320px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={viewsData} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#64748b" />
                <YAxis tick={{ fontSize: 12 }} stroke="#64748b" />
                <Tooltip
                  contentStyle={{ borderRadius: 8, border: "1px solid #e2e8f0" }}
                  labelStyle={{ color: "#475569" }}
                  formatter={(value: number) => [value, "Просмотров"]}
                />
                <Line
                  type="monotone"
                  dataKey="views"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={{ fill: "#10b981", r: 3 }}
                  name="Просмотры"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {viewsData && viewsData.length === 0 && !viewsLoading && (
          <div className="mt-8 flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 py-12">
            <BarChart3 className="h-12 w-12 text-slate-300" aria-hidden />
            <p className="mt-2 text-sm text-slate-500">Нет данных за выбранный период</p>
            <p className="mt-1 text-xs text-slate-400">
              Добавляйте события в таблицу views для отображения
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}
