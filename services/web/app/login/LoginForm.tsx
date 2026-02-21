"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Button, ButtonLink } from "@/components/ui/Button";

type Props = {
  botUsername: string;
  appUrl: string;
};

export function LoginForm({ botUsername, appUrl }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const addedRef = useRef(false);
  const [devTelegramId, setDevTelegramId] = useState("123456789");
  const [devLoading, setDevLoading] = useState(false);
  const [devError, setDevError] = useState("");
  const [showDevLogin, setShowDevLogin] = useState(false);
  useEffect(() => {
    if (typeof window === "undefined") return;
    const isLocalhost =
      window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
    const hasDevParam = new URLSearchParams(window.location.search).get("dev") === "1";
    if (isLocalhost || hasDevParam) setShowDevLogin(true);
  }, []);

  useEffect(() => {
    if (!botUsername || !containerRef.current || addedRef.current) return;
    addedRef.current = true;
    containerRef.current.innerHTML = "";
    const script = document.createElement("script");
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.setAttribute("data-telegram-login", botUsername);
    script.setAttribute("data-size", "large");
    script.setAttribute("data-auth-url", `${appUrl}/login/callback`);
    script.setAttribute("data-request-access", "write");
    script.async = true;
    containerRef.current.appendChild(script);
  }, [botUsername, appUrl]);

  return (
    <>
      {!botUsername && (
        <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          <p className="font-medium">Переменная не задана</p>
          <p className="mt-1">
            Файл должен быть именно{" "}
            <code className="rounded bg-red-100 px-1">services/web/.env.local</code> (рядом с{" "}
            <code className="rounded bg-red-100 px-1">package.json</code>).
          </p>
          <p className="mt-2">
            Одна строка в файле:{" "}
            <code className="block mt-1 rounded bg-red-100 p-1.5">
              NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=LytSlotBot
            </code>{" "}
            (для бота @LytSlotBot)
          </p>
          <p className="mt-2">
            После сохранения остановите <code className="rounded bg-red-100 px-1">npm run dev</code>{" "}
            (Ctrl+C) и запустите снова.
          </p>
        </div>
      )}
      <div
        ref={containerRef}
        className="mt-6 min-h-[44px] flex justify-center [&>iframe]:!block [&>script]:!block"
      />
      {botUsername && (
        <p className="mt-2 text-center text-xs text-slate-400">
          Бот: <span className="font-mono">@{botUsername}</span>
        </p>
      )}
      {botUsername && (
        <p className="mt-2 text-center text-xs text-slate-400">
          <a
            href={`https://t.me/${botUsername.replace(/^@/, "")}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-emerald-600 hover:underline"
          >
            Открыть бота в Telegram
          </a>
        </p>
      )}
      {botUsername && !showDevLogin && (
        <p className="mt-3 text-center text-sm text-slate-600">
          <Link href="/login?dev=1" className="text-emerald-600 hover:underline font-medium">
            Войти без Telegram (режим разработки)
          </Link>
        </p>
      )}
      {botUsername && (
        <p className="mt-2 text-center text-xs text-slate-500">
          Кнопка «Log in with Telegram» может не отображаться на localhost. В BotFather выполните{" "}
          <code className="rounded bg-slate-100 px-1">/setdomain</code> и укажите домен.
        </p>
      )}

      {showDevLogin && (
        <div className="mt-6 rounded-lg border border-amber-200 bg-amber-50/80 p-4">
          <p className="text-sm font-medium text-amber-800">Режим разработки (без домена)</p>
          <p className="mt-1 text-xs text-amber-700">
            В корневом <code className="rounded bg-amber-100 px-1">.env</code> добавьте{" "}
            <code className="rounded bg-amber-100 px-1">ENABLE_DEV_LOGIN=true</code> и перезапустите
            API.
          </p>
          <p className="mt-1 text-xs text-amber-700">
            Для тестовых данных (после{" "}
            <code className="rounded bg-amber-100 px-1">./scripts/seed-db.sh</code>) введите{" "}
            <strong>123456789</strong> и нажмите «Войти для разработки».
          </p>
          <form
            className="mt-3 flex flex-wrap items-end gap-2"
            onSubmit={async (e) => {
              e.preventDefault();
              setDevError("");
              setDevLoading(true);
              try {
                const id = parseInt(devTelegramId, 10);
                if (!Number.isFinite(id) || id <= 0) {
                  setDevError("Введите положительное число");
                  return;
                }
                const r = await fetch("/api/proxy/api/auth/dev-login", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ telegram_id: id }),
                });
                if (!r.ok) {
                  const err = await r.json().catch(() => ({}));
                  const msg =
                    typeof err.detail === "string"
                      ? err.detail
                      : Array.isArray(err.detail)
                        ? err.detail
                            .map((x: { msg?: string }) => x?.msg)
                            .filter(Boolean)
                            .join("; ")
                        : null;
                  throw new Error(msg || err.message || `Ошибка ${r.status}`);
                }
                const data = await r.json();
                if (data.access_token) {
                  localStorage.setItem("token", data.access_token);
                  window.location.href = "/dashboard";
                }
              } catch (err) {
                setDevError(err instanceof Error ? err.message : "Ошибка входа");
              } finally {
                setDevLoading(false);
              }
            }}
          >
            <label className="flex flex-col gap-1 text-xs text-amber-800">
              Telegram ID (число)
              <input
                type="number"
                min={1}
                value={devTelegramId}
                onChange={(e) => setDevTelegramId(e.target.value)}
                className="w-36 rounded border border-amber-300 bg-white px-2 py-1.5 text-sm"
              />
            </label>
            <Button type="submit" variant="primary" size="sm" disabled={devLoading}>
              {devLoading ? "Вход…" : "Войти для разработки"}
            </Button>
            {devError && <p className="w-full text-xs text-red-600">{devError}</p>}
          </form>
        </div>
      )}

      <div className="mt-6 border-t border-slate-100 pt-6">
        <ButtonLink href="/dashboard" variant="secondary" className="w-full justify-center">
          Перейти в кабинет
        </ButtonLink>
      </div>
    </>
  );
}
