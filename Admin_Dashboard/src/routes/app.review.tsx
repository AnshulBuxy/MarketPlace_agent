import { createFileRoute, Link } from "@tanstack/react-router";
import { SUBMISSIONS, STATUS_LABEL, getArtisan } from "@/lib/mock-data";
import { ArrowUpRight, Filter } from "lucide-react";

export const Route = createFileRoute("/app/review")({
  component: ReviewQueue,
});

function ReviewQueue() {
  const queue = SUBMISSIONS.filter((s) => ["review", "drafting", "intake"].includes(s.status));
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between rounded-xl border border-border bg-card p-4">
        <div>
          <h2 className="font-display text-lg text-ink">{queue.length} drafts awaiting review</h2>
          <p className="text-xs text-muted-foreground">Sorted by oldest first · approve before publish</p>
        </div>
        <button className="inline-flex items-center gap-2 rounded-md border border-border bg-background px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground">
          <Filter className="h-3.5 w-3.5" /> All clusters
        </button>
      </div>
      <div className="overflow-hidden rounded-xl border border-border bg-card">
        <table className="w-full text-sm">
          <thead className="border-b border-border bg-secondary/50 text-left text-[11px] uppercase tracking-widest text-muted-foreground">
            <tr>
              <th className="px-4 py-2.5">Submission</th>
              <th className="px-4 py-2.5">Artisan</th>
              <th className="px-4 py-2.5">Confidence</th>
              <th className="px-4 py-2.5">Routed to</th>
              <th className="px-4 py-2.5">Price</th>
              <th className="px-4 py-2.5">Status</th>
              <th className="px-4 py-2.5"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {queue.map((s) => {
              const a = getArtisan(s.artisanId)!;
              return (
                <tr key={s.id} className="transition hover:bg-secondary/40">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="grid h-9 w-9 place-items-center rounded-md bg-secondary text-lg">{s.thumbnail}</div>
                      <div>
                        <div className="font-medium text-foreground">{s.craft}</div>
                        <div className="text-xs text-muted-foreground">{s.id}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-foreground">{a.name}</div>
                    <div className="text-xs text-muted-foreground">{a.cluster}</div>
                  </td>
                  <td className="px-4 py-3">
                    {s.confidence > 0 ? (
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-16 overflow-hidden rounded-full bg-secondary">
                          <div className={`h-full ${s.confidence >= 0.9 ? "bg-emerald-500" : s.confidence >= 0.8 ? "bg-amber-500" : "bg-destructive"}`} style={{ width: `${s.confidence * 100}%` }} />
                        </div>
                        <span className="text-xs text-muted-foreground">{Math.round(s.confidence * 100)}%</span>
                      </div>
                    ) : <span className="text-xs text-muted-foreground">—</span>}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">{s.routedTo.join(", ") || "—"}</td>
                  <td className="px-4 py-3 text-foreground">{s.suggestedPrice.mid ? `₹${s.suggestedPrice.mid.toLocaleString("en-IN")}` : "—"}</td>
                  <td className="px-4 py-3"><span className="rounded-full bg-secondary px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-foreground">{STATUS_LABEL[s.status]}</span></td>
                  <td className="px-4 py-3 text-right">
                    <Link to="/app/review/$id" params={{ id: s.id }} className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline">
                      Review <ArrowUpRight className="h-3 w-3" />
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}