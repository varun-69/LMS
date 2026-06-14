# AI Lead Generation Agent

An autonomous AI agent that finds high-paying clients for digital marketing and web development services. Targets businesses in **US, UK, Australia, and India** across 20+ niches, scores them with Claude AI, and generates personalised cold-outreach emails.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        LeadGenCrew                               │
│                                                                  │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────┐  │
│  │   SCOUT    │ → │  ENRICHER  │ → │   SCORER   │ → │OUTREACH│  │
│  │            │   │            │   │ (Claude AI)│   │(Claude)│  │
│  │ Scrapers:  │   │ Visits     │   │            │   │        │  │
│  │ • Google   │   │ websites   │   │ Score 0-100│   │ Cold   │  │
│  │ • Clutch   │   │ Extracts:  │   │ Tier A/B/C │   │ email  │  │
│  │ • YellowPg │   │ • Emails   │   │ Budget est │   │ per    │  │
│  │ • Yelp     │   │ • Socials  │   │ Service rec│   │ Tier A │  │
│  └────────────┘   └────────────┘   └────────────┘   └────────┘  │
└──────────────────────────────────────────────────────────────────┘
         ↓                                                ↓
   Raw Lead List                              outputs/leads_*.csv
   (name, website,                            outputs/leads_*.json
    phone, address)
```

**Target Regions:** 🇺🇸 US · 🇬🇧 UK · 🇦🇺 Australia · 🇮🇳 India

**Target Niches:** E-commerce, Restaurants, Law Firms, Real Estate, Healthcare, SaaS, Hotels, Retail, Dental, Fitness, Accounting, Insurance, Auto Dealerships, and more.

---

## Setup

### 1. Prerequisites

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)

### 2. Install dependencies

```bash
cd lead-gen-agent
pip install -r requirements.txt
playwright install chromium  # optional, for JS-heavy sites
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

---

## Usage

### Basic examples

```bash
# Find restaurant leads in the US
python main.py --region US --niche "restaurants" --output csv

# Find law firms in the UK
python main.py --region UK --niche "law firms" --output json

# Multiple regions and niches
python main.py --region US,UK --niche "e-commerce stores,SaaS startups" --output both

# All regions, specific niche, skip enrichment for speed
python main.py --region ALL --niche "dental clinics" --skip-enrichment --output csv

# Top 50 leads only, no outreach emails
python main.py --region AU --niche "real estate agencies" --max-leads 50 --skip-outreach

# Just show the table in terminal
python main.py --region IN --niche "SaaS startups" --output table

# Full pipeline, all regions and niches (takes ~2-4 hours)
python main.py --region ALL --niche ALL --output both
```

### Command-line options

| Flag | Default | Description |
|---|---|---|
| `--region` | `US` | Target region(s): US, UK, AU, IN, ALL. Comma-separated. |
| `--niche` | `restaurants` | Business niche. Use ALL for all 20 niches. |
| `--output` | `csv` | Output format: `csv`, `json`, `both`, `table` |
| `--max-leads` | unlimited | Truncate to top N leads by score |
| `--skip-enrichment` | off | Skip website visits (faster, less contact data) |
| `--skip-outreach` | off | Skip AI email generation (saves API quota) |
| `--verbose` | off | Enable debug logging |

---

## Output Format

Each lead in the CSV/JSON contains:

| Field | Description |
|---|---|
| `name` | Business name |
| `website` | Website URL |
| `email` | Contact email (if found) |
| `phone` | Phone number |
| `address` | Street address |
| `city` | City |
| `country` | Country |
| `industry` | Business category |
| `source` | Which scraper found this lead |
| `rating` | Star rating (if available) |
| `review_count` | Number of reviews |
| `social_links` | LinkedIn, Twitter, Facebook, Instagram |
| `description` | Business description / meta |
| `score` | **AI score 0–100** |
| `tier` | **A / B / C** (A = hottest lead) |
| `reasoning` | Claude's scoring reasoning |
| `estimated_budget_usd_monthly` | Estimated monthly budget |
| `recommended_service` | Best service to pitch |
| `pain_points_identified` | List of identified pain points |
| `outreach_hook` | 3-sentence pitch seed |
| `outreach_email` | Full cold email (Tier A only) |

---

## Scoring Tiers

| Tier | Score | Meaning |
|---|---|---|
| **A** | 80–100 | Hot lead — clear need, budget signals, reachable decision-maker |
| **B** | 50–79 | Warm lead — good fit, longer sales cycle or missing data |
| **C** | 0–49 | Cold lead — poor fit, very small budget, or disqualifying signal |

---

## Data Sources

| Source | Regions | What it finds |
|---|---|---|
| Google Search | All | Any business with web presence |
| Clutch.co | All | Digital agencies, web dev shops |
| YellowPages.com | US only | Local SMBs with verified listings |
| Yelp.com | US, UK, AU | Rated local businesses |

---

## Adding New Scrapers

1. Create `scrapers/my_source.py` inheriting from `BaseScraper`
2. Implement `scrape()` and `_parse_lead()`
3. Return `self._normalise(raw)` for each lead
4. Import and add to `ScoutAgent._scrapers` list in `agents/scout.py`

```python
from scrapers.base import BaseScraper

class MySourceScraper(BaseScraper):
    source_name = "my_source"

    def scrape(self) -> list[dict]:
        # ... your scraping logic
        return [self._normalise(raw) for raw in raws]

    def _parse_lead(self, raw) -> dict:
        return {"name": ..., "website": ..., ...}
```

---

## Ethical Use

- This tool only scrapes **publicly available** business information.
- Built-in rate limiting and random delays are intentional — do not remove them.
- Always comply with the `robots.txt` of scraped sites.
- Use outreach emails responsibly. Include an opt-out link in all commercial emails.
- Respect GDPR (UK/EU), CAN-SPAM (US), and CASL (AU) regulations.
- Do NOT use for spam, mass unsolicited contact, or any illegal purpose.

---

## Tech Stack

- **Python 3.11+**
- **Claude (claude-sonnet-4-6)** — lead scoring & outreach generation
- **requests + BeautifulSoup4** — HTTP scraping
- **Playwright** — optional JS-rendered page support
- **Pydantic Settings** — configuration management
- **Rich** — terminal UI and tables
- **Tenacity** — retry / backoff logic
- **Pandas** — data manipulation
