<div align="center">

<br/>

<pre>
███╗   ███╗██╗██╗  ██╗
████╗ ████║██║██║  ██║
██╔████╔██║██║███████║
██║╚██╔╝██║██║██╔══██║
██║ ╚═╝ ██║██║██║  ██║
╚═╝     ╚═╝╚═╝╚═╝  ╚═╝
</pre>

### **Market Intelligence Hub**
*Autonomous competitive awareness — from signal to strategy.*

<br/>

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Architecture](https://img.shields.io/badge/Architecture-Agentic-6C3483?style=flat-square&logo=buffer&logoColor=white)
![Targets](https://img.shields.io/badge/Targets-Vercel%20·%20Netlify%20·%20Cloudflare-00C7B7?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-F0B429?style=flat-square)
![Status](https://img.shields.io/badge/Status-MVP-2ECC71?style=flat-square)

<br/>

> ⚠️ **Public Architectural Showcase** — Core agent patterns and representative implementations are open. Production infrastructure, specialized modules, and proprietary logic are maintained internally.

<br/>

**[Overview](#-overview) • [Architecture](#-architecture) • [Design Decisions](#%EF%B8%8F-design-decisions) • [MVP Scope](#-mvp-scope) • [Getting Started](#-getting-started)**

</div>

---

## 🔭 Overview

**Competitive advantage has a time constant.** A competitor's pricing change on Monday requires a response by Tuesday — not Friday.

Manual monitoring breaks down because it is neither continuous nor contextual. Generic scrapers detect change but cannot interpret it. Analyst teams provide context but cannot scale. The gap between *detection* and *decision-ready intelligence* is where strategic opportunity is lost.

```
Traditional Flow              Our Flow
──────────────────────        ──────────────────────────────
Scrape → Diff → Alert         Observe → Interpret → Act
      ↑ hours/days                    ↑ minutes
```

---

## 🏗 Architecture

MIH is built on a **modular agent pattern** — three agents, each owning a single responsibility, each independently upgradeable.

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   ┌──────────┐      ┌──────────┐      ┌──────────────────┐   │
│   │  WATCHER │─────▶│ ANALYST  │─────▶│    REPORTER      │   │
│   │          │      │          │      │                  │   │
│   │Structured│      │ Δ-detect │      │ LLM synthesis    │   │
│   │ingestion │      │ >5% flag │      │ → Markdown/Email │   │
│   └──────────┘      └──────────┘      └──────────────────┘   │
│                                                              │
│   🎯  Vercel · Netlify · Cloudflare                          │
└──────────────────────────────────────────────────────────────┘
```

### 👁️ `WatcherAgent` — Field Observer

Isolates live-web complexity from analysis logic. Executes structured extraction of pricing tiers, feature limits, and plan configurations. Implements circuit-breaker patterns and exponential backoff. Outputs clean, timestamped snapshots — nothing more.

### 🧠 `AnalystAgent` — Change Detector

Compares snapshots with deterministic logic. Flags meaningful variance (price shifts, tier restructuring, feature additions/removals). Does not hallucinate; does not guess. Passes structured signals downstream.

### 📡 `ReporterAgent` — Intelligence Synthesizer

Receives flagged changes. Uses LLM reasoning to contextualize the signal — *what changed, why it matters, what it likely signals.* Outputs executive-grade briefs in minutes, not hours.

---

## ⚙️ Design Decisions

### Why Agents, Not a Pipeline?

A linear `scrape → compare → alert` script is brittle. Upgrading analysis logic requires touching data collection. Failures cascade.

The agentic approach provides:

- 🔒 **Failure isolation** — Reporter email failure doesn't affect Analyst processing
- 🔄 **Independent upgrades** — swap `if price_change > 5%: flag()` for multi-source LLM reasoning without rewriting ingestion
- 🤝 **Clear interfaces** — each agent exposes a stable contract; internals evolve freely

### 🔇 Communication Philosophy

The system follows a *"silent guardian, vocal advisor"* model:

- Monitors continuously without requiring attention
- Surfaces insights through scheduled digests
- Interrupts only on time-sensitive signals

### 🛡️ Data Ethics

- Public pricing pages only — no authenticated sessions, no PII
- Respects `robots.txt` and rate limits
- Outputs business metrics only — no raw HTML stored
- Full audit trail with timestamps

---

## 🎯 MVP Scope

| Dimension | Implementation |
|-----------|---------------|
| 🌐 Monitored targets | Vercel, Netlify, Cloudflare |
| 📡 Detected signals | Pricing & tier changes |
| 🔬 Detection logic | Deterministic threshold-based |
| 🧠 Synthesis | LLM-powered strategic context |
| 📄 Output formats | Markdown report, Email alert |

**Why cloud hosting?** Pricing here is rarely arbitrary — edge compute limits, tier restructuring, and feature gating are often competitive responses. This makes it an ideal testbed: changes are meaningful, correlated, and fast-moving.

---

## 🚀 Getting Started

```bash
git clone https://github.com/your-org/market-intelligence-hub.git
cd market-intelligence-hub
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
python run.py
```

---

## 🔮 Roadmap

The current deterministic agents are architectural scaffolding. The interfaces are stable; the intelligence evolves.

```
Now    →  if price_change > threshold: flag()
Near   →  pattern recognition across historical snapshots
Later  →  predictive modeling, scenario-based recommendations
```

---

<div align="center">

<br/>

*Intelligence is not about having more data.*
*It's about understanding change before anyone else does.*

<br/>

</div>
