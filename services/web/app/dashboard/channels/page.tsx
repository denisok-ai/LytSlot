/**
 * @file: page.tsx
 * @description: Каналы — список, добавление и редактирование (API channels).
 * @dependencies: next, @tanstack/react-query
 * @created: 2025-02-20
 */
"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Radio, Plus, Pencil, X } from "lucide-react";
import { Card, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button, ButtonLink } from "@/components/ui/Button";

type Channel = {
  id: string;
  tenant_id: string;
  username: string;
  slot_duration: number;
  price_per_slot: number;
  is_active: boolean;
};

function getToken(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("token") || "";
}

async function fetchChannels(token: string): Promise<Channel[]> {
  const r = await fetch("/api/proxy/api/channels", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    const msg =
      typeof err.detail === "string" ? err.detail : err.detail?.[0]?.msg || `Ошибка ${r.status}`;
    throw new Error(msg);
  }
  return r.json();
}

async function createChannel(
  token: string,
  body: { username: string; slot_duration: number; price_per_slot: number; is_active: boolean }
) {
  const r = await fetch("/api/proxy/api/channels", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || "Ошибка создания канала");
  }
  return r.json();
}

async function updateChannel(
  token: string,
  channelId: string,
  body: { username?: string; slot_duration?: number; price_per_slot?: number; is_active?: boolean }
) {
  const r = await fetch(`/api/proxy/api/channels/${channelId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || "Ошибка обновления канала");
  }
  return r.json();
}

const SLOT_OPTIONS = [
  { value: 900, label: "15 мин" },
  { value: 1800, label: "30 мин" },
  { value: 3600, label: "1 ч" },
];

export default function ChannelsPage() {
  const token = getToken();
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [username, setUsername] = useState("");
  const [slotDuration, setSlotDuration] = useState(3600);
  const [pricePerSlot, setPricePerSlot] = useState(1000);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editUsername, setEditUsername] = useState("");
  const [editSlotDuration, setEditSlotDuration] = useState(3600);
  const [editPricePerSlot, setEditPricePerSlot] = useState(1000);
  const [editActive, setEditActive] = useState(true);

  const {
    data: channels,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["channels", token],
    queryFn: () => fetchChannels(token),
    enabled: !!token,
  });

  const createMutation = useMutation({
    mutationFn: (body: {
      username: string;
      slot_duration: number;
      price_per_slot: number;
      is_active: boolean;
    }) => createChannel(token, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["channels", token] });
      setUsername("");
      setSlotDuration(3600);
      setPricePerSlot(1000);
      setShowForm(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: string;
      body: {
        username?: string;
        slot_duration?: number;
        price_per_slot?: number;
        is_active?: boolean;
      };
    }) => updateChannel(token, id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["channels", token] });
      setEditingId(null);
    },
  });

  const startEdit = (c: Channel) => {
    setEditingId(c.id);
    setEditUsername(c.username);
    setEditSlotDuration(c.slot_duration);
    setEditPricePerSlot(c.price_per_slot);
    setEditActive(c.is_active);
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingId) return;
    updateMutation.mutate({
      id: editingId,
      body: {
        username: editUsername.trim() || undefined,
        slot_duration: editSlotDuration,
        price_per_slot: editPricePerSlot,
        is_active: editActive,
      },
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      username: username.trim() || "channel",
      slot_duration: slotDuration,
      price_per_slot: pricePerSlot,
      is_active: true,
    });
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="font-display text-2xl font-bold text-slate-900">Каналы</h1>
        <p className="mt-1 text-slate-500">Добавляйте каналы и настраивайте слоты и цены.</p>
      </div>

      <div className="space-y-6">
        <Card>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Radio className="h-5 w-5 text-emerald-600" />
                Мои каналы
              </CardTitle>
              <CardDescription>Список подключённых Telegram-каналов</CardDescription>
            </div>
            <Button
              type="button"
              variant="primary"
              size="md"
              className="gap-2"
              onClick={() => setShowForm((v) => !v)}
            >
              <Plus className="h-4 w-4" />
              Добавить канал
            </Button>
          </div>

          {showForm && (
            <form
              onSubmit={handleSubmit}
              className="mt-6 rounded-lg border border-slate-200 bg-slate-50/50 p-4"
            >
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-700">
                    Username канала
                  </label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="@channel"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-700">
                    Длительность слота
                  </label>
                  <select
                    value={slotDuration}
                    onChange={(e) => setSlotDuration(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  >
                    {SLOT_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-slate-700">
                    Цена за слот (₽)
                  </label>
                  <input
                    type="number"
                    min={0}
                    step={100}
                    value={pricePerSlot}
                    onChange={(e) => setPricePerSlot(Number(e.target.value) || 0)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  />
                </div>
                <div className="flex items-end gap-2">
                  <Button
                    type="submit"
                    variant="primary"
                    size="md"
                    disabled={createMutation.isPending}
                  >
                    {createMutation.isPending ? "Создание…" : "Создать"}
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    size="md"
                    onClick={() => setShowForm(false)}
                  >
                    Отмена
                  </Button>
                </div>
              </div>
              {createMutation.isError && (
                <p className="mt-2 text-sm text-red-600">{createMutation.error.message}</p>
              )}
            </form>
          )}

          {isLoading && <p className="mt-4 text-sm text-slate-500">Загрузка...</p>}
          {error && (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50/80 p-3" role="alert">
              <p className="text-sm font-medium text-red-800">
                {error instanceof Error ? error.message : "Ошибка загрузки"}
              </p>
              <p className="mt-1 text-xs text-red-600">
                Убедитесь, что API запущен (например,{" "}
                <code className="rounded bg-red-100 px-1">./scripts/run-api.sh</code> на порту 8000)
                и вы вошли в кабинет заново.
              </p>
            </div>
          )}
          {channels && channels.length === 0 && !showForm && (
            <p className="mt-4 text-sm text-slate-500">
              Пока нет каналов. Нажмите «Добавить канал».
            </p>
          )}
          {channels && channels.length > 0 && (
            <ul className="mt-4 space-y-2" role="list">
              {channels.map((c) => (
                <li key={c.id} className="rounded-lg border border-slate-100 bg-white">
                  <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
                    <div className="flex items-center gap-3">
                      <span className="font-medium text-slate-900">@{c.username}</span>
                      <span className="text-sm text-slate-500">
                        {SLOT_OPTIONS.find((o) => o.value === c.slot_duration)?.label ??
                          `${c.slot_duration / 60} мин`}
                      </span>
                      <span className="text-sm font-medium text-emerald-600">
                        {c.price_per_slot} ₽
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs ${c.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}
                      >
                        {c.is_active ? "Активен" : "Выкл"}
                      </span>
                      <button
                        type="button"
                        onClick={() => startEdit(c)}
                        className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
                        title="Изменить"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  {editingId === c.id && (
                    <form
                      onSubmit={handleEditSubmit}
                      className="border-t border-slate-100 bg-slate-50/50 px-4 py-3"
                    >
                      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                        <div>
                          <label className="mb-1 block text-xs font-medium text-slate-600">
                            Username
                          </label>
                          <input
                            type="text"
                            value={editUsername}
                            onChange={(e) => setEditUsername(e.target.value)}
                            className="w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
                          />
                        </div>
                        <div>
                          <label className="mb-1 block text-xs font-medium text-slate-600">
                            Длительность слота
                          </label>
                          <select
                            value={editSlotDuration}
                            onChange={(e) => setEditSlotDuration(Number(e.target.value))}
                            className="w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
                          >
                            {SLOT_OPTIONS.map((o) => (
                              <option key={o.value} value={o.value}>
                                {o.label}
                              </option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className="mb-1 block text-xs font-medium text-slate-600">
                            Цена (₽)
                          </label>
                          <input
                            type="number"
                            min={0}
                            step={100}
                            value={editPricePerSlot}
                            onChange={(e) => setEditPricePerSlot(Number(e.target.value) || 0)}
                            className="w-full rounded border border-slate-300 px-2 py-1.5 text-sm"
                          />
                        </div>
                        <div className="flex items-center gap-2">
                          <label className="flex items-center gap-1.5 text-sm text-slate-600">
                            <input
                              type="checkbox"
                              checked={editActive}
                              onChange={(e) => setEditActive(e.target.checked)}
                              className="rounded border-slate-300"
                            />
                            Активен
                          </label>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            type="submit"
                            variant="primary"
                            size="sm"
                            disabled={updateMutation.isPending}
                          >
                            {updateMutation.isPending ? "Сохранение…" : "Сохранить"}
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => setEditingId(null)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                      {updateMutation.isError && (
                        <p className="mt-2 text-xs text-red-600">{updateMutation.error.message}</p>
                      )}
                    </form>
                  )}
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
