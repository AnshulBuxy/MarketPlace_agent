import { createFileRoute, Link } from "@tanstack/react-router";
import heroImg from "@/assets/hero-artisan.jpg";
import craftsImg from "@/assets/crafts-grid.jpg";
import { ArrowRight, MessageCircle, Sparkles, ShieldCheck, Languages, Globe2, Mic, Camera, Send, CircleCheck, Workflow, Brain, Tag, IndianRupee, Boxes, Eye } from "lucide-react";

export const Route = createFileRoute("/")({
  component: Landing,
  head: () => ({
    meta: [
      { title: "Karigari — Agentic AI for India's Artisans" },
      { name: "description", content: "A WhatsApp-native AI orchestrator that lists India's heritage, homemade and GI-tagged products on every marketplace — in five minutes, in any language." },
    ],
  }),
});

function Landing() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <Nav />
      <Hero />
      <Marquee />
      <Problem />
      <Flow />
      <Agents />
      <Personas />
      <Metrics />
      <Roadmap />
      <CTA />
      <Footer />
    </main>
  );
}

function Nav() {
  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur-md">
      <div className="container-x flex h-16 items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-md text-primary-foreground" style={{ background: "var(--gradient-warm)" }}>
            <Sparkles className="h-4 w-4" />
          </span>
          <span className="font-display text-lg font-semibold tracking-tight">Karigari</span>
          <span className="ml-2 hidden rounded-full border border-border bg-secondary/60 px-2 py-0.5 text-[10px] uppercase tracking-widest text-muted-foreground sm:inline">PRD v1.0</span>
        </Link>
        <nav className="hidden items-center gap-8 text-sm text-muted-foreground md:flex">
          <a href="#flow" className="hover:text-foreground">Flow</a>
          <a href="#agents" className="hover:text-foreground">Agents</a>
          <a href="#personas" className="hover:text-foreground">Personas</a>
          <a href="#roadmap" className="hover:text-foreground">Roadmap</a>
          <Link to="/app" className="hover:text-foreground">Console</Link>
        </nav>
        <Link to="/app" className="inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-[var(--shadow-soft)] transition hover:opacity-90">
          Open console <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="relative overflow-hidden" style={{ background: "var(--gradient-sun)" }}>
      <div className="container-x grid grid-cols-1 gap-12 py-20 lg:grid-cols-12 lg:py-28">
        <div className="lg:col-span-6">
          <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-medium text-primary">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" /> Agentic AI Marketplace Orchestrator
          </span>
          <h1 className="mt-6 font-display text-5xl leading-[1.05] tracking-tight text-ink sm:text-6xl lg:text-7xl">
            From a WhatsApp photo<br />
            <em className="font-normal text-primary">to live listings</em><br />
            on every marketplace.
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-ink-soft">
            Karigari helps Indian artisans of heritage, homemade and GI-tagged crafts list across Amazon Karigar, Etsy, Flipkart Samarth, Jaypore, Meesho and more — using only a photo and a voice note in their language.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-4">
            <a href="#cta" className="inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-medium text-primary-foreground shadow-[var(--shadow-soft)] transition hover:translate-y-[-1px]">
              Start a pilot district <ArrowRight className="h-4 w-4" />
            </a>
            <a href="#flow" className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-5 py-3 text-sm font-medium text-foreground transition hover:bg-secondary">
              See the flow
            </a>
          </div>
          <dl className="mt-12 grid grid-cols-3 gap-6 border-t border-border/60 pt-8">
            {[
              ["< 5 min", "artisan effort"],
              ["14+", "Indian languages"],
              ["6+", "marketplaces"],
            ].map(([k, v]) => (
              <div key={v}>
                <dt className="font-display text-3xl text-primary">{k}</dt>
                <dd className="mt-1 text-xs uppercase tracking-widest text-muted-foreground">{v}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="relative lg:col-span-6">
          <div className="relative overflow-hidden rounded-3xl shadow-[var(--shadow-lift)]">
            <img src={heroImg} alt="An artisan sending a product photo via WhatsApp" width={1536} height={1152} className="h-full w-full object-cover" />
            <div className="absolute inset-0 bg-gradient-to-tr from-ink/30 via-transparent to-transparent" />
          </div>
          <FloatingCard className="absolute -left-4 bottom-8 sm:-left-8" />
          <PriceCard className="absolute -right-2 top-8 sm:-right-6" />
        </div>
      </div>
    </section>
  );
}

function FloatingCard({ className = "" }: { className?: string }) {
  return (
    <div className={`w-64 rounded-2xl border border-border bg-card p-4 shadow-[var(--shadow-soft)] ${className}`}>
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <MessageCircle className="h-3.5 w-3.5 text-primary" /> WhatsApp · Madhubani
      </div>
      <p className="mt-2 text-sm leading-snug text-foreground">
        ✅ Aapka product 3 jagah live ho gaya hai —
      </p>
      <ul className="mt-2 space-y-1 text-xs text-ink-soft">
        <li>• amazon.in/karigar/…</li>
        <li>• etsy.com/listing/…</li>
        <li>• jaypore.com/p/…</li>
      </ul>
    </div>
  );
}

function PriceCard({ className = "" }: { className?: string }) {
  return (
    <div className={`w-56 rounded-2xl border border-border bg-card p-4 shadow-[var(--shadow-soft)] ${className}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-widest text-muted-foreground">Suggested price</span>
        <Tag className="h-3.5 w-3.5 text-accent" />
      </div>
      <div className="mt-2 flex items-baseline gap-1 font-display text-3xl text-foreground">
        <IndianRupee className="h-5 w-5 text-primary" />2,450
      </div>
      <div className="mt-2 h-1 w-full rounded-full bg-secondary">
        <div className="h-1 w-2/3 rounded-full" style={{ background: "var(--gradient-warm)" }} />
      </div>
      <p className="mt-2 text-[11px] text-muted-foreground">Floor ₹1,800 · Ceiling ₹3,200</p>
    </div>
  );
}

function Marquee() {
  const items = ["Amazon Karigar", "Etsy", "Flipkart Samarth", "Jaypore", "Okhai", "GoCoop", "Meesho", "Blinkit", "Zepto", "Instamart"];
  return (
    <section className="border-y border-border/60 bg-secondary/30 py-6">
      <div className="container-x flex flex-wrap items-center justify-center gap-x-10 gap-y-3 text-sm text-muted-foreground">
        <span className="text-xs uppercase tracking-[0.2em]">Routes to</span>
        {items.map((m) => (
          <span key={m} className="font-medium text-ink-soft">{m}</span>
        ))}
      </div>
    </section>
  );
}

function Problem() {
  const items = [
    { icon: Camera, title: "One photo. Many marketplaces.", body: "Artisans shoot a single product photo. Karigari adapts catalog drafts to each marketplace's schema, conventions and audience." },
    { icon: Languages, title: "Voice in any language.", body: "Hindi, Tamil, Bhojpuri, Maithili, Bengali, Kannada, Marathi, Gujarati, Punjabi, Urdu, Assamese, Odia, Malayalam — captured natively." },
    { icon: ShieldCheck, title: "Human-in-the-loop quality.", body: "A regional admin reviews every draft before publish — preserving GI authenticity, attribution and provenance." },
  ];
  return (
    <section className="container-x py-24">
      <div className="grid grid-cols-1 gap-12 lg:grid-cols-12">
        <div className="lg:col-span-5">
          <h2 className="font-display text-4xl tracking-tight text-ink sm:text-5xl">
            Removing every barrier between<br /><em className="text-primary">skill</em> and the global buyer.
          </h2>
          <p className="mt-6 text-base leading-relaxed text-ink-soft">
            India's heritage producers are deeply skilled — but listing a product across modern marketplaces takes days, fluency in English, photography studios and operational know-how most artisans don't have.
          </p>
          <p className="mt-4 text-base leading-relaxed text-ink-soft">
            Karigari collapses that work into a five-minute WhatsApp exchange.
          </p>
        </div>
        <div className="grid grid-cols-1 gap-4 lg:col-span-7 sm:grid-cols-3">
          {items.map(({ icon: Icon, title, body }) => (
            <div key={title} className="rounded-2xl border border-border bg-card p-6 shadow-[var(--shadow-soft)] transition hover:translate-y-[-2px]">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-primary/10 text-primary">
                <Icon className="h-5 w-5" />
              </div>
              <h3 className="mt-4 font-display text-xl text-ink">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-soft">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Flow() {
  const steps = [
    { icon: Camera, title: "Capture", body: "Artisan sends a product photo to the Karigari WhatsApp number with an optional voice note." },
    { icon: Brain, title: "Understand", body: "Vision-language agents extract craft, materials, dimensions and motifs against an Indian craft taxonomy." },
    { icon: Workflow, title: "Route & draft", body: "Marketplace routing picks the best 2–4 channels; per-platform drafts are generated with titles, attributes, lifestyle imagery and price." },
    { icon: Eye, title: "Admin review", body: "A regional admin reviews drafts, edits low-confidence fields and approves — the human quality gate." },
    { icon: Send, title: "Publish", body: "Listings go live across selected marketplaces with platform-native compliance and attribution preserved." },
    { icon: CircleCheck, title: "Confirm on WhatsApp", body: "The artisan receives live URLs in their language, on the same channel where they began." },
  ];
  return (
    <section id="flow" className="bg-ink text-background">
      <div className="container-x py-24">
        <div className="flex flex-col items-end justify-between gap-6 sm:flex-row sm:items-end">
          <div>
            <span className="text-xs uppercase tracking-[0.25em] text-accent">The flow</span>
            <h2 className="mt-3 max-w-xl font-display text-4xl tracking-tight sm:text-5xl">
              From <em className="text-accent">click</em> to live listing,<br /> in under a few hours.
            </h2>
          </div>
          <p className="max-w-md text-sm leading-relaxed text-background/70">
            Six coordinated agents do the work of an entire e-commerce ops team — while the artisan only ever touches WhatsApp.
          </p>
        </div>
        <ol className="mt-14 grid grid-cols-1 gap-px overflow-hidden rounded-3xl border border-white/10 bg-white/5 sm:grid-cols-2 lg:grid-cols-3">
          {steps.map((s, i) => (
            <li key={s.title} className="relative bg-ink p-7">
              <div className="flex items-center justify-between">
                <span className="font-display text-sm text-accent/80">0{i + 1}</span>
                <s.icon className="h-5 w-5 text-accent" />
              </div>
              <h3 className="mt-6 font-display text-2xl text-background">{s.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-background/70">{s.body}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

function Agents() {
  const agents = [
    { icon: Mic, name: "Intake Agent", role: "Listens to voice notes and reads images on WhatsApp; transcribes regional languages and clarifies ambiguity politely." },
    { icon: Brain, name: "Product Understanding", role: "Extracts craft, materials, attributes and provenance against a curated Indian-craft taxonomy with confidence scores." },
    { icon: Workflow, name: "Marketplace Routing", role: "Picks the most suitable destinations based on category, season, price band and policy fit." },
    { icon: Tag, name: "Pricing Intelligence", role: "Recommends a fair price band using comparables, marketplace fees and artisan input — explains it in the artisan's language." },
    { icon: Boxes, name: "Catalog Generation", role: "Writes platform-native titles, descriptions, attributes and lifestyle imagery tuned to each marketplace's conventions." },
    { icon: Send, name: "Publishing & Notify", role: "Submits via APIs or partner ingestion; returns live URLs to the artisan and logs every step for audit." },
  ];
  return (
    <section id="agents" className="container-x py-24">
      <div className="max-w-2xl">
        <span className="text-xs uppercase tracking-[0.25em] text-primary">The agent mesh</span>
        <h2 className="mt-3 font-display text-4xl tracking-tight text-ink sm:text-5xl">
          Six specialised agents,<br /> <em className="text-primary">one calm interface.</em>
        </h2>
      </div>
      <div className="mt-14 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {agents.map((a, i) => (
          <article key={a.name} className="group relative overflow-hidden rounded-2xl border border-border bg-card p-7 shadow-[var(--shadow-soft)]">
            <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-accent/10 blur-2xl transition group-hover:bg-accent/20" />
            <div className="relative">
              <div className="flex items-center justify-between">
                <span className="font-display text-xs text-muted-foreground">Agent · 0{i + 1}</span>
                <a.icon className="h-5 w-5 text-primary" />
              </div>
              <h3 className="mt-5 font-display text-2xl text-ink">{a.name}</h3>
              <p className="mt-3 text-sm leading-relaxed text-ink-soft">{a.role}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function Personas() {
  return (
    <section id="personas" className="bg-secondary/40 py-24">
      <div className="container-x grid grid-cols-1 gap-16 lg:grid-cols-12">
        <div className="lg:col-span-5">
          <div className="overflow-hidden rounded-3xl shadow-[var(--shadow-lift)]">
            <img src={craftsImg} alt="Indian heritage crafts flat lay" width={1280} height={1280} loading="lazy" className="h-full w-full object-cover" />
          </div>
        </div>
        <div className="lg:col-span-7">
          <span className="text-xs uppercase tracking-[0.25em] text-primary">Built for two people</span>
          <h2 className="mt-3 font-display text-4xl tracking-tight text-ink sm:text-5xl">
            The artisan and<br /> <em className="text-primary">the regional admin.</em>
          </h2>
          <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2">
            <PersonaCard
              tag="Primary user"
              title="The Artisan"
              points={[
                "Madhubani, Channapatna, Banarasi, Pashmina, Bidri, terracotta and more",
                "Entry-level Android · WhatsApp-native · regional language",
                "Wants fair price, fast cash and dignity",
              ]}
            />
            <PersonaCard
              tag="Quality gate"
              title="The District Admin"
              points={[
                "Reviews 50–150 drafts/day from a desktop dashboard",
                "Trained on local craft, GI authenticity and marketplace policy",
                "Handles rejections, customisation and onboarding",
              ]}
            />
          </div>
        </div>
      </div>
    </section>
  );
}

function PersonaCard({ tag, title, points }: { tag: string; title: string; points: string[] }) {
  return (
    <div className="rounded-2xl border border-border bg-card p-6 shadow-[var(--shadow-soft)]">
      <span className="text-[11px] uppercase tracking-widest text-primary">{tag}</span>
      <h3 className="mt-2 font-display text-2xl text-ink">{title}</h3>
      <ul className="mt-4 space-y-2 text-sm text-ink-soft">
        {points.map((p) => (
          <li key={p} className="flex gap-2">
            <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-primary" />
            <span>{p}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Metrics() {
  const stats = [
    ["< 5 min", "Artisan effort per product"],
    ["2+", "Marketplaces per listing"],
    ["50–150", "Daily reviews per admin"],
    ["99.5%", "WhatsApp uptime SLO"],
  ];
  return (
    <section className="container-x py-24">
      <div className="rounded-3xl border border-border p-10 sm:p-14" style={{ background: "var(--gradient-warm)" }}>
        <div className="grid grid-cols-1 gap-12 text-primary-foreground lg:grid-cols-12">
          <div className="lg:col-span-5">
            <span className="text-xs uppercase tracking-[0.25em] text-primary-foreground/80">North-star metric</span>
            <h2 className="mt-3 font-display text-4xl tracking-tight sm:text-5xl">
              Listings published per artisan, per week.
            </h2>
            <p className="mt-5 max-w-md text-primary-foreground/80">
              Everything we build pushes one number up — without ever compromising on authenticity or admin quality.
            </p>
          </div>
          <dl className="grid grid-cols-2 gap-8 lg:col-span-7">
            {stats.map(([k, v]) => (
              <div key={v} className="border-t border-primary-foreground/30 pt-5">
                <dt className="font-display text-4xl">{k}</dt>
                <dd className="mt-2 text-xs uppercase tracking-widest text-primary-foreground/80">{v}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </section>
  );
}

function Roadmap() {
  const phases = [
    { tag: "Phase 1 · MVP", title: "Pilot district", body: "Single craft cluster, 2 API-rich marketplaces, mandatory admin approval, WhatsApp confirmation loop." },
    { tag: "Phase 2", title: "Order lifecycle", body: "Order, returns and settlement summaries on WhatsApp. Onboard 4+ marketplaces. Multi-cluster admin tooling." },
    { tag: "Phase 3", title: "Financial inclusion", body: "Pooled settlements, savings, credit scoring, customisation brokerage and reduced admin involvement on high-confidence drafts." },
  ];
  return (
    <section id="roadmap" className="container-x py-24">
      <div className="max-w-2xl">
        <span className="text-xs uppercase tracking-[0.25em] text-primary">12-month horizon</span>
        <h2 className="mt-3 font-display text-4xl tracking-tight text-ink sm:text-5xl">Roadmap</h2>
      </div>
      <ol className="mt-12 grid grid-cols-1 gap-px overflow-hidden rounded-3xl border border-border bg-border/50 md:grid-cols-3">
        {phases.map((p) => (
          <li key={p.title} className="bg-card p-8">
            <span className="text-[11px] uppercase tracking-widest text-primary">{p.tag}</span>
            <h3 className="mt-3 font-display text-2xl text-ink">{p.title}</h3>
            <p className="mt-3 text-sm leading-relaxed text-ink-soft">{p.body}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

function CTA() {
  return (
    <section id="cta" className="container-x pb-24">
      <div className="relative overflow-hidden rounded-3xl border border-border bg-ink p-12 text-background sm:p-16">
        <div className="absolute -right-20 -top-20 h-72 w-72 rounded-full bg-accent/30 blur-3xl" />
        <div className="absolute -left-10 -bottom-10 h-56 w-56 rounded-full bg-primary/40 blur-3xl" />
        <div className="relative grid grid-cols-1 gap-10 lg:grid-cols-12 lg:items-end">
          <div className="lg:col-span-7">
            <h2 className="font-display text-4xl leading-tight tracking-tight sm:text-5xl">
              Ready to bring a craft cluster<br /> <em className="text-accent">online in weeks, not years?</em>
            </h2>
            <p className="mt-5 max-w-xl text-background/70">
              We're piloting Karigari with cooperatives, FPOs, NGOs and craft boards. Bring us a district — we'll bring the agents.
            </p>
          </div>
          <div className="flex flex-wrap gap-3 lg:col-span-5 lg:justify-end">
            <a href="mailto:hello@karigari.in" className="inline-flex items-center gap-2 rounded-full bg-accent px-5 py-3 text-sm font-medium text-accent-foreground transition hover:translate-y-[-1px]">
              <MessageCircle className="h-4 w-4" /> Request a pilot
            </a>
            <a href="#flow" className="inline-flex items-center gap-2 rounded-full border border-white/20 px-5 py-3 text-sm font-medium text-background transition hover:bg-white/10">
              Read the PRD
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-border bg-secondary/30">
      <div className="container-x flex flex-col items-start justify-between gap-6 py-10 text-sm text-muted-foreground sm:flex-row sm:items-center">
        <div className="flex items-center gap-2">
          <span className="grid h-7 w-7 place-items-center rounded-md text-primary-foreground" style={{ background: "var(--gradient-warm)" }}>
            <Sparkles className="h-3.5 w-3.5" />
          </span>
          <span className="font-display text-base text-ink">Karigari</span>
          <span className="ml-2 hidden sm:inline">— heritage commerce, intelligently routed.</span>
        </div>
        <div className="flex items-center gap-6">
          <span className="inline-flex items-center gap-1"><Globe2 className="h-3.5 w-3.5" /> Made in India</span>
          <span>© 2026</span>
        </div>
      </div>
    </footer>
  );
}
