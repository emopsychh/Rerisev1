export function PageShell({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <section className={`page-shell ${className}`.trim()}>
      {children}
    </section>
  );
}
