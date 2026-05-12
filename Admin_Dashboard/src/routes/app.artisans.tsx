import { createFileRoute } from "@tanstack/react-router";
import { ARTISANS } from "@/lib/mock-data";

export const Route = createFileRoute("/app/artisans")({
  component: Artisans,
});

function Artisans() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between rounded-xl border border-border bg-card p-4">
        <div>
          <h2 className="font-display text-lg text-ink">{ARTISANS.length} active artisans</h2>
          <p className="text-xs text-muted-foreground">Across 6 craft clusters</p>
        </div>
        <button className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:opacity-90">
          Onboard artisan
        </button>
      </div>
      <div className="overflow-hidden rounded-xl border border-border bg-card">
        <table className="w-full text-sm">
          <thead className="border-b border-border bg-secondary/50 text-left text-[11px] uppercase tracking-widest text-muted-foreground">
            <tr>
              <th className="px-4 py-2.5">Artisan</th>
              <th className="px-4 py-2.5">Cluster · craft</th>
              <th className="px-4 py-2.5">Language</th>
              <th className="px-4 py-2.5">Listings</th>
              <th className="px-4 py-2.5">Earnings (₹)</th>
              <th className="px-4 py-2.5">WhatsApp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {ARTISANS.map((a) => (
              <tr key={a.id} className="transition hover:bg-secondary/40">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="grid h-9 w-9 place-items-center rounded-full text-xs font-semibold text-primary-foreground" style={{ background: "var(--gradient-warm)" }}>
                      {a.name.split(" ").map((n) => n[0]).slice(0, 2).join("")}
                    </div>
                    <div>
                      <div className="font-medium text-foreground">{a.name}</div>
                      <div className="text-xs text-muted-foreground">Joined {a.joined}</div>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="text-foreground">{a.cluster}</div>
                  <div className="text-xs text-muted-foreground">{a.craft}</div>
                </td>
                <td className="px-4 py-3 text-foreground">{a.language}</td>
                <td className="px-4 py-3 text-foreground">{a.listings}</td>
                <td className="px-4 py-3 text-foreground">₹{a.earnings.toLocaleString("en-IN")}</td>
                <td className="px-4 py-3 text-xs text-muted-foreground">{a.phone}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}