import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import {
  ArrowLeft, Search, Sparkles, Check, Package, TrendingUp,
  Edit3, Loader2, IndianRupee, User, MapPin,
  Zap, Star, Send, CircleCheck, ShoppingBag, X, ChevronRight,
  Eye, Layers, Camera, Truck, BadgePercent, Users,
} from "lucide-react";

import heroOriginal from "@/assets/Products/Origin_Image.png";
import aiImage1 from "@/assets/Products/image.png";
import aiImage2 from "@/assets/Products/image copy.png";
import aiImage3 from "@/assets/Products/image copy 2.png";
import aiImage4 from "@/assets/Products/image copy 3.png";

export const Route = createFileRoute("/app/catalog/$id")({
  component: CatalogWizard,
  head: () => ({ meta: [{ title: "Banao · Create catalog" }] }),
});

/* ─── constants ─── */

const PRODUCT = {
  name: "Handcrafted Metal Boat Pen Holder",
  category: "Home Decor",
  materials: ["Metal", "Brass", "Wrought Iron"],
  dimensions: "~15–20 cm in length",
  description:
    "An intricate handcrafted metal showpiece shaped like a traditional boat (Mayurpankhi) featuring figures of musicians and a mesh-style pen holder. Finished in a golden metallic tone with red and black decorative accents.",
  sender: { name: "Ravi Sharma", location: "Moradabad, UP", phone: "+91 93••• 44821" },
  confidence: [
    { label: "Category", value: 0.95 },
    { label: "Materials", value: 0.92 },
    { label: "Description", value: 0.91 },
    { label: "Craftsmanship", value: 0.89 },
    { label: "Dimensions", value: 0.88 },
  ],
};

const MARKETPLACES = [
  { name: "Amazon Karigar", emoji: "🛒", price: 950, currency: "₹", fit: 92, category: "Home & Kitchen › Showpieces", fees: "15% referral", delivery: "2–4 days", audience: "Premium Indian buyers", desc: "Best for heritage visibility with Karigar program benefits." },
  { name: "Etsy", emoji: "🎨", price: 1150, currency: "₹", fit: 88, category: "Home Decor › Desk Accessories", fees: "6.5% + ₹16", delivery: "7–14 days intl.", audience: "Global craft enthusiasts", desc: "Ideal for international exposure and premium pricing." },
  { name: "Flipkart Samarth", emoji: "📦", price: 1050, currency: "₹", fit: 85, category: "Handicraft › Metal Art", fees: "10% commission", delivery: "3–5 days", audience: "Mass Indian market", desc: "Large user base with Samarth artisan support program." },
  { name: "Meesho", emoji: "🧡", price: 799, currency: "₹", fit: 78, category: "Home Decor › Showpiece", fees: "0% commission", delivery: "5–7 days", audience: "Value-conscious buyers", desc: "Zero commission model with social commerce reach." },
];

const AI_IMAGES = [
  { label: "Original Shot", img: heroOriginal, bg: "from-amber-800/30 to-yellow-600/20" },
  { label: "Studio White", img: aiImage1, bg: "from-slate-200/40 to-amber-100/30" },
  { label: "Detail Close-up", img: aiImage2, bg: "from-rose-700/20 to-amber-600/20" },
  { label: "Aerial View", img: aiImage3, bg: "from-stone-300/30 to-amber-200/20" },
  { label: "Lifestyle", img: aiImage4, bg: "from-emerald-900/20 to-amber-600/20" },
];

const STEP_KEYS = ["detail", "searching", "pricing", "optimum", "catalog", "publishing", "live"] as const;
type Step = (typeof STEP_KEYS)[number];
const userSteps = [
  { key: "detail", label: "Details" },
  { key: "pricing", label: "Pricing" },
  { key: "optimum", label: "Price" },
  { key: "catalog", label: "Catalog" },
  { key: "publishing", label: "Publish" },
];

/* ─── helpers ─── */

function stepIndex(s: Step) {
  const map: Record<string, number> = { detail: 0, searching: 1, pricing: 1, optimum: 2, catalog: 3, publishing: 4, live: 4 };
  return map[s] ?? 0;
}

function ConfidenceBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 90 ? "bg-emerald-500" : pct >= 80 ? "bg-amber-500" : "bg-destructive";
  return (
    <div className="flex items-center gap-3">
      <span className="w-28 text-xs text-muted-foreground">{label}</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-secondary">
        <div className={`h-full rounded-full transition-all duration-700 ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-10 text-right text-xs font-medium text-foreground">{pct}%</span>
    </div>
  );
}

/* ─── main component ─── */

function CatalogWizard() {
  const [step, setStep] = useState<Step>("detail");
  const [cardsRevealed, setCardsRevealed] = useState(0);
  const [priceCounter, setPriceCounter] = useState(0);
  const [priceConfirmed, setPriceConfirmed] = useState(false);
  const [selectedImages, setSelectedImages] = useState<Set<number>>(new Set([0]));
  const [selectedMarketplaces, setSelectedMarketplaces] = useState<Set<number>>(new Set());
  const [publishProgress, setPublishProgress] = useState(0);
  const [publishingMp, setPublishingMp] = useState("");
  const [catalogTitle, setCatalogTitle] = useState("Handcrafted Brass Boat Pen Holder — Mayurpankhi Design");
  const [catalogDesc, setCatalogDesc] = useState(PRODUCT.description);
  const [editingField, setEditingField] = useState<string | null>(null);
  const [animKey, setAnimKey] = useState(0); // force re-mount for animations
  const [isGenerating, setIsGenerating] = useState(false);
  const [genSubStep, setGenSubStep] = useState(0);

  const GEN_SUBSTEPS = [
    "Analyzing lighting...",
    "Extracting textures...",
    "Synthesizing angles...",
    "Upscaling details...",
    "Finalizing shots..."
  ];

  /* AI generation sequence trigger */
  useEffect(() => {
    if (step === "catalog") {
      setIsGenerating(true);
      setGenSubStep(0);
      const timers = GEN_SUBSTEPS.map((_, i) => 
        setTimeout(() => setGenSubStep(i), i * 800)
      );
      timers.push(setTimeout(() => setIsGenerating(false), GEN_SUBSTEPS.length * 800 + 400));
      return () => timers.forEach(clearTimeout);
    }
  }, [step]);

  /* searching → cards reveal one by one */
  useEffect(() => {
    if (step !== "searching") return;
    setCardsRevealed(0);
    const timers = MARKETPLACES.map((_, i) =>
      setTimeout(() => setCardsRevealed(i + 1), 1000 + i * 700),
    );
    timers.push(setTimeout(() => setStep("pricing"), 1000 + MARKETPLACES.length * 700 + 300));
    return () => timers.forEach(clearTimeout);
  }, [step]);

  /* optimum price counter */
  useEffect(() => {
    if (step !== "optimum") return;
    setPriceCounter(0);
    setPriceConfirmed(false);
    let cur = 0;
    const target = 950;
    const id = setInterval(() => {
      cur += Math.ceil((target - cur) * 0.07) + 2;
      if (cur >= target) { cur = target; clearInterval(id); }
      setPriceCounter(cur);
    }, 18);
    return () => clearInterval(id);
  }, [step]);

  /* publishing progress */
  useEffect(() => {
    if (step !== "publishing") return;
    setPublishProgress(0);
    const mps = [...selectedMarketplaces].map((i) => MARKETPLACES[i].name);
    let idx = 0;
    setPublishingMp(mps[0] ?? "");
    let p = 0;
    const id = setInterval(() => {
      p += Math.random() * 8 + 4;
      if (p >= 100) { p = 100; clearInterval(id); setTimeout(() => setStep("live"), 800); }
      setPublishProgress(Math.min(p, 100));
      const newIdx = Math.min(Math.floor((p / 100) * mps.length), mps.length - 1);
      if (newIdx !== idx) { idx = newIdx; setPublishingMp(mps[idx]); }
    }, 200);
    return () => clearInterval(id);
  }, [step, selectedMarketplaces]);

  const goTo = (s: Step) => { setAnimKey((k) => k + 1); setStep(s); };

  return (
    <div className="min-h-[60vh]" key={animKey}>
      {/* ─── top bar ─── */}
      <div className="mb-6 flex items-center justify-between">
        <Link to="/app" className="inline-flex items-center gap-1.5 text-xs text-muted-foreground transition hover:text-foreground">
          <ArrowLeft className="h-3.5 w-3.5" /> Back to inbox
        </Link>
        {step !== "live" && (
          <div className="flex items-center gap-1.5">
            {userSteps.map((s, i) => (
              <div key={s.key} className="flex items-center gap-1.5">
                <div className={`flex h-6 items-center gap-1 rounded-full px-2.5 text-[10px] font-medium uppercase tracking-widest transition-all duration-500 ${
                  stepIndex(step) >= i
                    ? "text-primary-foreground"
                    : "bg-secondary text-muted-foreground"
                }`} style={stepIndex(step) >= i ? { background: "var(--gradient-warm)" } : undefined}>
                  {stepIndex(step) > i ? <Check className="h-3 w-3" /> : null}
                  <span className="hidden sm:inline">{s.label}</span>
                </div>
                {i < userSteps.length - 1 && <div className={`hidden h-px w-4 sm:block ${stepIndex(step) > i ? "bg-primary" : "bg-border"}`} />}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ─── step content ─── */}

      {/* STEP 1 — Product detail */}
      {step === "detail" && (
        <div className="animate-fade-in-up space-y-6">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
            {/* image */}
            <div className="lg:col-span-2">
              <div className="overflow-hidden rounded-2xl border border-border bg-background shadow-[var(--shadow-soft)] flex items-center justify-center p-4">
                <img src={heroOriginal} alt="Product" className="max-h-[500px] w-auto rotate-90 object-contain shadow-md rounded-lg" />
              </div>
              <p className="mt-4 text-center text-[10px] uppercase tracking-widest text-muted-foreground">Original photo · WhatsApp</p>
            </div>
            {/* details */}
            <div className="space-y-5 lg:col-span-3">
              <div>
                <span className="rounded-full bg-primary/10 px-2.5 py-1 text-[10px] font-medium uppercase tracking-widest text-primary">{PRODUCT.category}</span>
                <h2 className="mt-3 font-display text-3xl tracking-tight text-ink">{PRODUCT.name}</h2>
                <p className="mt-3 text-sm leading-relaxed text-ink-soft">{PRODUCT.description}</p>
              </div>
              {/* sender */}
              <div className="rounded-xl border border-border bg-card p-4">
                <div className="flex items-center gap-3">
                  <div className="grid h-10 w-10 place-items-center rounded-full text-xs font-semibold text-primary-foreground" style={{ background: "var(--gradient-warm)" }}>RS</div>
                  <div>
                    <div className="flex items-center gap-2 text-sm font-medium text-foreground"><User className="h-3.5 w-3.5 text-muted-foreground" />{PRODUCT.sender.name}</div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground"><MapPin className="h-3 w-3" />{PRODUCT.sender.location}</div>
                  </div>
                </div>
              </div>
              {/* materials & dims */}
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg border border-border bg-card p-3">
                  <div className="text-[10px] uppercase tracking-widest text-muted-foreground">Materials</div>
                  <div className="mt-1 text-sm text-foreground">{PRODUCT.materials.join(", ")}</div>
                </div>
                <div className="rounded-lg border border-border bg-card p-3">
                  <div className="text-[10px] uppercase tracking-widest text-muted-foreground">Dimensions</div>
                  <div className="mt-1 text-sm text-foreground">{PRODUCT.dimensions}</div>
                </div>
              </div>
              {/* confidence */}
              <div className="rounded-xl border border-border bg-card p-4">
                <div className="mb-3 flex items-center gap-2 text-xs font-medium text-ink"><Sparkles className="h-4 w-4 text-primary" /> AI Confidence Scores</div>
                <div className="space-y-2.5">
                  {PRODUCT.confidence.map((c) => <ConfidenceBar key={c.label} label={c.label} value={c.value} />)}
                </div>
              </div>
              <button
                onClick={() => goTo("searching")}
                className="group inline-flex w-full items-center justify-center gap-2.5 rounded-xl bg-primary px-6 py-3.5 text-sm font-medium text-primary-foreground shadow-[var(--shadow-soft)] transition hover:opacity-90"
              >
                <Search className="h-4 w-4 transition group-hover:scale-110" />
                Find Marketplace Pricing
                <ChevronRight className="h-4 w-4 transition group-hover:translate-x-1" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* STEP 2a — Searching animation */}
      {step === "searching" && (
        <div className="animate-fade-in-up flex flex-col items-center justify-center py-20">
          <div className="relative">
            <div className="animate-scan-pulse grid h-20 w-20 place-items-center rounded-full bg-primary/10">
              <Search className="h-8 w-8 text-primary" />
            </div>
            <div className="absolute inset-0 animate-ping rounded-full bg-primary/10" style={{ animationDuration: "2s" }} />
          </div>
          <h2 className="mt-8 font-display text-2xl text-ink">Scanning marketplaces</h2>
          <p className="mt-2 text-sm text-muted-foreground">Checking prices, fees, and fit across platforms…</p>
          <div className="mt-8 grid grid-cols-2 gap-3 md:grid-cols-4">
            {MARKETPLACES.map((mp, i) => (
              <div key={mp.name} className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-xs transition-all duration-500 ${
                i < cardsRevealed
                  ? "border-primary/30 bg-primary/5 text-primary"
                  : "border-border bg-card text-muted-foreground"
              }`}>
                {i < cardsRevealed ? <Check className="h-3.5 w-3.5" /> : <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                {mp.name}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* STEP 2b — Marketplace pricing cards */}
      {step === "pricing" && (
        <div className="animate-fade-in-up space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-display text-2xl text-ink">Marketplace pricing</h2>
              <p className="mt-1 text-xs text-muted-foreground">Hover on any card to see detailed fit analysis</p>
            </div>
            <span className="rounded-full bg-emerald-500/10 px-2.5 py-1 text-[10px] font-medium uppercase tracking-widest text-emerald-700">4 matches found</span>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            {MARKETPLACES.map((mp, i) => (
              <div
                key={mp.name}
                className="group relative overflow-hidden rounded-2xl border border-border bg-card shadow-[var(--shadow-soft)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[var(--shadow-lift)]"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <div className="absolute -right-8 -top-8 h-24 w-24 rounded-full bg-primary/5 transition group-hover:bg-primary/10" />
                <div className="relative p-5">
                  <div className="flex items-center justify-between">
                    <span className="text-2xl">{mp.emoji}</span>
                    <div className="flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
                      <Star className="h-3 w-3" /> {mp.fit}% fit
                    </div>
                  </div>
                  <h3 className="mt-3 font-display text-lg text-ink">{mp.name}</h3>
                  <div className="mt-1 flex items-baseline gap-1">
                    <span className="font-display text-3xl text-foreground">{mp.currency}{mp.price.toLocaleString("en-IN")}</span>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{mp.category}</p>
                  {/* expanded details on hover */}
                  <div className="mt-0 max-h-0 overflow-hidden opacity-0 transition-all duration-400 ease-in-out group-hover:mt-4 group-hover:max-h-64 group-hover:opacity-100">
                    <div className="space-y-2.5 border-t border-border pt-3">
                      <div className="flex items-center gap-2 text-xs"><BadgePercent className="h-3.5 w-3.5 text-primary" /><span className="text-muted-foreground">Fees:</span><span className="text-foreground">{mp.fees}</span></div>
                      <div className="flex items-center gap-2 text-xs"><Truck className="h-3.5 w-3.5 text-primary" /><span className="text-muted-foreground">Delivery:</span><span className="text-foreground">{mp.delivery}</span></div>
                      <div className="flex items-center gap-2 text-xs"><Users className="h-3.5 w-3.5 text-primary" /><span className="text-muted-foreground">Audience:</span><span className="text-foreground">{mp.audience}</span></div>
                      <p className="text-xs leading-relaxed text-ink-soft">{mp.desc}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="flex justify-center">
            <button onClick={() => goTo("optimum")} className="group inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-3 text-sm font-medium text-primary-foreground shadow-[var(--shadow-soft)] transition hover:opacity-90">
              <TrendingUp className="h-4 w-4" /> Show Recommended Price <ChevronRight className="h-4 w-4 transition group-hover:translate-x-1" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3 — Optimum price */}
      {step === "optimum" && (
        <div className="animate-fade-in-up flex flex-col items-center py-16">
          <span className="text-xs uppercase tracking-[0.25em] text-primary">AI-recommended price</span>
          <h2 className="mt-3 font-display text-2xl text-ink">Based on market analysis across 4 platforms</h2>
          <div className="relative mt-10">
            {priceCounter >= 950 && (
              <>
                <div className="absolute inset-0 rounded-full" style={{ animation: "celebrate-ring 1.5s ease-out forwards", border: "2px solid var(--primary)" }} />
                <div className="absolute inset-0 rounded-full" style={{ animation: "celebrate-ring 1.5s ease-out 0.2s forwards", border: "2px solid var(--accent)" }} />
              </>
            )}
            <div className="relative grid h-40 w-40 place-items-center rounded-full border-2 border-primary/20 bg-card shadow-[var(--shadow-lift)]">
              <div className="text-center">
                <div className="flex items-center justify-center gap-1 font-display text-5xl text-primary">
                  <IndianRupee className="h-8 w-8" />
                  {priceCounter.toLocaleString("en-IN")}
                </div>
                <div className="mt-1 text-[10px] uppercase tracking-widest text-muted-foreground">Optimum</div>
              </div>
            </div>
          </div>
          <div className="mt-8 grid grid-cols-3 gap-6 text-center">
            <div><div className="text-xs text-muted-foreground">Floor</div><div className="font-display text-lg text-foreground">₹650</div></div>
            <div><div className="text-xs text-muted-foreground">Recommended</div><div className="font-display text-lg text-primary">₹950</div></div>
            <div><div className="text-xs text-muted-foreground">Ceiling</div><div className="font-display text-lg text-foreground">₹1,300</div></div>
          </div>
          {priceCounter >= 950 && !priceConfirmed && (
            <div className="mt-10 animate-fade-in-up text-center">
              <p className="text-sm text-ink-soft">Is this price okay for your listing?</p>
              <div className="mt-4 flex items-center justify-center gap-3">
                <button onClick={() => { setPriceConfirmed(true); setTimeout(() => goTo("catalog"), 600); }} className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-medium text-primary-foreground shadow-[var(--shadow-soft)] transition hover:opacity-90">
                  <Check className="h-4 w-4" /> Looks good
                </button>
                <button className="inline-flex items-center gap-2 rounded-xl border border-border bg-card px-5 py-3 text-sm font-medium text-foreground transition hover:bg-secondary">
                  <Edit3 className="h-4 w-4" /> Edit price
                </button>
              </div>
            </div>
          )}
          {priceConfirmed && (
            <div className="mt-8 animate-bounce-check text-center">
              <CircleCheck className="mx-auto h-10 w-10 text-emerald-500" />
              <p className="mt-2 text-sm font-medium text-emerald-700">Price confirmed!</p>
            </div>
          )}
        </div>
      )}

      {/* STEP 4 — Catalog editor */}
      {step === "catalog" && (
        <div className="animate-fade-in-up space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-display text-2xl text-ink">Create your catalog</h2>
              <p className="mt-1 text-xs text-muted-foreground">Select images, refine details, and choose where to publish</p>
            </div>
            {isGenerating && (
              <div className="flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-[10px] font-medium uppercase tracking-widest text-primary">
                <Sparkles className="h-3 w-3 animate-pulse" /> AI is generating assets...
              </div>
            )}
            {!isGenerating && <span className="rounded-full bg-primary/10 px-2.5 py-1 text-[10px] font-medium uppercase tracking-widest text-primary">Draft</span>}
          </div>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            {/* AI images */}
            <div className="space-y-4 lg:col-span-5">
              <div className="rounded-xl border border-border bg-card p-4">
                <div className="mb-3 flex items-center gap-2 text-xs font-medium text-ink">
                  <Camera className="h-4 w-4 text-primary" /> 
                  AI-Generated Images 
                  {isGenerating ? <span className="text-muted-foreground animate-pulse ml-1">— {GEN_SUBSTEPS[genSubStep]}</span> : <span className="text-muted-foreground ml-1">— select multiple</span>}
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {AI_IMAGES.map((img, i) => (
                    <button
                      key={i}
                      disabled={isGenerating}
                      onClick={() => setSelectedImages((prev) => {
                        const next = new Set(prev);
                        if (next.has(i)) {
                          if (next.size > 1) next.delete(i);
                        } else {
                          next.add(i);
                        }
                        return next;
                      })}
                      className={`group relative aspect-square overflow-hidden rounded-xl border-2 transition-all duration-300 ${
                        selectedImages.has(i) && !isGenerating
                          ? "border-primary shadow-[var(--shadow-soft)] scale-[1.02]"
                          : "border-border hover:border-primary/40"
                      } ${isGenerating ? "cursor-wait" : ""}`}
                    >
                      {/* Generation Animation Layer */}
                      {isGenerating && (
                        <div className="absolute inset-0 z-10 overflow-hidden bg-background">
                          <div className={`absolute inset-0 bg-gradient-to-br ${img.bg} opacity-20`} />
                          {/* Noise/Blur placeholder */}
                          <div className="absolute inset-0 grid place-items-center opacity-30">
                            <Sparkles className="h-8 w-8 text-muted-foreground animate-pulse" />
                          </div>
                          {/* Scan line */}
                          <div className="absolute left-0 right-0 h-1 bg-primary/40 blur-sm animate-scan-line shadow-[0_0_15px_var(--primary)]" style={{ animationDelay: `${i * 0.2}s` }} />
                          {/* Status text */}
                          <div className="absolute bottom-2 left-0 right-0 text-center text-[8px] font-medium uppercase tracking-tighter text-muted-foreground animate-pulse">
                            Processing...
                          </div>
                        </div>
                      )}
                      
                      {/* Image Layer */}
                      <div className={`h-full w-full bg-gradient-to-br ${img.bg} ${isGenerating ? "blur-xl scale-110 opacity-50" : "animate-blur-reveal"}`}>
                        <img src={img.img} alt={img.label} className="h-full w-full object-cover mix-blend-multiply opacity-90 transition group-hover:scale-105" />
                      </div>

                      <div className="absolute bottom-0 left-0 right-0 bg-ink/60 px-2 py-1 text-[10px] font-medium text-white backdrop-blur-sm">{img.label}</div>
                      {selectedImages.has(i) && !isGenerating && (
                        <div className="absolute right-1.5 top-1.5 z-20 grid h-5 w-5 place-items-center rounded-full bg-primary text-primary-foreground shadow-sm animate-bounce-check">
                          <Check className="h-3 w-3" />
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
              {/* preview */}
              <div className="rounded-xl border border-border bg-card overflow-hidden">
                <div className="flex bg-secondary/30 p-2 overflow-x-auto gap-2 min-h-40">
                  {isGenerating ? (
                    <div className="flex-1 grid place-items-center text-xs text-muted-foreground gap-3">
                      <Loader2 className="h-6 w-6 animate-spin text-primary" />
                      Preparing your selection...
                    </div>
                  ) : (
                    [...selectedImages].map((idx) => (
                      <div key={idx} className={`relative flex-none h-40 aspect-video rounded-lg overflow-hidden bg-gradient-to-br ${AI_IMAGES[idx].bg} animate-blur-reveal`}>
                        <img src={AI_IMAGES[idx].img} alt="Preview" className="h-full w-full object-cover mix-blend-multiply opacity-90" />
                      </div>
                    ))
                  )}
                </div>
                {!isGenerating && <div className="p-3 text-center text-xs text-muted-foreground">{selectedImages.size} images selected</div>}
              </div>
            </div>

            {/* editable form */}
            <div className="space-y-4 lg:col-span-7">
              <div className="rounded-xl border border-border bg-card p-5">
                <div className="mb-4 flex items-center gap-2 text-xs font-medium text-ink"><Layers className="h-4 w-4 text-primary" /> Listing Details</div>
                {/* title */}
                <div className="space-y-3">
                  <div>
                    <div className="flex items-center justify-between">
                      <label className="text-[10px] uppercase tracking-widest text-muted-foreground">Title</label>
                      <button onClick={() => setEditingField(editingField === "title" ? null : "title")} className="text-xs text-primary hover:underline"><Edit3 className="inline h-3 w-3" /> {editingField === "title" ? "Done" : "Edit"}</button>
                    </div>
                    {editingField === "title"
                      ? <input value={catalogTitle} onChange={(e) => setCatalogTitle(e.target.value)} className="mt-1 w-full rounded-lg border border-primary/30 bg-background px-3 py-2 text-sm text-foreground outline-none focus:ring-2 focus:ring-primary/20" />
                      : <p className="mt-1 text-sm font-medium text-foreground">{catalogTitle}</p>
                    }
                  </div>
                  {/* description */}
                  <div>
                    <div className="flex items-center justify-between">
                      <label className="text-[10px] uppercase tracking-widest text-muted-foreground">Description</label>
                      <button onClick={() => setEditingField(editingField === "desc" ? null : "desc")} className="text-xs text-primary hover:underline"><Edit3 className="inline h-3 w-3" /> {editingField === "desc" ? "Done" : "Edit"}</button>
                    </div>
                    {editingField === "desc"
                      ? <textarea value={catalogDesc} onChange={(e) => setCatalogDesc(e.target.value)} rows={3} className="mt-1 w-full rounded-lg border border-primary/30 bg-background px-3 py-2 text-sm text-foreground outline-none focus:ring-2 focus:ring-primary/20" />
                      : <p className="mt-1 text-sm text-ink-soft leading-relaxed">{catalogDesc}</p>
                    }
                  </div>
                  {/* attributes grid */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-lg border border-border bg-background p-3"><div className="text-[10px] uppercase tracking-widest text-muted-foreground">Category</div><div className="mt-0.5 text-sm text-foreground">{PRODUCT.category}</div></div>
                    <div className="rounded-lg border border-border bg-background p-3"><div className="text-[10px] uppercase tracking-widest text-muted-foreground">Materials</div><div className="mt-0.5 text-sm text-foreground">{PRODUCT.materials.join(", ")}</div></div>
                    <div className="rounded-lg border border-border bg-background p-3"><div className="text-[10px] uppercase tracking-widest text-muted-foreground">Dimensions</div><div className="mt-0.5 text-sm text-foreground">{PRODUCT.dimensions}</div></div>
                    <div className="rounded-lg border border-border bg-background p-3">
                      <div className="text-[10px] uppercase tracking-widest text-muted-foreground">Price</div>
                      <div className="mt-0.5 flex items-center gap-1 font-display text-lg text-primary"><IndianRupee className="h-3.5 w-3.5" />950</div>
                    </div>
                  </div>
                </div>
              </div>
              {/* marketplace selection */}
              <div className="rounded-xl border border-border bg-card p-5">
                <div className="mb-4 flex items-center gap-2 text-xs font-medium text-ink"><ShoppingBag className="h-4 w-4 text-primary" /> Select Marketplaces</div>
                <div className="space-y-2">
                  {MARKETPLACES.map((mp, i) => (
                    <button
                      key={mp.name}
                      onClick={() => setSelectedMarketplaces((prev) => { const n = new Set(prev); n.has(i) ? n.delete(i) : n.add(i); return n; })}
                      className={`flex w-full items-center gap-3 rounded-lg border px-4 py-3 text-left transition ${
                        selectedMarketplaces.has(i)
                          ? "border-primary bg-primary/5"
                          : "border-border bg-background hover:border-primary/30"
                      }`}
                    >
                      <div className={`grid h-5 w-5 place-items-center rounded border transition ${
                        selectedMarketplaces.has(i) ? "border-primary bg-primary text-primary-foreground" : "border-border"
                      }`}>
                        {selectedMarketplaces.has(i) && <Check className="h-3 w-3" />}
                      </div>
                      <span className="text-lg">{mp.emoji}</span>
                      <div className="flex-1">
                        <div className="text-sm font-medium text-foreground">{mp.name}</div>
                        <div className="text-xs text-muted-foreground">{mp.currency}{mp.price.toLocaleString("en-IN")} · {mp.fees}</div>
                      </div>
                      <div className="rounded-full bg-secondary px-2 py-0.5 text-[10px] font-medium text-foreground">{mp.fit}% fit</div>
                    </button>
                  ))}
                </div>
              </div>
              {/* publish button */}
              <button
                disabled={selectedMarketplaces.size === 0}
                onClick={() => goTo("publishing")}
                className="group inline-flex w-full items-center justify-center gap-2.5 rounded-xl bg-primary px-6 py-3.5 text-sm font-medium text-primary-foreground shadow-[var(--shadow-soft)] transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Send className="h-4 w-4 transition group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
                Publish to {selectedMarketplaces.size} marketplace{selectedMarketplaces.size !== 1 ? "s" : ""}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* STEP 5a — Publishing progress */}
      {step === "publishing" && (
        <div className="animate-fade-in-up flex flex-col items-center justify-center py-20">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
          <h2 className="mt-6 font-display text-2xl text-ink">Publishing your listing</h2>
          <p className="mt-2 text-sm text-muted-foreground">Connecting to {publishingMp}…</p>
          <div className="mt-8 w-full max-w-md">
            <div className="h-3 w-full overflow-hidden rounded-full bg-secondary">
              <div className="h-full rounded-full transition-all duration-300" style={{ width: `${publishProgress}%`, background: "var(--gradient-warm)" }} />
            </div>
            <div className="mt-2 flex justify-between text-xs text-muted-foreground">
              <span>{publishingMp}</span>
              <span>{Math.round(publishProgress)}%</span>
            </div>
          </div>
          <div className="mt-6 flex flex-wrap justify-center gap-2">
            {[...selectedMarketplaces].map((i) => {
              const done = publishProgress >= ((Array.from(selectedMarketplaces).indexOf(i) + 1) / selectedMarketplaces.size) * 100;
              return (
                <span key={i} className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition ${done ? "bg-emerald-500/10 text-emerald-700" : "bg-secondary text-muted-foreground"}`}>
                  {done ? <Check className="h-3 w-3" /> : <Loader2 className="h-3 w-3 animate-spin" />} {MARKETPLACES[i].name}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* STEP 5b — Live! 🎉 */}
      {step === "live" && (
        <div className="flex flex-col items-center justify-center py-16">
          {/* celebration particles */}
          <div className="pointer-events-none absolute inset-0 overflow-hidden">
            {Array.from({ length: 20 }).map((_, i) => (
              <div
                key={i}
                className="absolute rounded-full"
                style={{
                  width: `${Math.random() * 8 + 4}px`,
                  height: `${Math.random() * 8 + 4}px`,
                  left: `${Math.random() * 100}%`,
                  top: `${Math.random() * 40 + 10}%`,
                  background: ["var(--primary)", "var(--accent)", "#e96d36", "#f5b642", "#3b82f6"][i % 5],
                  animation: `float-up ${Math.random() * 2 + 1.5}s ease-out ${Math.random() * 0.5}s forwards`,
                }}
              />
            ))}
          </div>
          {/* main content */}
          <div className="relative">
            <div className="absolute inset-0 rounded-full" style={{ animation: "celebrate-ring 1.5s ease-out forwards", border: "3px solid var(--primary)" }} />
            <div className="absolute inset-0 rounded-full" style={{ animation: "celebrate-ring 1.5s ease-out 0.3s forwards", border: "3px solid var(--accent)" }} />
            <div className="relative animate-bounce-check grid h-24 w-24 place-items-center rounded-full bg-emerald-500 text-white shadow-[var(--shadow-lift)]">
              <Check className="h-12 w-12" />
            </div>
          </div>
          <h2 className="mt-8 font-display text-4xl text-ink">Your item is LIVE! 🎉</h2>
          <p className="mt-3 max-w-md text-center text-sm text-ink-soft">
            Your <strong>{PRODUCT.name}</strong> has been published successfully across {selectedMarketplaces.size} marketplace{selectedMarketplaces.size !== 1 ? "s" : ""}.
          </p>
          <div className="mt-8 space-y-2">
            {[...selectedMarketplaces].map((i) => (
              <div key={i} className="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-5 py-3">
                <CircleCheck className="h-5 w-5 text-emerald-600" />
                <span className="text-lg">{MARKETPLACES[i].emoji}</span>
                <span className="font-medium text-foreground">{MARKETPLACES[i].name}</span>
                <span className="ml-auto text-xs text-emerald-600">● Live</span>
              </div>
            ))}
          </div>
          <div className="mt-10 flex gap-3">
            <Link to="/app" className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-medium text-primary-foreground shadow-[var(--shadow-soft)] transition hover:opacity-90">
              <Package className="h-4 w-4" /> Back to Inbox
            </Link>
            <button onClick={() => goTo("detail")} className="inline-flex items-center gap-2 rounded-xl border border-border bg-card px-5 py-3 text-sm font-medium text-foreground transition hover:bg-secondary">
              <Eye className="h-4 w-4" /> View Listing
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
