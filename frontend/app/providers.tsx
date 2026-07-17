"use client";

import { AuthProvider } from "../lib/auth/AuthProvider";
import { PortalBackendProvider } from "../lib/auth/PortalBackendProvider";
import { PortalRouter } from "../components/portal/PortalRouter";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <PortalBackendProvider>
        <PortalRouter>{children}</PortalRouter>
      </PortalBackendProvider>
    </AuthProvider>
  );
}
