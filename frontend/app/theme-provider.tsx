"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

export type Theme = "dark" | "light";

type ThemeContextValue = {
  theme: Theme;
  toggleTheme: () => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);
const THEME_STORAGE_KEY = "rerise-theme";
const LEGACY_THEME_STORAGE_KEY = "code-theme";
const THEME_TRANSITION_DURATION = 220;

type ViewTransitionDocument = Document & {
  startViewTransition?: (update: () => void) => { finished: Promise<void> };
};

function isTheme(value: string | undefined | null): value is Theme {
  return value === "dark" || value === "light";
}

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  root.dataset.theme = theme;
  root.style.colorScheme = theme;
}

function readMountedTheme(): Theme {
  const earlyTheme = document.documentElement.dataset.theme;

  if (isTheme(earlyTheme)) {
    return earlyTheme;
  }

  try {
    const savedTheme = window.localStorage.getItem(THEME_STORAGE_KEY) ?? window.localStorage.getItem(LEGACY_THEME_STORAGE_KEY);

    if (isTheme(savedTheme)) {
      return savedTheme;
    }
  } catch {
    // Storage can be unavailable in restricted browsing modes.
  }

  try {
    if (window.matchMedia("(prefers-color-scheme: light)").matches) {
      return "light";
    }
  } catch {
    // Fall back to the portal's existing dark theme.
  }

  return "dark";
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>("dark");

  useEffect(() => {
    const mountedTheme = readMountedTheme();
    setThemeState(mountedTheme);
    applyTheme(mountedTheme);
  }, []);

  const setTheme = useCallback((nextTheme: Theme) => {
    const root = document.documentElement;
    const commitTheme = () => {
      setThemeState(nextTheme);
      applyTheme(nextTheme);

      try {
        window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
      } catch {
        // The in-memory and document themes still update when storage is blocked.
      }
    };

    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    const startViewTransition = (document as ViewTransitionDocument).startViewTransition;

    if (!reduceMotion && startViewTransition) {
      root.classList.add("theme-view-transition");
      const transition = startViewTransition.call(document, commitTheme);
      void transition.finished.finally(() => root.classList.remove("theme-view-transition"));
      return;
    }

    if (!reduceMotion) {
      root.classList.add("theme-switching");
      window.setTimeout(() => root.classList.remove("theme-switching"), THEME_TRANSITION_DURATION);
    }

    commitTheme();
  }, []);

  const toggleTheme = useCallback(() => {
    const appliedTheme = document.documentElement.dataset.theme;
    const currentTheme = isTheme(appliedTheme) ? appliedTheme : theme;
    setTheme(currentTheme === "dark" ? "light" : "dark");
  }, [setTheme, theme]);

  const value = useMemo<ThemeContextValue>(
    () => ({ theme, toggleTheme }),
    [theme, toggleTheme],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);

  if (!context) {
    throw new Error("useTheme must be used within ThemeProvider");
  }

  return context;
}
