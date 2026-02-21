/**
 * @file: page.tsx
 * @description: Настройки — API-ключи (список, создание, отзыв).
 * @dependencies: next, @tanstack/react-query
 * @created: 2025-02-20
 */
"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Settings, Key, Plus, Trash2 } from "lucide-react";
import { Card, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

type ApiKeyItem = {
  id: string;
  name: string | null;
  created_at: string;
  key_preview: string;
};

function getToken(): string {
  return typeof window === "undefined" ? "" : localStorage.getItem("token") || "";
}

async function fetchApiKeys(token: string): Promise<ApiKeyItem[]> {
  const r = await fetch("/api/proxy/api/api-keys", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!r.ok) throw new Error("Не удалось загрузить ключи");
  return r.json();
}

async function createApiKey(
  token: string,
  name?: string
): Promise<{ id: string; name: string | null; created_at: string; key: string }> {
  const r = await fetch("/api/proxy/api/api-keys", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ name: name || null }),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || "Ошибка создания ключа");
  }
  return r.json();
}

async function revokeApiKey(token: string, keyId: string): Promise<void> {
  const r = await fetch(`/api/proxy/api/api-keys/${keyId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!r.ok) throw new Error("Не удалось отозвать ключ");
}

function formatDate(s: string) {
  try {
    return new Date(s).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
  } catch {
    return s;
  }
}

export default function SettingsPage() {
  const token = getToken();
  const queryClient = useQueryClient();
  const [createName, setCreateName] = useState("");
  const [newKeyShown, setNewKeyShown] = useState<string | null>(null);

  const {
    data: keys,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["api-keys", token],
    queryFn: () => fetchApiKeys(token),
    enabled: !!token,
  });

  const createMutation = useMutation({
    mutationFn: () => createApiKey(token, createName.trim() || undefined),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["api-keys", token] });
      setNewKeyShown(data.key);
      setCreateName("");
    },
  });

  const revokeMutation = useMutation({
    mutationFn: (keyId: string) => revokeApiKey(token, keyId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["api-keys", token] }),
  });

  const copyKey = () => {
    if (newKeyShown && typeof navigator?.clipboard !== "undefined") {
      navigator.clipboard.writeText(newKeyShown);
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="font-display text-2xl font-bold text-slate-900">Настройки</h1>
        <p className="mt-1 text-slate-500">API-ключи для программного доступа.</p>
      </div>

      <Card>
        <CardTitle className="flex items-center gap-2">
          <Key className="h-5 w-5 text-emerald-600" />
          API-ключи
        </CardTitle>
        <CardDescription>
          Создавайте ключи для интеграций. Ключ показывается один раз при создании — сохраните его.
        </CardDescription>

        <div className="mt-4 flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">
              Имя (необязательно)
            </label>
            <input
              type="text"
              value={createName}
              onChange={(e) => setCreateName(e.target.value)}
              placeholder="Мой интеграция"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm w-48"
            />
          </div>
          <Button
            type="button"
            variant="primary"
            size="md"
            className="gap-1"
            onClick={() => createMutation.mutate()}
            disabled={createMutation.isPending}
          >
            <Plus className="h-4 w-4" />
            {createMutation.isPending ? "Создание…" : "Создать ключ"}
          </Button>
          {createMutation.isError && (
            <p className="text-sm text-red-600">{createMutation.error.message}</p>
          )}
        </div>

        {newKeyShown && (
          <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50/80 p-4">
            <p className="text-sm font-medium text-amber-800">
              Ключ создан. Скопируйте его — больше он не отобразится.
            </p>
            <code className="mt-2 block break-all rounded bg-white px-2 py-2 text-sm text-slate-700">
              {newKeyShown}
            </code>
            <div className="mt-3 flex gap-2">
              <Button type="button" variant="secondary" size="sm" onClick={copyKey}>
                Копировать
              </Button>
              <Button type="button" variant="ghost" size="sm" onClick={() => setNewKeyShown(null)}>
                Закрыть
              </Button>
            </div>
          </div>
        )}

        {isLoading && <p className="mt-4 text-sm text-slate-500">Загрузка...</p>}
        {error && <p className="mt-4 text-sm text-red-600">Ошибка загрузки ключей</p>}
        {keys && keys.length === 0 && !createMutation.isPending && (
          <p className="mt-4 text-sm text-slate-500">Нет API-ключей. Создайте первый ключ выше.</p>
        )}
        {keys && keys.length > 0 && (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-slate-500">
                  <th className="pb-2 pr-4 font-medium">Имя</th>
                  <th className="pb-2 pr-4 font-medium">Ключ</th>
                  <th className="pb-2 pr-4 font-medium">Создан</th>
                  <th className="pb-2 font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {keys.map((k) => (
                  <tr key={k.id} className="border-b border-slate-100">
                    <td className="py-3 pr-4 text-slate-700">{k.name || "—"}</td>
                    <td className="py-3 pr-4 font-mono text-slate-500">{k.key_preview}</td>
                    <td className="py-3 pr-4 text-slate-500">{formatDate(k.created_at)}</td>
                    <td className="py-3">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="text-red-600 hover:bg-red-50"
                        onClick={() => revokeMutation.mutate(k.id)}
                        disabled={revokeMutation.isPending}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
