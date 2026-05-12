import { createFileRoute } from "@tanstack/react-router";
import { SUBMISSIONS, getArtisan } from "@/lib/mock-data";
import { ExternalLink } from "lucide-react";

export const Route = createFileRoute("/app/listings")({
  component: Listings,
});

function Listings() {
  const live = SUBMISSIONS.filter((s) => s.status === "published").flatMap((s) =>
    s.drafts.filter((d) => d.url).map((d) => ({ ...d, sub: s, artisan: getArtisan(s.artisanId)! })),
  );
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-border bg-card p-4">
        <h2 className="font-display text-lg text-ink">{live.length} live listings</h2>
        <p className="text-xs text-muted-foreground">Across {new Set(live.map((l) => l.marketplace)).size} marketplaces</p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {live.map((l, i) => (
          <article key={i} className="rounded-xl border border-border bg-card p-4">
            <div className="flex items-center justify-between">
              <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-widest text-primary">{l.marketplace}</span>
              <span className="text-xs text-emerald-600">● Live</span>
            </div>
            <div className="mt-3 grid h-32 place-items-center rounded-lg bg-secondary text-5xl">{l.sub.thumbnail}</div>
            <h3 className="mt-3 line-clamp-2 font-medium text-foreground">{l.title}</h3>
            <div className="mt-2 text-xs text-muted-foreground">{l.artisan.name} · {l.artisan.cluster}</div>
            <div className="mt-3 flex items-center justify-between border-t border-border pt-3">
              <span className="font-display text-lg text-foreground">{l.marketplace === "Etsy" ? `$${l.price}` : `₹${l.price.toLocaleString("en-IN")}`}</span>
              <a href={`https://${l.url}`} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline">
                Visit <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}