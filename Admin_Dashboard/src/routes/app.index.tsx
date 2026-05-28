import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useMemo, useEffect } from "react";
import { 
  Search, Filter, CheckCircle2, Circle, 
  MessageCircle, ArrowUpRight, Inbox, ClipboardCheck, Package, TrendingUp 
} from "lucide-react";
import { fetchSubmissions } from "@/lib/api";
import { ARTISANS, STATUS_LABEL } from "@/lib/mock-data";

export const Route = createFileRoute("/app/")({
  component: InboxPage,
});

const STATUS_TONE: Record<string, string> = {
  intake: "bg-blue-500/10 text-blue-700 dark:text-blue-300",
  understanding: "bg-violet-500/10 text-violet-700 dark:text-violet-300",
  routing: "bg-cyan-500/10 text-cyan-700 dark:text-cyan-300",
  pricing: "bg-amber-500/10 text-amber-700 dark:text-amber-300",
  drafting: "bg-amber-500/10 text-amber-700 dark:text-amber-300",
  review: "bg-primary/10 text-primary",
  published: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
  rejected: "bg-destructive/10 text-destructive",
};

function timeAgo(iso: string) {
  const m = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (m < 60) return `${m}m ago`;
  return `${Math.round(m / 60)}h ago`;
}

function InboxPage() {
  const [submissions, setSubmissions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSubIds, setSelectedSubIds] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    fetchSubmissions().then((data) => {
      setSubmissions(data);
      setLoading(false);
    }).catch(console.error);
  }, []);

  const filtered = useMemo(() => {
    return submissions.filter((s) => {
      if (statusFilter !== "all" && s.status !== statusFilter) return false;
      if (search) {
        const query = search.toLowerCase();
        if (!s.craft.toLowerCase().includes(query)) return false;
      }
      return true;
    });
  }, [search, statusFilter, submissions]);

  const inReview = submissions.filter((s) => s.status === "review").length;
  const inFlight = submissions.filter((s) => !["published", "rejected"].includes(s.status)).length;
  const publishedToday = submissions.filter((s) => s.status === "published").length;

  const toggleAll = () => {
    if (selectedSubIds.size === filtered.length) setSelectedSubIds(new Set());
    else setSelectedSubIds(new Set(filtered.map((s) => s.id)));
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Stat label="In flight" value={inFlight} icon={Inbox} hint="Across all agents" />
        <Stat label="Awaiting review" value={inReview} icon={ClipboardCheck} hint="District admin queue" tone="primary" />
        <Stat label="Published today" value={publishedToday} icon={Package} hint="Across 3 marketplaces" />
        <Stat label="Active artisans" value={ARTISANS.length} icon={TrendingUp} hint="+2 this week" />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="rounded-xl border border-border bg-card xl:col-span-2">
          <div className="flex items-center justify-between border-b border-border px-5 py-3">
            <div>
              <h2 className="font-display text-lg text-ink">Live submissions</h2>
              <p className="text-xs text-muted-foreground">Photos & voice notes flowing in from WhatsApp</p>
            </div>
            <div className="flex items-center gap-2">
              <input type="text" placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} className="h-8 rounded-md border border-border bg-background px-3 text-xs" />
              <Link to="/app/review" className="text-xs font-medium text-primary hover:underline">Open review queue →</Link>
            </div>
          </div>
          {loading ? <div className="p-8 text-center text-sm text-muted-foreground">Loading...</div> : (
            <ul className="divide-y divide-border">
              {filtered.map((s) => (
                <li key={s.id}>
                  <Link 
                    to="/app/catalog/$id" 
                    params={{ id: s.id }} 
                    className="flex items-center gap-4 px-5 py-3 transition hover:bg-secondary/40"
                  >
                    <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-secondary text-xl overflow-hidden">
                      {s.thumbnail?.startsWith("http") || s.thumbnail?.startsWith("s3") ? (
                         <img src={s.thumbnail} className="h-full w-full object-cover" />
                      ) : (
                         s.thumbnail
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="truncate font-medium text-foreground">{s.craft}</span>
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider ${STATUS_TONE[s.status]}`}>
                          {STATUS_LABEL[s.status as keyof typeof STATUS_LABEL] || s.status}
                        </span>
                      </div>
                      <div className="mt-0.5 truncate text-xs text-muted-foreground">
                        {s.artisanName} · {s.cluster} · <MessageCircle className="inline h-3 w-3" /> {s.voiceLang}
                      </div>
                    </div>
                    <div className="hidden text-right text-xs text-muted-foreground sm:block">
                      <div>{s.id}</div>
                      <div>{timeAgo(s.receivedAt)}</div>
                    </div>
                    <ArrowUpRight className="h-4 w-4 text-muted-foreground" />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="space-y-6">
          <div className="rounded-xl border border-border bg-card p-5">
            <h2 className="font-display text-lg text-ink">North-star</h2>
            <p className="mt-1 text-xs text-muted-foreground">Listings published per artisan, per week</p>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="font-display text-4xl text-primary">3.8</span>
              <span className="text-xs font-medium text-emerald-600">▲ 0.4 vs last wk</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, icon: Icon, hint, tone }: { label: string; value: number | string; icon: any; hint: string; tone?: "primary" }) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-widest text-muted-foreground">{label}</span>
        <Icon className={`h-4 w-4 ${tone === "primary" ? "text-primary" : "text-muted-foreground"}`} />
      </div>
      <div className={`mt-3 font-display text-3xl ${tone === "primary" ? "text-primary" : "text-foreground"}`}>{value}</div>
      <div className="mt-1 text-xs text-muted-foreground">{hint}</div>
    </div>
  );
}