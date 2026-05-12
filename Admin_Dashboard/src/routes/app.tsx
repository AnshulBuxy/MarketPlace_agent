import { createFileRoute, Outlet, useRouterState } from "@tanstack/react-router";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { Bell, Search } from "lucide-react";

export const Route = createFileRoute("/app")({
  component: AppLayout,
  head: () => ({ meta: [{ title: "Karigari · Operator console" }] }),
});

const TITLES: Record<string, string> = {
  "/app": "Inbox",
  "/app/review": "Review queue",
  "/app/listings": "Listings",
  "/app/agents": "Agent mesh",
  "/app/artisans": "Artisans",
  "/app/analytics": "Analytics",
};

function AppLayout() {
  const path = useRouterState({ select: (r) => r.location.pathname });
  const title = TITLES[path] ?? (path.startsWith("/app/review/") ? "Submission review" : "Karigari");
  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full bg-secondary/30">
        <AppSidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur">
            <SidebarTrigger />
            <div className="h-5 w-px bg-border" />
            <h1 className="font-display text-lg text-ink">{title}</h1>
            <div className="ml-auto flex items-center gap-2">
              <div className="hidden items-center gap-2 rounded-md border border-border bg-card px-2.5 py-1.5 text-xs text-muted-foreground sm:flex">
                <Search className="h-3.5 w-3.5" />
                <span>Search artisans, listings…</span>
                <kbd className="ml-2 rounded bg-secondary px-1.5 py-0.5 text-[10px] text-foreground">⌘K</kbd>
              </div>
              <button className="relative grid h-8 w-8 place-items-center rounded-md border border-border bg-card text-muted-foreground hover:text-foreground">
                <Bell className="h-4 w-4" />
                <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-primary" />
              </button>
              <div className="grid h-8 w-8 place-items-center rounded-full text-xs font-semibold text-primary-foreground" style={{ background: "var(--gradient-warm)" }}>
                RA
              </div>
            </div>
          </header>
          <main className="flex-1 p-6">
            <Outlet />
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}