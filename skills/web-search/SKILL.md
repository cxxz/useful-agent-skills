---
name: web-search
description:  Iterative web research combining Google search and webpage scraping. Use whenever needing to do web search, i.e. searching current information, research topics, gather sources, or answer questions requiring up-to-date web data. Triggers on queries like "search for...", "find information about...", "what's the latest on...", research questions, or any task requiring web research beyond the knowledge cutoff.
---

# Web Search Guidance

## Workflow Overview
Perform iterative web research by combining Google search with webpage reading—emulating how a human researches topics online. Steps for each research session:
1. **Formulate query** — Transform the user's question into effective search terms
2. **Search** — Run `google_search.py` with your query
3. **Evaluate search results** — Review titles and descriptions for relevance
   - **No relevant results**: Refine your query and return to step 2
   - **Relevant results found**: Proceed to step 4
4. **Read content** — For each promising result, choose one approach:
   - **Summary first** (recommended): Read the summary → if valuable, read the full content
   - **Full content directly**: Use only when the title/description clearly indicates very high relevance, and the user's question will most likely require deep details from the page
5. **Iterate** — Follow leads, search new terms you discover, and gather more sources
6. **Synthesize** — Combine your findings into a coherent answer
7. **Stop** when you gather sufficient information for the user's question OR the turn limit is exhausted

**Turn counting rules:**
- One Google search = one turn
- Reading any number of webpage summaries from a single search = one turn total
- Reading the full content of a webpage = one turn each

**Turn limits:**
- Default maximum: 10 turns
- Extended maximum: 30 turns (when the user requests "deep research," "extensive search," "gather as much information as possible," etc.)

Below is an example workflow with 9 turns:
```
Turn 1: Search the 1st query → Evaluate search results → No relevant pages found
Turn 2: Refine query → Search again → Identify results #1, #3, #6 as relevant
Turn 3: Read summaries of #1, #3, #6 → The Hacker News discussion (#3) is worth a deeper look
Turn 4: Read full content of #3 → Discover new term to research
Turn 5: Search new term → Evaluate search results → Find one paper (#2) and a blog post (#4) that are relevant
Turn 6: Read summaries of #2 and #4 → Both are worth reading in full
Turn 7: Read full content of #2 → Extract key insights relevant to the user's question
Turn 8: Read full content of #4 → Extract complementary insights for the user's question
Turn 9: Decide enough information has been collected → Search complete, synthesize findings into final answer
```

## Scripts

> **Note**: Use absolute paths or ensure correct relative paths when running scripts. With `uv` projects, prefix commands with `uv run`.

### Google Search

Searches Google and caches results with metadata.

```bash
# Basic search
python <skill_folder>/scripts/google_search.py --query "LLM scaling slowing down 2025"

# Domain-specific search
python <skill_folder>/scripts/google_search.py --query "data efficient ai agent training site:arxiv.org"

# Location-aware search (for local/regional results)
python <skill_folder>/scripts/google_search.py --query "Grab vs Shopee growth strategies comparision" --location "Singapore"

# More results
python <skill_folder>/scripts/google_search.py --query "RAG implementation" --num-results 20
```

| Option | Description | Default |
|--------|-------------|---------|
| `--query`, `-q` | Search query (required) | — |
| `--num-results` | Number of results | 10 |
| `--lang` | Language code | `en` |
| `--location` | Geographic location | — |
| `--webcache-folder` | Cache location | `../../../webcache` |

#### Google Search Operators

| Operator | Purpose | Example |
|----------|---------|---------|
| `site:` | Restrict to domain | `site:arxiv.org transformer efficiency` |
| `filetype:` | Filter by file type | `machine learning survey filetype:pdf` |
| `"..."` | Exact phrase match | `"chain of thought prompting"` |
| `-` | Exclude term | `python tutorial -beginner` |
| `OR` | Alternative terms | `LLM OR "large language model"` |
| `intitle:` | Term in page title | `intitle:benchmark GPT-4` |
| `after:` | Results after date | `AI safety after:2025-01-01` |

#### Refinement Strategies

- **Too few results**: Remove constraints, use broader terms, try synonyms
- **Too many irrelevant results**: Add `site:`, use exact phrases, add specific keywords
- **Wrong domain**: Add domain-specific terms (e.g., "arxiv", "github", "documentation")
- **Outdated results**: Add year or use `after:` operator

### Read Webpage

Fetches and caches webpage content. Returns LLM summary by default.

```bash
# Read summary (default, faster for initial evaluation)
python <skill_folder>/scripts/read_webpage.py --url "https://openai.com/index/openai-for-healthcare/"

# Read full content (for detailed analysis)
python <skill_folder>/scripts/read_webpage.py --url "https://arxiv.org/html/2508.02994v1" --full-content
```

| Option | Description | Default |
|--------|-------------|---------|
| `--url` | URL to read (required) | — |
| `--full-content` | Return full content instead of summary | `false` |
