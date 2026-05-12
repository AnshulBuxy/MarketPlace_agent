import { createFileRoute } from "@tanstack/react-router";
import { WEEKLY_LISTINGS } from "@/lib/mock-data";

export const Route = createFileRoute("/app/analytics")({
  component: Analytics,
});

function Analytics() {
  const max = Math.max(...WEEKLY_LISTINGS.map((w) => w.count));
  const totals = [
    { k: "Listings published / artisan / wk", v: "3.8", delta: "+0.4" },
    { k: "Median time to live", v: "2h 14m", delta: "−18m" },
    { k: "Approval rate", v: "87%", delta: "+3%" },
    { k: "Avg order value", v: "₹2,840", delta: "+₹120" },
  ];
  const breakdown = [
    { mp: "Amazon Karigar", pct: 38 },
    { mp: "Etsy", pct: 24 },
    { mp: "Jaypore", pct: 18 },
    { mp: "Flipkart Samarth", pct: 12 },
    { mp: "Okhai", pct: 8 },
  ];
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        {totals.map((t) => (
          <div key={t.k} className="rounded-xl border border-border bg-card p-4">
            <div className="text-xs uppercase tracking-widest text-muted-foreground">{t.k}</div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="font-display text-3xl text-foreground">{t.v}</span>
              <span className="text-xs font-medium text-emerald-600">▲ {t.delta}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="rounded-xl border border-border bg-card p-5 lg:col-span-2">
          <h2 className="font-display text-lg text-ink">Listings published / week</h2>
          <p className="text-xs text-muted-foreground">Last 5 weeks · all clusters</p>
          <div className="mt-6 flex h-64 items-end gap-3">
            {WEEKLY_LISTINGS.map((w) => (
              <div key={w.week} className="flex flex-1 flex-col items-center gap-2">
                <div className="text-xs font-medium text-foreground">{w.count}</div>
                <div className="w-full rounded-t-md transition-all" style={{ height: `${(w.count / max) * 100}%`, background: "var(--gradient-warm)" }} />
                <div className="text-[10px] uppercase tracking-widest text-muted-foreground">{w.week}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-border bg-card p-5">
          <h2 className="font-display text-lg text-ink">Marketplace mix</h2>
          <p className="text-xs text-muted-foreground">Share of live listings</p>
          <ul className="mt-4 space-y-3">
            {breakdown.map((b) => (
              <li key={b.mp}>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-foreground">{b.mp}</span>
                  <span className="text-muted-foreground">{b.pct}%</span>
                </div>
                <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                  <div className="h-full rounded-full" style={{ width: `${b.pct}%`, background: "var(--gradient-warm)" }} />
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}