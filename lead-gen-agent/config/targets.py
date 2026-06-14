"""
Target regions, niches, ideal customer profile (ICP), and search keywords
used throughout the lead generation pipeline.
"""

# ── Regions ───────────────────────────────────────────────────────────────────
# Maps a friendly region key to its country name + list of major cities.

REGIONS: dict[str, dict] = {
    "US": {
        "country": "United States",
        "country_code": "US",
        "cities": [
            "New York",
            "Los Angeles",
            "Chicago",
            "Houston",
            "Phoenix",
            "Philadelphia",
            "San Antonio",
            "San Diego",
            "Dallas",
            "San Jose",
            "Austin",
            "Jacksonville",
            "Fort Worth",
            "Columbus",
            "Charlotte",
            "Indianapolis",
            "San Francisco",
            "Seattle",
            "Denver",
            "Nashville",
        ],
        "yellow_pages_states": {
            "New York": "NY",
            "Los Angeles": "CA",
            "Chicago": "IL",
            "Houston": "TX",
            "Phoenix": "AZ",
            "Philadelphia": "PA",
            "San Antonio": "TX",
            "San Diego": "CA",
            "Dallas": "TX",
            "San Jose": "CA",
            "Austin": "TX",
            "Jacksonville": "FL",
            "Fort Worth": "TX",
            "Columbus": "OH",
            "Charlotte": "NC",
            "Indianapolis": "IN",
            "San Francisco": "CA",
            "Seattle": "WA",
            "Denver": "CO",
            "Nashville": "TN",
        },
    },
    "UK": {
        "country": "United Kingdom",
        "country_code": "GB",
        "cities": [
            "London",
            "Birmingham",
            "Manchester",
            "Leeds",
            "Glasgow",
            "Liverpool",
            "Sheffield",
            "Edinburgh",
            "Bristol",
            "Leicester",
            "Coventry",
            "Bradford",
            "Nottingham",
            "Cardiff",
            "Belfast",
        ],
    },
    "AU": {
        "country": "Australia",
        "country_code": "AU",
        "cities": [
            "Sydney",
            "Melbourne",
            "Brisbane",
            "Perth",
            "Adelaide",
            "Gold Coast",
            "Canberra",
            "Newcastle",
            "Wollongong",
            "Hobart",
        ],
    },
    "IN": {
        "country": "India",
        "country_code": "IN",
        "cities": [
            "Mumbai",
            "Delhi",
            "Bangalore",
            "Hyderabad",
            "Chennai",
            "Kolkata",
            "Pune",
            "Ahmedabad",
            "Jaipur",
            "Surat",
            "Lucknow",
            "Kanpur",
            "Nagpur",
            "Indore",
            "Thane",
        ],
    },
}

# ── Niches ────────────────────────────────────────────────────────────────────
# Businesses that commonly need digital marketing or web development services.

NICHES: list[str] = [
    "e-commerce stores",
    "restaurants",
    "law firms",
    "real estate agencies",
    "healthcare clinics",
    "SaaS startups",
    "hotels and hospitality",
    "retail chains",
    "logistics companies",
    "educational institutes",
    "dental clinics",
    "fitness gyms",
    "accounting firms",
    "insurance agencies",
    "auto dealerships",
    "beauty salons",
    "home services",
    "construction companies",
    "financial advisors",
    "wedding planners",
]

# ── Ideal Customer Profile (ICP) ──────────────────────────────────────────────

ICP: dict = {
    "budget_range": {
        "min_usd": 2000,
        "max_usd": 50000,
        "monthly_retainer_target": 3000,
    },
    "company_size": {
        "employees_min": 5,
        "employees_max": 500,
        "ideal_range": "10–100 employees",
    },
    "industry_signals": [
        "Has a website older than 3 years",
        "Low Google search ranking for local keywords",
        "No active social media presence",
        "Missing Google My Business listing",
        "No HTTPS / SSL certificate",
        "Poor mobile responsiveness",
        "No email marketing or newsletter",
        "Brick-and-mortar with no online ordering / booking",
        "Competitor outranking them on Google Ads",
        "Recently funded startup needing growth",
    ],
    "pain_points": [
        "Not getting enough leads online",
        "Low website traffic",
        "Poor conversion rate",
        "Bad online reviews with no response strategy",
        "No clear brand identity online",
        "Website down or broken",
        "No e-commerce capability for physical store",
        "Spending on ads with poor ROI",
        "Can't compete with larger chain brands",
        "No CRM or customer follow-up system",
    ],
    "decision_makers": [
        "Owner / Founder",
        "CEO",
        "Marketing Manager",
        "Head of Growth",
        "Operations Manager",
    ],
    "disqualifiers": [
        "Already has an in-house marketing team of 10+",
        "Enterprise company with $100M+ revenue",
        "Government or NGO (long sales cycles)",
        "Actively in bankruptcy or closure",
    ],
}

# ── Search Keywords ───────────────────────────────────────────────────────────
# Used by scrapers to query directories and search engines.

SEARCH_KEYWORDS: list[str] = [
    "{niche} near me",
    "best {niche} in {city}",
    "top {niche} {city}",
    "{niche} {city} contact",
    "{niche} company {city}",
    "{niche} agency {city}",
    "{niche} services {city}",
    "local {niche} {city}",
    "{niche} {city} website",
    "{niche} business {city} {country}",
    "hire {niche} {city}",
    "{niche} professionals {city}",
]
