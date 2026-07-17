import type { Metadata } from "next";
import "@fontsource-variable/inter/standard.css";
import "./globals.css";
import { ThemeProvider } from "./theme-provider";
import { Providers } from "./providers";

const themeInitializationScript = `
(function () {
  var theme = "dark";

  try {
    var savedTheme = window.localStorage.getItem("rerise-theme") || window.localStorage.getItem("code-theme");

    if (savedTheme === "dark" || savedTheme === "light") {
      theme = savedTheme;
    } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches) {
      theme = "light";
    }
  } catch (error) {
    try {
      if (window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches) {
        theme = "light";
      }
    } catch (matchMediaError) {}
  }

  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
})();
`;

const themeToggleInitializationScript = `
(function () {
  var isLight = document.documentElement.dataset.theme === "light";
  var label = isLight ? "Включить тёмную тему" : "Включить светлую тему";
  var toggles = document.querySelectorAll(".theme-toggle");

  for (var index = 0; index < toggles.length; index += 1) {
    toggles[index].setAttribute("aria-checked", String(isLight));
    toggles[index].setAttribute("aria-label", label);
  }
})();
`;

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
    <html lang="ru" data-theme="dark" style={{ colorScheme: "dark" }} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitializationScript }} />
      </head>
      <body>
        <ThemeProvider>
          <Providers>{children}</Providers>
        </ThemeProvider>
        <script dangerouslySetInnerHTML={{ __html: themeToggleInitializationScript }} />
      </body>
    </html>
  );
}
