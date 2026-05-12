import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { getSubmission, getArtisan, STATUS_LABEL } from "@/lib/mock-data";
import { ArrowLeft, Bot, Check, MessageCircle, Ruler, Sparkles, Tag, X } from "lucide-react";

export const Route = createFileRoute("/app/review/$id")({
  component: SubmissionDetail,
  loader: ({ params }) => {
    const s = getSubmission(params.id);
    if (!s) throw notFound();
    return { submission: s };
  },
  notFoundComponent: () => (
    <div className="rounded-xl border border-border bg-card p-8 text-center">
      <p className="text-muted-foreground">Submission not found.</p>
      <Link to="/app/review" className="mt-3 inline-block text-sm text-primary hover:underline">Back to queue</Link>
    </div>
  ),
  errorComponent: ({ error }) => (
    <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-sm text-destructive">{error.message}</div>
  ),
});

function SubmissionDetail() {
  const { submission: s } = Route.useLoaderData();
  const a = getArtisan(s.artisanId)!;

  return (
    <div className="space-y-6">
      <Link to="/app/review" className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-3 w-3" /> Back to queue
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-4 rounded-xl border border-border bg-card p-5">
        <div className="flex items-center gap-4">
          <div className="grid h-14 w-14 place-items-center rounded-xl bg-secondary text-3xl">{s.thumbnail}</div>
          <div>
            <div className="text-xs uppercase tracking-widest text-muted-foreground">{s.id} · {STATUS_LABEL[s.status]}</div>
            <h2 className="font-display text-2xl text-ink">{s.craft}</h2>
            <div className="mt-1 text-sm text-muted-foreground">{a.name} · {a.cluster} · <MessageCircle className="inline h-3 w-3" /> {s.voiceLang}</div>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="inline-flex items-center gap-1.5 rounded-md border border-border bg-background px-3 py-2 text-xs font-medium text-foreground hover:bg-secondary">
            <X className="h-3.5 w-3.5" /> Reject
          </button>
          <button className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:opacity-90">
            <Check className="h-3.5 w-3.5" /> Approve & publish
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-4">
          <Card title="Voice transcript" icon={MessageCircle}>
            <p className="text-sm leading-relaxed text-foreground">"{s.voiceTranscript}"</p>
            <div className="mt-3 text-[11px] uppercase tracking-widest text-muted-foreground">Original: {s.voiceLang}</div>
          </Card>
          <Card title="Extracted attributes" icon={Sparkles}>
            <dl className="space-y-2 text-sm">
              <Row k="Materials" v={s.materials.join(", ") || "—"} />
              <Row k="Dimensions" v={s.dimensions} />
              <Row k="Motifs" v={s.motifs.join(", ") || "—"} />
              <Row k="Confidence" v={s.confidence ? `${Math.round(s.confidence * 100)}%` : "—"} />
            </dl>
          </Card>
          <Card title="Pricing" icon={Tag}>
            {s.suggestedPrice.mid ? (
              <>
                <div className="font-display text-3xl text-foreground">₹{s.suggestedPrice.mid.toLocaleString("en-IN")}</div>
                <div className="mt-3 h-1.5 w-full rounded-full bg-secondary">
                  <div className="h-full w-2/3 rounded-full" style={{ background: "var(--gradient-warm)" }} />
                </div>
                <div className="mt-2 flex justify-between text-[11px] text-muted-foreground">
                  <span>Floor ₹{s.suggestedPrice.floor.toLocaleString("en-IN")}</span>
                  <span>Ceiling ₹{s.suggestedPrice.ceiling.toLocaleString("en-IN")}</span>
                </div>
              </>
            ) : <p className="text-sm text-muted-foreground">Awaiting pricing agent…</p>}
          </Card>
        </div>

        <div className="space-y-4 lg:col-span-2">
          <Card title={`Marketplace drafts (${s.drafts.length})`} icon={Ruler}>
            {s.drafts.length === 0 ? (
              <p className="text-sm text-muted-foreground">Catalog agent is generating drafts…</p>
            ) : (
              <div className="space-y-3">
                {s.drafts.map((d) => (
                  <div key={d.marketplace} className="rounded-lg border border-border bg-background p-4">
                    <div className="flex items-center justify-between">
                      <span className="rounded-full bg-secondary px-2 py-0.5 text-[10px] font-medium uppercase tracking-widest text-foreground">{d.marketplace}</span>
                      <span className="font-medium text-foreground">{d.marketplace === "Etsy" ? `$${d.price}` : `₹${d.price.toLocaleString("en-IN")}`}</span>
                    </div>
                    <h3 className="mt-2 font-medium text-foreground">{d.title}</h3>
                    {d.bullets.length > 0 && (
                      <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
                        {d.bullets.map((b) => <li key={b}>• {b}</li>)}
                      </ul>
                    )}
                    {Object.keys(d.attributes).length > 0 && (
                      <div className="mt-3 grid grid-cols-2 gap-2 border-t border-border pt-3 text-xs">
                        {Object.entries(d.attributes).map(([k, v]) => (
                          <div key={k}>
                            <div className="text-[10px] uppercase tracking-widest text-muted-foreground">{k}</div>
                            <div className="text-foreground">{v}</div>
                          </div>
                        ))}
                      </div>
                    )}
                    {d.url && <div className="mt-3 text-xs text-emerald-600">● Live · {d.url}</div>}
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card title="Agent trace" icon={Bot}>
            <ol className="relative space-y-3 border-l border-border pl-5">
              {s.logs.map((l, i) => (
                <li key={i} className="relative">
                  <span className="absolute -left-[26px] top-1.5 h-2 w-2 rounded-full bg-primary" />
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="text-xs font-medium text-foreground">{l.agent}</span>
                    <span className="text-[10px] text-muted-foreground">{l.ts}</span>
                  </div>
                  <p className="text-sm text-muted-foreground">{l.message}</p>
                </li>
              ))}
            </ol>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Card({ title, icon: Icon, children }: { title: string; icon: any; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-card">
      <div className="flex items-center gap-2 border-b border-border px-4 py-3">
        <Icon className="h-4 w-4 text-primary" />
        <h3 className="font-display text-sm text-ink">{title}</h3>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-border pb-2 last:border-0">
      <dt className="text-xs uppercase tracking-widest text-muted-foreground">{k}</dt>
      <dd className="text-right text-foreground">{v}</dd>
    </div>
  );
}