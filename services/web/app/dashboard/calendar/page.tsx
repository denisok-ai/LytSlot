/**
 * @file: page.tsx
 * @description: Календарь и слоты — список слотов по каналу, создание слота.
 * @dependencies: next, @tanstack/react-query
 * @created: 2025-02-20
 */
"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Calendar, Plus, ShoppingCart } from "lucide-react";
import { Card, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { SlotsCalendar } from "@/components/calendar/SlotsCalendar";

type Channel = { id: string; username: string };
type Slot = { id: string; channel_id: string; datetime: string; status: string };

function getToken(): string {
  return typeof window === "undefined" ? "" : localStorage.getItem("token") || "";
}

async function fetchChannels(token: string): Promise<Channel[]> {
  const r = await fetch("/api/proxy/api/channels", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!r.ok) throw new Error("Не удалось загрузить каналы");
  return r.json();
}

async function fetchSlots(
  token: string,
  channelId: string,
  dateFrom?: string,
  dateTo?: string
): Promise<Slot[]> {
  const url = new URL("/api/proxy/api/slots", window.location.origin);
  url.searchParams.set("channel_id", channelId);
  if (dateFrom) url.searchParams.set("date_from", dateFrom);
  if (dateTo) url.searchParams.set("date_to", dateTo);
  const r = await fetch(url.toString(), { headers: { Authorization: `Bearer ${token}` } });
  if (!r.ok) throw new Error("Не удалось загрузить слоты");
  return r.json();
}

async function createSlot(token: string, body: { channel_id: string; datetime: string }) {
  const r = await fetch("/api/proxy/api/slots", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || "Ошибка создания слота");
  }
  return r.json();
}

async function createOrder(
  token: string,
  body: { channel_id: string; slot_id: string; content: Record<string, unknown> }
) {
  const r = await fetch("/api/proxy/api/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || "Ошибка создания заказа");
  }
  return r.json();
}

function toLocalISO(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const h = String(d.getHours()).padStart(2, "0");
  const min = String(d.getMinutes()).padStart(2, "0");
  return `${y}-${m}-${day}T${h}:${min}:00`;
}

function currentMonthRange(): { from: string; to: string } {
  const now = new Date();
  const first = new Date(now.getFullYear(), now.getMonth(), 1);
  const last = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  return { from: first.toISOString().slice(0, 10), to: last.toISOString().slice(0, 10) };
}

export default function CalendarPage() {
  const token = getToken();
  const queryClient = useQueryClient();
  const [channelId, setChannelId] = useState("");
  const [slotDate, setSlotDate] = useState(() => {
    const d = new Date();
    d.setMinutes(0, 0, 0);
    return toLocalISO(d).slice(0, 16);
  });
  const defaultRange = currentMonthRange();
  const [dateFrom, setDateFrom] = useState(defaultRange.from);
  const [dateTo, setDateTo] = useState(defaultRange.to);
  const [orderSlot, setOrderSlot] = useState<Slot | null>(null);
  const [orderText, setOrderText] = useState("");
  const [orderLink, setOrderLink] = useState("");

  const { data: channels } = useQuery({
    queryKey: ["channels", token],
    queryFn: () => fetchChannels(token),
    enabled: !!token,
  });

  const { data: slots, isLoading: slotsLoading } = useQuery({
    queryKey: ["slots", token, channelId, dateFrom, dateTo],
    queryFn: () => fetchSlots(token, channelId, dateFrom || undefined, dateTo || undefined),
    enabled: !!token && !!channelId,
  });

  const createMutation = useMutation({
    mutationFn: (body: { channel_id: string; datetime: string }) => createSlot(token, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["slots", token, channelId, dateFrom, dateTo] });
      setSlotDate(toLocalISO(new Date()).slice(0, 16));
    },
  });

  const orderMutation = useMutation({
    mutationFn: (body: { channel_id: string; slot_id: string; content: Record<string, unknown> }) =>
      createOrder(token, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["slots", token, channelId, dateFrom, dateTo] });
      queryClient.invalidateQueries({ queryKey: ["orders", token] });
      setOrderSlot(null);
      setOrderText("");
      setOrderLink("");
    },
  });

  const handleCreateSlot = (e: React.FormEvent) => {
    e.preventDefault();
    if (!channelId) return;
    const dt = slotDate.replace("T", " ") + ":00";
    createMutation.mutate({ channel_id: channelId, datetime: dt });
  };

  const formatSlotDate = (s: string) => {
    try {
      return new Date(s).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
    } catch {
      return s;
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="font-display text-2xl font-bold text-slate-900">Календарь</h1>
        <p className="mt-1 text-slate-500">Слоты по каналам, создание слотов.</p>
      </div>

      <div className="space-y-6">
        <Card>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-emerald-600" />
            Слоты по каналу
          </CardTitle>
          <CardDescription>Выберите канал и при необходимости период</CardDescription>

          <div className="mt-4 flex flex-wrap gap-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Канал</label>
              <select
                value={channelId}
                onChange={(e) => setChannelId(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <option value="">— Выберите канал —</option>
                {(channels || []).map((ch) => (
                  <option key={ch.id} value={ch.id}>
                    @{ch.username}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">С (дата)</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">По (дата)</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          </div>

          {channelId && (
            <>
              <form
                onSubmit={handleCreateSlot}
                className="mt-4 flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-slate-50/50 p-3"
              >
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600">
                    Дата и время слота
                  </label>
                  <input
                    type="datetime-local"
                    value={slotDate}
                    onChange={(e) => setSlotDate(e.target.value)}
                    className="rounded border border-slate-300 px-2 py-1.5 text-sm"
                  />
                </div>
                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  className="gap-1"
                  disabled={createMutation.isPending}
                >
                  <Plus className="h-4 w-4" />
                  {createMutation.isPending ? "Создание…" : "Добавить слот"}
                </Button>
                {createMutation.isError && (
                  <p className="text-sm text-red-600">{createMutation.error.message}</p>
                )}
              </form>

              {slotsLoading && <p className="mt-3 text-sm text-slate-500">Загрузка слотов...</p>}
              {slots && slots.length === 0 && !createMutation.isPending && (
                <p className="mt-3 text-sm text-slate-500">Нет слотов за выбранный период.</p>
              )}
              {slots && slots.length > 0 && (
                <ul className="mt-3 space-y-1.5">
                  {slots.map((s) => (
                    <li
                      key={s.id}
                      className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-100 bg-white px-3 py-2 text-sm"
                    >
                      <span className="text-slate-700">{formatSlotDate(s.datetime)}</span>
                      <div className="flex items-center gap-2">
                        <span
                          className={`rounded px-2 py-0.5 text-xs ${s.status === "free" ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}
                        >
                          {s.status === "free" ? "Свободен" : s.status}
                        </span>
                        {s.status === "free" && (
                          <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            className="gap-1"
                            onClick={() => setOrderSlot(s)}
                          >
                            <ShoppingCart className="h-3.5 w-3.5" />
                            Заказать
                          </Button>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
              {orderSlot && (
                <form
                  className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50/50 p-4"
                  onSubmit={(e) => {
                    e.preventDefault();
                    orderMutation.mutate({
                      channel_id: orderSlot.channel_id,
                      slot_id: orderSlot.id,
                      content: {
                        text: orderText.trim() || "Реклама",
                        link: orderLink.trim() || undefined,
                      },
                    });
                  }}
                >
                  <p className="text-sm font-medium text-slate-700">
                    Заказ на слот {formatSlotDate(orderSlot.datetime)}
                  </p>
                  <div className="mt-3 grid gap-2 sm:grid-cols-2">
                    <div>
                      <label className="mb-1 block text-xs font-medium text-slate-600">
                        Текст рекламы
                      </label>
                      <input
                        type="text"
                        value={orderText}
                        onChange={(e) => setOrderText(e.target.value)}
                        placeholder="Текст поста"
                        className="w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs font-medium text-slate-600">
                        Ссылка (необязательно)
                      </label>
                      <input
                        type="url"
                        value={orderLink}
                        onChange={(e) => setOrderLink(e.target.value)}
                        placeholder="https://..."
                        className="w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
                      />
                    </div>
                  </div>
                  <div className="mt-3 flex gap-2">
                    <Button
                      type="submit"
                      variant="primary"
                      size="sm"
                      disabled={orderMutation.isPending}
                    >
                      {orderMutation.isPending ? "Создание…" : "Создать заказ"}
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setOrderSlot(null);
                        setOrderText("");
                        setOrderLink("");
                      }}
                    >
                      Отмена
                    </Button>
                  </div>
                  {orderMutation.isError && (
                    <p className="mt-2 text-xs text-red-600">{orderMutation.error.message}</p>
                  )}
                </form>
              )}
            </>
          )}
        </Card>

        <Card>
          <CardTitle>Визуальный календарь</CardTitle>
          <CardDescription>
            Неделя/день/месяц. Клик по свободному слоту (зелёный) — создать заказ.
          </CardDescription>
          {channelId ? (
            <div className="mt-4">
              <SlotsCalendar
                slots={slots || []}
                onSlotClick={(s) => setOrderSlot(s)}
                height={420}
              />
            </div>
          ) : (
            <div className="mt-6 flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 py-12">
              <Calendar className="h-12 w-12 text-slate-300" aria-hidden />
              <p className="mt-2 text-sm text-slate-500">
                Выберите канал выше, чтобы увидеть слоты
              </p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
