"""Configuration settings for the municipal code scraper."""

# BYU site URLs
BYU_URLS = [
    "https://guides.law.byu.edu/state_local/a-h",
    "https://guides.law.byu.edu/state_local/i-p",
    "https://guides.law.byu.edu/state_local/q-z"
]

# Rate limiting
REQUEST_DELAY = 2.5  # seconds between requests

# Search terms for ethics codes (case-insensitive)
ETHICS_TERMS = [
    "code of ethics",
    "code of conduct",
    "ethics code",
    "professional conduct",
    "standards of conduct",
    "ethical standards",
    "conduct code",
    "rules of conduct",
    "employee conduct",
    "ethics policy",
    "ethics",  # Added - catches sections titled just "Ethics"
    "conflict of interest",
    "conflicts of interest"
]

# Output settings
OUTPUT_DIR = "output_pdfs"
LINKS_CACHE_FILE = "city_links.json"

# User agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Testing mode
TEST_MODE = False  # Set to False to run full scraper
TEST_LIMIT = 5  # Number of cities to process in test mode
