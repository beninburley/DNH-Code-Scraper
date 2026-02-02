"""BYU link collector - scrapes city/municipality links from BYU's repository."""

import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict
import config


def fetch_page(url: str) -> BeautifulSoup:
    """Fetch and parse a webpage."""
    headers = {'User-Agent': config.USER_AGENT}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return BeautifulSoup(response.content, 'lxml')


def extract_municode_links(soup: BeautifulSoup, state_range: str) -> List[Dict[str, str]]:
    """Extract all municipal code links from BYU page for supported platforms."""
    links = []
    
    # Platform identifiers for supported platforms
    SUPPORTED_PLATFORMS = {
        'municode.com': 'Municode',
        'library.municode.com': 'Municode',
        'municipalcodeonline.com': 'Municipal Code Online'
    }
    
    # BYU organizes city codes in unordered lists with bullet points
    # Find all list items in the main content area
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        # Skip navigation links, empty links, and non-code links
        if not text or not href:
            continue
        
        # Skip internal navigation
        if href.startswith('#') or 'guides.law.byu.edu' in href:
            continue
        
        # Check if this is a supported platform
        platform = None
        for domain, platform_name in SUPPORTED_PLATFORMS.items():
            if domain in href.lower():
                platform = platform_name
                break
        
        # Only collect supported platforms
        if platform:
            links.append({
                'city': text,
                'url': href,
                'source_page': state_range,
                'platform': platform
            })
    
    return links


def collect_all_links() -> List[Dict[str, str]]:
    """Collect all Municode links from all BYU pages."""
    all_links = []
    
    for url in config.BYU_URLS:
        print(f"\n📥 Fetching links from: {url}")
        try:
            soup = fetch_page(url)
            
            # Determine which state range this is
            if 'a-h' in url:
                state_range = 'A-H'
            elif 'i-p' in url:
                state_range = 'I-P'
            elif 'q-z' in url:
                state_range = 'Q-Z'
            else:
                state_range = 'Unknown'
            
            links = extract_municode_links(soup, state_range)
            all_links.extend(links)
            print(f"✅ Found {len(links)} municipal code links in {state_range} range")
            
            # Be respectful - wait between requests
            time.sleep(config.REQUEST_DELAY)
            
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
    
    return all_links


def save_links(links: List[Dict[str, str]], filename: str = config.LINKS_CACHE_FILE):
    """Save collected links to JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(links, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Saved {len(links)} links to {filename}")


def load_links(filename: str = config.LINKS_CACHE_FILE) -> List[Dict[str, str]]:
    """Load links from cached JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


if __name__ == '__main__':
    print("🚀 Starting BYU link collection...")
    
    # Check robots.txt first
    print("\n🤖 Checking BYU robots.txt...")
    try:
        robots_url = "https://guides.law.byu.edu/robots.txt"
        response = requests.get(robots_url)
        print("Robots.txt content:")
        print(response.text[:500])  # Show first 500 chars
    except:
        print("No robots.txt found or accessible")
    
    # Collect links
    links = collect_all_links()
    
    # Save to file
    save_links(links)
    
    # Show platform breakdown
    platform_counts = {}
    for link in links:
        platform = link.get('platform', 'Unknown')
        platform_counts[platform] = platform_counts.get(platform, 0) + 1
    
    print(f"\n✨ Collection complete! Found {len(links)} total links")
    print("\n📊 Platform breakdown:")
    for platform, count in sorted(platform_counts.items()):
        print(f"  - {platform}: {count}")
    
    # Show sample
    if links:
        print("\n📋 Sample of collected links:")
        for link in links[:5]:
            print(f"  - {link['city']}: {link['url']}")
