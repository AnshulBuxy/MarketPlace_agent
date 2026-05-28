# Banao: End-to-End System Blueprint & Roadmap

Banao is an AI-powered orchestration platform designed to bridge the gap between Indian artisans and global digital marketplaces. It automates the complex process of catalog creation, pricing, and multi-channel listing.

---

## 🛠️ Current Architecture (Phase 1: Intelligent Onboarding)

### 1. The Artisan Side (WhatsApp Bot)
- **Feature**: Direct product onboarding via WhatsApp messages.
- **Agents Involved**: 
    - **Ingestion Agent**: Receives and stores images/voice notes in S3/PostgreSQL.
    - **Extraction Agent**: Uses multimodal AI to identify the product, material, and category from raw inputs.
    - **Conversational Agent**: Asks follow-up questions to fill in missing details (size, weight, story).

### 2. The Operator Side (Admin Dashboard)
- **Feature**: A high-end workspace for market experts to verify and polish listings.
- **Key Modules**:
    - **Catalog Wizard**: A 5-step flow for refining product attributes and creating premium collateral.
    - **Pricing Intelligence (The Search Agent)**:
        - **eBay Connector**: Provides sandbox-ready marketplace context.
        - **Google Lens Connector**: Global visual matching for unique handcrafted items.
        - **Google Shopping Connector**: Accurate Indian regional pricing (Flipkart, Meesho, Ajio).
    - **Pricing Agent**: A master agent that aggregates all marketplace data and suggests an optimal price in INR.

---

## 🚀 Future Roadmap (Phase 2 & 3: Creative & Global)

### 1. Creative Master (AI Media Suite)
- **Goal**: Transform a mobile photo into a professional studio shot or video.
- **Agents**: **Creative Agent** will handle AI background removal, "in-painting" for lifestyle shots, and short promotional video generation with retry/edit controls for the operator.

### 2. The Multi-Channel Publisher (One-Click Live)
- **Goal**: Instantly list the finalized product across marketplaces.
- **Targets**: Amazon SP-API, Etsy API, eBay Production, and Shopify.
- **Workflow**: Automated formatting of descriptions to match each platform's specific SEO requirements.

### 3. Custom Voice Experience (TTS/STT)
- **Goal**: Localized communication for artisans in multiple Indian languages.
- **STT (Speech-to-Text) Use Cases**:
    - **Voice Onboarding**: Artisans send WhatsApp voice notes describing their craft (e.g., "Handmade brass elephant from Moradabad"), which the AI transcribes and parses into catalog details.
- **TTS (Text-to-Speech) Use Cases**:
    - **Automated Status Updates**: Sending voice notes to artisans confirming "Your product is now live on Amazon India!"
    - **Accessibility**: Reading out marketplace feedback or pricing suggestions to artisans with limited literacy.

### 4. Artisan Micro-Websites (Optional Add-on)
- **Goal**: Automated generation of a simple, beautiful landing page for each product.
- **Feature**: Basic "Contact Seller" functionality allowing direct buyer-to-artisan connection without middleman complexity.

---


