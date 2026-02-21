/**
 * @file: layout.tsx
 * @description: Root layout - Next.js 15 App Router
 * @dependencies: next, react
 * @created: 2025-02-19
 */
import type { Metadata, Viewport } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const fontDisplay = Plus_Jakarta_Sans({
  subsets: ["latin", "latin-ext"],
  variable: "--font-display",
  display: "swap",
});

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export const metadata: Metadata = {
  title: "LytSlot Pro",
  description: "Платформа рекламы в Telegram-каналах — слоты, заказы, аналитика",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className={fontDisplay.variable}>
      <body className={`${fontDisplay.variable} font-sans antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
