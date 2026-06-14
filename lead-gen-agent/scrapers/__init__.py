"""
Scraper package — one module per data source.
Each scraper inherits from BaseScraper and returns a list of normalised lead dicts.
"""

from scrapers.base import BaseScraper
from scrapers.google_maps import GoogleMapsScraper
from scrapers.clutch import ClutchScraper
from scrapers.yellow_pages import YellowPagesScraper
from scrapers.yelp import YelpScraper

__all__ = [
    "BaseScraper",
    "GoogleMapsScraper",
    "ClutchScraper",
    "YellowPagesScraper",
    "YelpScraper",
]
