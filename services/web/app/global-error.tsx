"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";

/**
 * Captures React render errors and shows fallback UI.
 * Sentry.captureException is no-op when DSN is not set.
 */
export default function GlobalError({ error }: { error: Error & { digest?: string } }) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <html lang="ru">
      <body>
        <div style={{ padding: "2rem", fontFamily: "system-ui" }}>
          <h1>Что-то пошло не так</h1>
          <p>Ошибка зафиксирована. Попробуйте обновить страницу.</p>
        </div>
      </body>
    </html>
  );
}
