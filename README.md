# NeuroAI Digest

I built this because keeping up with the intersection of Neuroscience and AI is becoming a full-time job in itself. The "firehose" of arXiv preprints, Reddit discussions, and science blogs is mostly noise. This pipeline is an attempt to automate the synthesis of that stream into something actually readable.

### The Problem
Most newsletters are either too broad (generic AI) or too high-level (pop science). I needed something that specifically targets the NeuroAI niche, evaluates technical relevance, and deduplicates the same paper across five different sources.

### How it Works
This isn't just an RSS aggregator. It follows a multi-stage filtering and ranking process:

1.  **Extraction**: Pulls from curated sources like arXiv (cs.NE, q-bio.NC), NeuroStars, Quanta, and specific subreddits.
2.  **Filtering**: Every post is run through a relevance engine (NRS) to ensure it actually pertains to neural computation, biological constraints, or cognitive modeling.
3.  **Ranking**: Scoring is based on:
    *   **Source Weight**: Academic journals and curated blogs (Quanta) outrank social media.
    *   **Engagement**: Reddit upvotes and arXiv cross-listings act as popularity signals.
    *   **Specificity**: Review papers and surveys get a slight boost for better context.
4.  **Synthesis**: An LLM generates concise, technical summaries. No marketing fluff—just the core findings.

### Setup
If you want to run this yourself:

1.  **Dependencies**: `pip install -r requirements.txt`
2.  **Config**: Create a `.env` in the `config/` directory with your `GROQ_API_KEY` (for summaries) and SMTP details.
3.  **Run**: `python main.py` triggers a manual run.

### Why this exists
To get the signal without the doomscrolling. It’s opinionated about what "relevance" means in NeuroAI, which is exactly the point.

---
*Maintained by [Aakif Khan](https://github.com/aakif-khan)*
