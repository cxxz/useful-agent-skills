# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of AI agent skills - reusable research capabilities that can be invoked via CLI scripts. Each skill is self-contained in its own directory under `skills/`.

## Skills

### web-search
Iterative web research combining Google search and webpage scraping.

**Dependencies:** `brightdata-sdk`, `httpx`, `openai`, `python-dotenv` (optional)

**Environment variables (in `.env`):**
- `BRIGHTDATA_API_TOKEN` - For Google search via BrightData
- `JINA_API_KEY` - For webpage content fetching via Jina Reader
- `SUMMARY_LLM_API_KEY` - For generating webpage summaries (uses Cerebras by default)

**Scripts:**
```bash
# Google search
python skills/web-search/scripts/google_search.py --query "search terms"

# Read webpage (summary by default)
python skills/web-search/scripts/read_webpage.py --url "https://example.com"

# Read full content
python skills/web-search/scripts/read_webpage.py --url "https://example.com" --full-content
```

Search results and webpage content are cached in `webcache/` (relative to script).

### deep-research
Autonomous multi-step research using Google Gemini Deep Research Agent.

**Dependencies:** `httpx`, `python-dotenv` (optional)

**Setup:**
```bash
cd skills/deep-research
pip install -r requirements.txt
export GEMINI_API_KEY=your-key
```

**Scripts:**
```bash
# Basic research (takes 2-10 minutes)
python skills/deep-research/scripts/research.py --query "Research topic"

# Stream progress
python skills/deep-research/scripts/research.py --query "Topic" --stream

# Start without waiting
python skills/deep-research/scripts/research.py --query "Topic" --no-wait

# Check status
python skills/deep-research/scripts/research.py --status <interaction_id>

# Continue previous research
python skills/deep-research/scripts/research.py --query "Follow-up" --continue <interaction_id>
```

Research history is cached in `~/.cache/deep-research/`.

## Architecture

Each skill follows this structure:
```
skills/<skill-name>/
├── SKILL.md           # Skill metadata and usage instructions (YAML frontmatter + markdown)
├── README.md          # Detailed documentation (optional)
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
└── scripts/           # Executable CLI scripts
```

The `SKILL.md` frontmatter contains:
- `name`: Skill identifier
- `description`: When to trigger this skill

## Exit Codes

All scripts use consistent exit codes:
- `0`: Success
- `1`: Error (API error, config issue, timeout)
- `130`: Cancelled by user (Ctrl+C)
