import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Regime",
  description: "Market intelligence terminal for traders and desks.",
  icons: {
    icon: "/icon.svg",
    shortcut: "/icon.svg",
    apple: "/icon.svg",
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
