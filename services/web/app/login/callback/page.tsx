/**
 * @file: page.tsx
 * @description: Callback после Telegram Login Widget — обмен данных на JWT, сохранение, редирект.
 * @dependencies: next
 * @created: 2025-02-20
 */
"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { ButtonLink } from "@/components/ui/Button";

function buildInitData(searchParams: URLSearchParams): string {
  const params: string[] = [];
  searchParams.forEach((value, key) => {
    if (key !== "hash") params.push(`${key}=${value}`);
  });
  const hash = searchParams.get("hash");
  if (hash) params.push(`hash=${hash}`);
  return params.sort().join("&");
}

function LoginCallbackContent() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const hash = searchParams.get("hash");
    if (!hash) {
      setStatus("error");
      setMessage("Нет данных от Telegram. Войдите через виджет на странице входа.");
      return;
    }
    const initData = buildInitData(searchParams);
    fetch("/api/auth/callback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ init_data: initData }),
    })
      .then(async (r) => {
        if (!r.ok) {
          const err = await r.json().catch(() => ({}));
          throw new Error(err.detail || r.statusText);
        }
        return r.json();
      })
      .then((data: { access_token: string }) => {
        if (data.access_token) {
          localStorage.setItem("token", data.access_token);
          window.location.href = "/dashboard";
          return;
        }
        throw new Error("Нет токена в ответе");
      })
      .catch((e) => {
        setStatus("error");
        setMessage(e instanceof Error ? e.message : "Ошибка входа");
      });
  }, [searchParams]);

  if (status === "loading") {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4">
        <div className="rounded-2xl border border-slate-200/80 bg-white px-8 py-6 shadow-card">
          <p className="text-slate-600">Вход в кабинет...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm rounded-2xl border border-slate-200/80 bg-white p-8 shadow-card">
        <h1 className="text-lg font-semibold text-slate-900">Ошибка входа</h1>
        <p className="mt-2 text-sm text-slate-500">{message}</p>
        <div className="mt-6 flex gap-3">
          <ButtonLink href="/login" variant="primary" className="flex-1 justify-center">
            Повторить
          </ButtonLink>
          <ButtonLink href="/" variant="secondary" className="flex-1 justify-center">
            На главную
          </ButtonLink>
        </div>
      </div>
    </div>
  );
}

export default function LoginCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4">
          <div className="rounded-2xl border border-slate-200/80 bg-white px-8 py-6 shadow-card">
            <p className="text-slate-600">Вход в кабинет...</p>
          </div>
        </div>
      }
    >
      <LoginCallbackContent />
    </Suspense>
  );
}
