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
      <body>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function () {
                var key = "regime_chunk_reload_once";
                function shouldHandle(message) {
                  if (!message) return false;
                  var text = String(message).toLowerCase();
                  return text.indexOf("chunkloaderror") !== -1 || text.indexOf("loading chunk") !== -1;
                }
                function reloadOnce() {
                  try {
                    if (sessionStorage.getItem(key) === "1") return;
                    sessionStorage.setItem(key, "1");
                    window.location.reload();
                  } catch (e) {
                    window.location.reload();
                  }
                }
                window.addEventListener("error", function (event) {
                  if (shouldHandle(event && event.message)) reloadOnce();
                });
                window.addEventListener("unhandledrejection", function (event) {
                  var reason = event && event.reason;
                  var message =
                    (reason && (reason.message || reason.name || reason.toString && reason.toString())) ||
                    "";
                  if (shouldHandle(message)) reloadOnce();
                });
                window.addEventListener("load", function () {
                  try { sessionStorage.removeItem(key); } catch (e) {}
                });
              })();
            `,
          }}
        />
        {children}
      </body>
    </html>
  );
}
