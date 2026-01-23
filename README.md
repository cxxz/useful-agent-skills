# useful-agent-skills

A collection of reusable AI agent skills for web research and information gathering.

## Skills

| Skill | Description |
|-------|-------------|
| [web-search](skills/web-search/) | Iterative web research via Google search + webpage scraping |
| [deep-research](skills/deep-research/) | Autonomous multi-step research using Gemini Deep Research Agent |

## Quick Start

### Web Search
```bash
# Set up environment
cp skills/web-search/.env.sample skills/web-search/.env
# Edit .env with your API keys (BRIGHTDATA_API_TOKEN, JINA_API_KEY, SUMMARY_LLM_API_KEY)

# Search Google
python skills/web-search/scripts/google_search.py -q "your search query"

# Read a webpage
python skills/web-search/scripts/read_webpage.py --url "https://example.com"
```

### Deep Research
```bash
# Set up environment
cd skills/deep-research
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# Run research (takes 2-10 minutes)
python scripts/research.py -q "Research topic"
```
