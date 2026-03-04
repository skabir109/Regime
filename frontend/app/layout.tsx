import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Regime",
  description: "Market intelligence terminal for traders and desks.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
