/**
 * @file: page.tsx
 * @description: Лендинг — hero, ценность, CTA (премиум, UX).
 * @created: 2025-02-19
 */
import Link from "next/link";
import { ArrowRight, BarChart3, Calendar, Shield, Zap } from "lucide-react";
import { ButtonLink } from "@/components/ui/Button";

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-slate-100 bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link href="/" className="font-display text-xl font-bold text-slate-900">
            LytSlot <span className="text-emerald-600">Pro</span>
          </Link>
          <nav className="flex items-center gap-6 text-sm font-medium text-slate-600">
            <Link href="/#features" className="hover:text-slate-900">
              Возможности
            </Link>
            <Link href="/dashboard" className="hover:text-slate-900">
              Войти
            </Link>
            <ButtonLink href="/dashboard" variant="primary" size="sm">
              Кабинет
            </ButtonLink>
          </nav>
        </div>
      </header>

      <section className="border-b border-slate-100 bg-slate-50/50">
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28">
          <div className="mx-auto max-w-2xl text-center">
            <h1 className="font-display text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
              Реклама в Telegram-каналах под контролем
            </h1>
            <p className="mt-5 text-lg text-slate-600">
              Мульти-канальная платформа: слоты, заказы, аналитика и выплаты в одном кабинете.
              Регистрация через Telegram — без паролей.
            </p>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
              <ButtonLink href="/dashboard" variant="primary" size="lg" className="gap-2">
                Открыть кабинет
                <ArrowRight className="h-5 w-5" aria-hidden />
              </ButtonLink>
              <ButtonLink href="/login" variant="secondary" size="lg">
                Войти через Telegram
              </ButtonLink>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="border-b border-slate-100 bg-white py-16 sm:py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="font-display text-2xl font-bold text-slate-900 sm:text-3xl">
            Всё для монетизации каналов
          </h2>
          <p className="mt-2 text-slate-600">
            Один бот, тысячи каналов — настраивайте слоты, принимайте заказы и получайте аналитику.
          </p>
          <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {[
              {
                icon: Calendar,
                title: "Слоты 15/30/60 мин",
                text: "Гибкое расписание и динамические цены под каждый канал.",
              },
              {
                icon: BarChart3,
                title: "Views, CTR, выручка",
                text: "Метрики по постам и каналам в одном дашборде.",
              },
              {
                icon: Shield,
                title: "Безопасность и RLS",
                text: "Изоляция данных по тенанту, JWT и Telegram Login.",
              },
              {
                icon: Zap,
                title: "Один бот для всех",
                text: "Единый @LytSlotProBot — масштаб без лишней инфраструктуры.",
              },
            ].map(({ icon: Icon, title, text }) => (
              <div
                key={title}
                className="rounded-xl border border-slate-200/80 bg-white p-6 shadow-card transition-shadow hover:shadow-card-hover"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
                  <Icon className="h-5 w-5" aria-hidden />
                </div>
                <h3 className="mt-4 font-semibold text-slate-900">{title}</h3>
                <p className="mt-2 text-sm text-slate-500">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-b border-slate-100 bg-slate-50/50 py-16 sm:py-20">
        <div className="mx-auto max-w-6xl px-4 text-center sm:px-6">
          <h2 className="font-display text-2xl font-bold text-slate-900 sm:text-3xl">
            Готовы начать?
          </h2>
          <p className="mt-2 text-slate-600">Войдите через Telegram — кабинет откроется сразу.</p>
          <div className="mt-8">
            <ButtonLink href="/dashboard" variant="primary" size="lg" className="gap-2">
              Войти в кабинет
              <ArrowRight className="h-5 w-5" aria-hidden />
            </ButtonLink>
          </div>
        </div>
      </section>

      <footer className="bg-white py-8">
        <div className="mx-auto max-w-6xl px-4 text-center text-sm text-slate-500 sm:px-6">
          LytSlot Pro — платформа рекламы в Telegram-каналах. Multi-Channel Ad Platform.
        </div>
      </footer>
    </div>
  );
}
