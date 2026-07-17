"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "./theme-provider";

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, toggleTheme } = useTheme();
  const isLight = theme === "light";
  const label = isLight ? "Включить тёмную тему" : "Включить светлую тему";
  const classes = className ? `theme-toggle ${className}` : "theme-toggle";

  return (
    <button
      type="button"
      className={classes}
      role="switch"
      aria-checked={isLight}
      aria-label={label}
      onClick={toggleTheme}
      suppressHydrationWarning
    >
      <span className="theme-toggle-track" aria-hidden="true">
        <Sun className="theme-toggle-icon theme-toggle-sun" />
        <Moon className="theme-toggle-icon theme-toggle-moon" />
        <span className="theme-toggle-thumb" />
      </span>
    </button>
  );
}
