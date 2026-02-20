/**
 * @file: page.tsx
 * @description: Вход через Telegram Login Widget (данные с сервера).
 * @dependencies: next
 * @created: 2025-02-20
 */
import Link from "next/link";
import { LoginForm } from "./LoginForm";

export default function LoginPage() {
  const raw = (process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME || "").trim().replace(/^@/, "");
  const botUsername = raw === "LytSlotProBot" ? "LytSlotBot" : raw;
  const appUrl = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm rounded-2xl border border-slate-200/80 bg-white p-8 shadow-card">
        <Link href="/" className="font-display text-xl font-bold text-slate-900">
          LytSlot <span className="text-emerald-600">Pro</span>
        </Link>
        <h1 className="mt-6 text-xl font-semibold text-slate-900">Вход в кабинет</h1>
        <p className="mt-2 text-sm text-slate-500">Используйте Telegram для входа — без пароля.</p>
        <LoginForm botUsername={botUsername} appUrl={appUrl} />
      </div>
    </div>
  );
}
