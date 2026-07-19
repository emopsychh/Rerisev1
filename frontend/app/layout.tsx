import type { Metadata } from "next";
import "@fontsource-variable/inter/standard.css";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "RE:RISE",
  description: "AI workspace, learning, marketplace, and partner tools.",
  icons: {
    icon: [{ url: "/icon.svg", type: "image/svg+xml" }],
    shortcut: "/icon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" data-theme="dark" style={{ colorScheme: "dark" }}>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
