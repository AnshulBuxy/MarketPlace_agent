import { createFileRoute } from "@tanstack/react-router";
import { AGENTS } from "@/lib/mock-data";

export const Route = createFileRoute("/app/agents")({
  component: Agents,
});

function Agents() {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-border bg-card p-4">
        <h2 className="font-display text-lg text-ink">Agent mesh</h2>
        <p className="text-xs text-muted-foreground">Six specialised agents · last 24h</p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {AGENTS.map((a) => (
          <div key={a.key} className="rounded-xl border border-border bg-card p-5">
            <div className="flex items-center justify-between">
              <div className="grid h-10 w-10 place-items-center rounded-lg bg-primary/10 text-primary">
                <a.icon className="h-5 w-5" />
              </div>
              <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-widest ${a.status === "healthy" ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300" : "bg-amber-500/10 text-amber-700 dark:text-amber-300"}`}>
                ● {a.status}
              </span>
            </div>
            <h3 className="mt-4 font-display text-lg text-ink">{a.name}</h3>
            <dl className="mt-4 grid grid-cols-2 gap-3 border-t border-border pt-3 text-sm">
              <div>
                <dt className="text-[10px] uppercase tracking-widest text-muted-foreground">Throughput / 24h</dt>
                <dd className="font-display text-xl text-foreground">{a.throughput}</dd>
              </div>
              <div>
                <dt className="text-[10px] uppercase tracking-widest text-muted-foreground">P50 latency</dt>
                <dd className="font-display text-xl text-foreground">{a.p50}s</dd>
              </div>
            </dl>
          </div>
        ))}
      </div>
    </div>
  );
}