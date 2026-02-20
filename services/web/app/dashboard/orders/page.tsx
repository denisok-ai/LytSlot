/**
 * @file: page.tsx
 * @description: Заказы — список заказов из API, превью контента, смена статуса.
 * @dependencies: next, @tanstack/react-query
 * @created: 2025-02-20
 */
"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ShoppingBag } from "lucide-react";
import { Card, CardTitle, CardDescription } from "@/components/ui/Card";

const ORDER_STATUSES = ["draft", "paid", "marked", "scheduled", "published", "cancelled"] as const;

type Order = {
  id: string;
  advertiser_id: number;
  channel_id: string;
  slot_id: string;
  content: Record<string, unknown>;
  erid: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

function getToken(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("token") || "";
}

async function fetchOrders(token: string): Promise<Order[]> {
  const r = await fetch("/api/proxy/api/orders", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!r.ok) throw new Error("Не удалось загрузить заказы");
  return r.json();
}

async function updateOrderStatus(token: string, orderId: string, status: string): Promise<Order> {
  const r = await fetch(`/api/proxy/api/orders/${orderId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ status }),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || "Не удалось обновить статус");
  }
  return r.json();
}

function formatDate(s: string) {
  try {
    return new Date(s).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
  } catch {
    return s;
  }
}

function contentPreview(content: Record<string, unknown>, maxLen = 60): string {
  if (!content || typeof content !== "object") return "—";
  const text = content.text;
  if (typeof text === "string") {
    return text.length <= maxLen ? text : text.slice(0, maxLen) + "…";
  }
  const link = content.link;
  if (typeof link === "string") return link;
  return "—";
}

export default function OrdersPage() {
  const token = getToken();
  const queryClient = useQueryClient();
  const {
    data: orders,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["orders", token],
    queryFn: () => fetchOrders(token),
    enabled: !!token,
  });

  const statusMutation = useMutation({
    mutationFn: ({ orderId, status }: { orderId: string; status: string }) =>
      updateOrderStatus(token, orderId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders", token] });
    },
  });

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="font-display text-2xl font-bold text-slate-900">Заказы</h1>
        <p className="mt-1 text-slate-500">Список заказов на рекламу по вашим каналам.</p>
      </div>

      <Card>
        <CardTitle className="flex items-center gap-2">
          <ShoppingBag className="h-5 w-5 text-emerald-600" />
          Список заказов
        </CardTitle>
        <CardDescription>Все заказы по вашим каналам. Можно менять статус.</CardDescription>

        {isLoading && <p className="mt-4 text-sm text-slate-500">Загрузка...</p>}
        {error && <p className="mt-4 text-sm text-red-600">Ошибка загрузки</p>}
        {orders && orders.length === 0 && (
          <p className="mt-4 text-sm text-slate-500">Пока нет заказов.</p>
        )}
        {orders && orders.length > 0 && (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-slate-500">
                  <th className="pb-2 pr-4 font-medium">ID</th>
                  <th className="pb-2 pr-4 font-medium">Контент</th>
                  <th className="pb-2 pr-4 font-medium">Статус</th>
                  <th className="pb-2 pr-4 font-medium">Создан</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((o) => (
                  <tr key={o.id} className="border-b border-slate-100">
                    <td className="py-3 pr-4 font-mono text-slate-600 align-top">
                      {o.id.slice(0, 8)}…
                    </td>
                    <td className="max-w-[200px] py-3 pr-4 align-top">
                      <span
                        className="line-clamp-2 text-slate-600"
                        title={contentPreview(o.content, 200)}
                      >
                        {contentPreview(o.content)}
                      </span>
                    </td>
                    <td className="py-3 pr-4 align-top">
                      <select
                        value={o.status}
                        onChange={(e) =>
                          statusMutation.mutate({ orderId: o.id, status: e.target.value })
                        }
                        disabled={statusMutation.isPending}
                        className="rounded border border-slate-300 bg-white px-2 py-1 text-slate-700 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                      >
                        {ORDER_STATUSES.map((s) => (
                          <option key={s} value={s}>
                            {s}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="py-3 text-slate-500 align-top">{formatDate(o.created_at)}</td>
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
