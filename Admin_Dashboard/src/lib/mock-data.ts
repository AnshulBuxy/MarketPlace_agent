import type { LucideIcon } from "lucide-react";
import { Mic, Brain, Workflow, Tag, Boxes, Send } from "lucide-react";

export type Marketplace = "Amazon Karigar" | "Etsy" | "Flipkart Samarth" | "Jaypore" | "Okhai" | "Meesho";
export type SubmissionStatus = "intake" | "understanding" | "routing" | "pricing" | "drafting" | "review" | "published" | "rejected";
export type Language = "Hindi" | "Maithili" | "Tamil" | "Bengali" | "Kannada" | "Marathi" | "Bhojpuri";

export interface Artisan {
  id: string;
  name: string;
  cluster: string;
  craft: string;
  language: Language;
  phone: string;
  joined: string;
  listings: number;
  earnings: number;
}

export interface AgentLog {
  agent: string;
  ts: string;
  message: string;
  confidence?: number;
}

export interface DraftListing {
  marketplace: Marketplace;
  title: string;
  bullets: string[];
  attributes: Record<string, string>;
  price: number;
  url?: string;
}

export interface Submission {
  id: string;
  artisanId: string;
  receivedAt: string;
  status: SubmissionStatus;
  thumbnail: string;
  voiceTranscript: string;
  voiceLang: Language;
  craft: string;
  materials: string[];
  dimensions: string;
  motifs: string[];
  confidence: number;
  suggestedPrice: { floor: number; mid: number; ceiling: number };
  routedTo: Marketplace[];
  drafts: DraftListing[];
  logs: AgentLog[];
}

export const AGENTS: { key: string; name: string; icon: LucideIcon; status: "healthy" | "degraded"; throughput: number; p50: number }[] = [
  { key: "intake", name: "Intake Agent", icon: Mic, status: "healthy", throughput: 412, p50: 1.2 },
  { key: "understanding", name: "Product Understanding", icon: Brain, status: "healthy", throughput: 408, p50: 3.4 },
  { key: "routing", name: "Marketplace Routing", icon: Workflow, status: "healthy", throughput: 405, p50: 0.6 },
  { key: "pricing", name: "Pricing Intelligence", icon: Tag, status: "degraded", throughput: 398, p50: 2.1 },
  { key: "catalog", name: "Catalog Generation", icon: Boxes, status: "healthy", throughput: 392, p50: 5.8 },
  { key: "publishing", name: "Publishing & Notify", icon: Send, status: "healthy", throughput: 387, p50: 4.2 },
];

export const ARTISANS: Artisan[] = [
  { id: "a-001", name: "Sita Devi", cluster: "Madhubani, Bihar", craft: "Madhubani painting", language: "Maithili", phone: "+91 98••• 12034", joined: "2026-01-12", listings: 14, earnings: 38450 },
  { id: "a-002", name: "Rajesh Kumar", cluster: "Channapatna, Karnataka", craft: "Lacquer toys", language: "Kannada", phone: "+91 97••• 88210", joined: "2026-02-04", listings: 9, earnings: 22100 },
  { id: "a-003", name: "Fatima Begum", cluster: "Varanasi, UP", craft: "Banarasi weaving", language: "Hindi", phone: "+91 96••• 54421", joined: "2025-11-22", listings: 22, earnings: 91200 },
  { id: "a-004", name: "Meera Iyer", cluster: "Kanchipuram, TN", craft: "Silk saree", language: "Tamil", phone: "+91 99••• 11290", joined: "2026-03-01", listings: 6, earnings: 54000 },
  { id: "a-005", name: "Anjali Das", cluster: "Shantiniketan, WB", craft: "Kantha embroidery", language: "Bengali", phone: "+91 98••• 77621", joined: "2026-02-19", listings: 11, earnings: 19800 },
  { id: "a-006", name: "Kavita Patil", cluster: "Paithan, Maharashtra", craft: "Paithani saree", language: "Marathi", phone: "+91 95••• 33012", joined: "2026-01-30", listings: 8, earnings: 47200 },
];

export const SUBMISSIONS: Submission[] = [
  {
    id: "s-1042",
    artisanId: "a-001",
    receivedAt: "2026-05-04T09:12:00Z",
    status: "review",
    thumbnail: "🎨",
    voiceTranscript: "Yeh Madhubani painting hai, mछली aur kamal ka design. Handmade paper par natural rang use kiya hai. Size ek foot ka hai.",
    voiceLang: "Maithili",
    craft: "Madhubani painting",
    materials: ["Handmade paper", "Natural pigments", "Bamboo pen"],
    dimensions: "30 × 30 cm",
    motifs: ["Fish", "Lotus", "Bharni style"],
    confidence: 0.92,
    suggestedPrice: { floor: 1800, mid: 2450, ceiling: 3200 },
    routedTo: ["Amazon Karigar", "Etsy", "Jaypore"],
    drafts: [
      {
        marketplace: "Amazon Karigar",
        title: "Handpainted Madhubani Fish & Lotus Wall Art — 30cm Bharni Style",
        bullets: ["100% handmade on natural handmade paper", "Traditional Bharni technique with natural pigments", "Signed by artisan from Madhubani cluster", "Frame-ready, 30 × 30 cm"],
        attributes: { Material: "Handmade paper", Technique: "Bharni Madhubani", Origin: "Madhubani, Bihar (GI region)", Color: "Earth tones" },
        price: 2450,
      },
      {
        marketplace: "Etsy",
        title: "Madhubani Fish & Lotus Painting · Folk Art India · Handmade Bharni Bihar",
        bullets: ["Traditional Bharni style folk painting", "Natural plant-based pigments", "From a women-led co-op in Bihar"],
        attributes: { Material: "Handmade paper", Style: "Bharni / Madhubani", Region: "Bihar, India" },
        price: 32,
      },
      {
        marketplace: "Jaypore",
        title: "Madhubani Bharni — Fish & Lotus (30cm)",
        bullets: ["Heritage Mithila craft", "Natural pigments, handmade paper", "Artisan: Sita Devi, Madhubani"],
        attributes: { Origin: "Madhubani", Technique: "Bharni" },
        price: 2650,
      },
    ],
    logs: [
      { agent: "Intake", ts: "09:12:04", message: "Photo + 22s voice note received from +91 98••• 12034" },
      { agent: "Intake", ts: "09:12:09", message: "Transcribed Maithili → English (conf 0.94)" },
      { agent: "Understanding", ts: "09:12:18", message: "Classified: Madhubani · Bharni · 30cm (conf 0.92)", confidence: 0.92 },
      { agent: "Routing", ts: "09:12:21", message: "Routed to Amazon Karigar, Etsy, Jaypore" },
      { agent: "Pricing", ts: "09:12:26", message: "Suggested ₹2,450 (band ₹1,800–₹3,200) using 14 comparables" },
      { agent: "Catalog", ts: "09:12:48", message: "Generated 3 platform-native drafts" },
      { agent: "Catalog", ts: "09:12:49", message: "Awaiting district admin review" },
    ],
  },
  {
    id: "s-1041",
    artisanId: "a-002",
    receivedAt: "2026-05-04T08:48:00Z",
    status: "drafting",
    thumbnail: "🪆",
    voiceTranscript: "Channapatna ke khilone hain, lacquer wood se bana hai. Bachhon ke liye safe hai. Set of 5.",
    voiceLang: "Kannada",
    craft: "Channapatna lacquer toys",
    materials: ["Hale wood", "Lac dye"],
    dimensions: "Set of 5, 8–12 cm",
    motifs: ["Spinning top", "Stacking rings"],
    confidence: 0.88,
    suggestedPrice: { floor: 850, mid: 1150, ceiling: 1450 },
    routedTo: ["Amazon Karigar", "Flipkart Samarth"],
    drafts: [],
    logs: [
      { agent: "Intake", ts: "08:48:12", message: "3 photos + 14s voice note received" },
      { agent: "Understanding", ts: "08:48:31", message: "Classified: Channapatna toys (conf 0.88)", confidence: 0.88 },
      { agent: "Routing", ts: "08:48:34", message: "Routed to Amazon Karigar, Flipkart Samarth" },
      { agent: "Pricing", ts: "08:48:40", message: "Suggested ₹1,150 (band ₹850–₹1,450)" },
      { agent: "Catalog", ts: "08:48:42", message: "Generating drafts… 2 of 2" },
    ],
  },
  {
    id: "s-1040",
    artisanId: "a-003",
    receivedAt: "2026-05-04T07:31:00Z",
    status: "published",
    thumbnail: "🧵",
    voiceTranscript: "Banarasi silk saree, pure zari work, red color, 6 yard.",
    voiceLang: "Hindi",
    craft: "Banarasi silk saree",
    materials: ["Pure silk", "Zari (gold thread)"],
    dimensions: "5.5m saree + 0.8m blouse",
    motifs: ["Kalga", "Bel"],
    confidence: 0.95,
    suggestedPrice: { floor: 8500, mid: 11200, ceiling: 14800 },
    routedTo: ["Amazon Karigar", "Jaypore", "Okhai"],
    drafts: [
      { marketplace: "Amazon Karigar", title: "Pure Banarasi Silk Saree · Red · Real Zari Kalga Bel", bullets: [], attributes: {}, price: 11200, url: "amazon.in/karigar/banarasi-1040" },
      { marketplace: "Jaypore", title: "Banarasi Kadhua Saree — Red & Gold", bullets: [], attributes: {}, price: 12400, url: "jaypore.com/p/1040" },
      { marketplace: "Okhai", title: "Heritage Banarasi Saree by Fatima Begum", bullets: [], attributes: {}, price: 11800, url: "okhai.org/p/1040" },
    ],
    logs: [
      { agent: "Publishing", ts: "07:33:11", message: "Live on 3 marketplaces · WhatsApp confirmation sent" },
    ],
  },
  {
    id: "s-1039",
    artisanId: "a-005",
    receivedAt: "2026-05-04T07:02:00Z",
    status: "review",
    thumbnail: "🪡",
    voiceTranscript: "Kantha sari, hand-stitched, Shantiniketan style, off-white with red border.",
    voiceLang: "Bengali",
    craft: "Kantha embroidery saree",
    materials: ["Cotton", "Cotton thread"],
    dimensions: "5.5m",
    motifs: ["Floral border", "Running stitch"],
    confidence: 0.81,
    suggestedPrice: { floor: 3200, mid: 4100, ceiling: 5400 },
    routedTo: ["Etsy", "Jaypore"],
    drafts: [
      { marketplace: "Etsy", title: "Hand-stitched Kantha Saree · Shantiniketan · Off-white Red Border", bullets: ["Hand running stitch", "Ethically sourced cotton"], attributes: { Origin: "Shantiniketan, WB" }, price: 55 },
      { marketplace: "Jaypore", title: "Shantiniketan Kantha Saree — Ivory & Red", bullets: ["Hand kantha", "Pure cotton"], attributes: { Origin: "WB" }, price: 4100 },
    ],
    logs: [
      { agent: "Understanding", ts: "07:02:48", message: "Low confidence on motif (0.71). Flagged for admin." },
      { agent: "Catalog", ts: "07:03:21", message: "2 drafts ready · awaiting review" },
    ],
  },
  {
    id: "s-1038",
    artisanId: "a-004",
    receivedAt: "2026-05-04T06:40:00Z",
    status: "intake",
    thumbnail: "🥻",
    voiceTranscript: "(processing voice note in Tamil…)",
    voiceLang: "Tamil",
    craft: "(detecting…)",
    materials: [],
    dimensions: "—",
    motifs: [],
    confidence: 0,
    suggestedPrice: { floor: 0, mid: 0, ceiling: 0 },
    routedTo: [],
    drafts: [],
    logs: [{ agent: "Intake", ts: "06:40:02", message: "Receiving 2 photos + voice note…" }],
  },
  {
    id: "s-1037",
    artisanId: "a-006",
    receivedAt: "2026-05-04T06:11:00Z",
    status: "rejected",
    thumbnail: "🧶",
    voiceTranscript: "Paithani replica machine-made.",
    voiceLang: "Marathi",
    craft: "Paithani (machine)",
    materials: ["Polyester"],
    dimensions: "5.5m",
    motifs: [],
    confidence: 0.74,
    suggestedPrice: { floor: 0, mid: 0, ceiling: 0 },
    routedTo: [],
    drafts: [],
    logs: [
      { agent: "Understanding", ts: "06:11:30", message: "Detected machine-made replica — fails GI authenticity policy" },
      { agent: "Admin", ts: "06:14:02", message: "Rejected by admin · feedback sent on WhatsApp" },
    ],
  },
];

export function getArtisan(id: string) {
  return ARTISANS.find((a) => a.id === id);
}
export function getSubmission(id: string) {
  return SUBMISSIONS.find((s) => s.id === id);
}

export const STATUS_LABEL: Record<SubmissionStatus, string> = {
  intake: "Intake",
  understanding: "Understanding",
  routing: "Routing",
  pricing: "Pricing",
  drafting: "Drafting",
  review: "Awaiting review",
  published: "Published",
  rejected: "Rejected",
};

export const WEEKLY_LISTINGS = [
  { week: "W14", count: 41 },
  { week: "W15", count: 53 },
  { week: "W16", count: 62 },
  { week: "W17", count: 71 },
  { week: "W18", count: 88 },
];