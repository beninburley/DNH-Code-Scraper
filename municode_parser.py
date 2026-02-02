"""Municode parser - extracts ethics/conduct codes from municipal code sites."""

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time
import re
from typing import Optional, List, Dict, Tuple
import config


class MunicodeParser:
    """Parser for Municode and Municipal Code Online municipal code websites."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': config.USER_AGENT})
    
    def search_for_ethics_sections(self, text: str) -> bool:
        """Check if text contains ethics/conduct keywords (case-insensitive)."""
        text_lower = text.lower()
        return any(term in text_lower for term in config.ETHICS_TERMS)
    
    def fetch_municode_toc(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch the table of contents from a municipal code site."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except Exception as e:
            print(f"  ❌ Error fetching {url}: {e}")
            return None
    
    def fetch_with_playwright(self, url: str) -> Optional[str]:
        """Fetch JavaScript-rendered content using Playwright."""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent=config.USER_AGENT)
                page.goto(url, wait_until='networkidle', timeout=60000)
                time.sleep(2)  # Wait for initial load
                
                # For Municipal Code Online, navigate through chapters to load all content
                # ONLY if we're on the main page (no anchor in URL)
                if 'municipalcodeonline.com' in url.lower() and '#name=' not in url:
                    print("  🔄 Loading chapter content...")
                    try:
                        # Get all chapter links from the TOC (top-level items with numbers)
                        all_chapters = []
                        
                        # Find all tree items
                        tree_items = page.locator('[role="treeitem"]').all()
                        
                        # Filter for chapter-level items (usually just have a number and name)
                        for item in tree_items[:20]:  # Limit to prevent issues
                            try:
                                text = item.text_content()
                                # Chapter items typically start with a number followed by space
                                if text and len(text) > 0 and text[0].isdigit() and ' ' in text:
                                    all_chapters.append(text.strip())
                            except:
                                pass
                        
                        print(f"    Found {len(all_chapters)} chapters to check")
                        
                        # Click through each chapter to load content, collect all content
                        # (don't stop at first match - we want to find ALL ethics sections)
                        ethics_chapters = []
                        for i, chapter_name in enumerate(all_chapters):
                            try:
                                # Click on the chapter
                                chapter_link = page.get_by_text(chapter_name, exact=False).first
                                chapter_link.click()
                                time.sleep(1)  # Wait for content to load
                                
                                # Get the HTML after loading this chapter
                                chapter_html = page.content()
                                
                                # Check if any ethics terms are in this chapter
                                has_ethics = any(term in chapter_html.lower() for term in config.ETHICS_TERMS)
                                if has_ethics:
                                    # Check if it's a real ethics section (not just "conduct" in "animal conduct")
                                    soup_check = BeautifulSoup(chapter_html, 'lxml')
                                    section_divs = soup_check.find_all('div', class_='phx-name')
                                    has_real_ethics = False
                                    for div in section_divs:
                                        heading_link = div.find('a', class_='k-link')
                                        if heading_link:
                                            heading_text = heading_link.get_text(strip=True).lower()
                                            # Must contain ethics term AND not be about animals/pets
                                            if any(term in heading_text for term in config.ETHICS_TERMS):
                                                if 'animal' not in heading_text and 'pet' not in heading_text:
                                                    has_real_ethics = True
                                                    break
                                    
                                    if has_real_ethics:
                                        print(f"    ✓ Found ethics content in chapter: {chapter_name}")
                                        ethics_chapters.append(chapter_html)
                            except Exception as e:
                                pass  # Skip this chapter if it fails
                        
                        if ethics_chapters:
                            # Return the last chapter with ethics content
                            full_html = ethics_chapters[-1]
                        else:
                            # No ethics content found in any chapter, return last page state
                            full_html = page.content()
                        
                        browser.close()
                        return full_html
                        
                    except Exception as e:
                        print(f"    ⚠️ Error loading chapters: {e}")
                
                # For direct links with #name= or other platforms, just get the content
                content = page.content()
                browser.close()
                return content
        except Exception as e:
            print(f"  ❌ Playwright error for {url}: {e}")
            return None
    
    def find_ethics_sections(self, soup: BeautifulSoup, base_url: str, platform: str) -> List[Dict[str, str]]:
        """Find all sections related to ethics/conduct in the TOC."""
        ethics_sections = []
        
        if platform == 'Municipal Code Online':
            # Municipal Code Online structure:
            # Content is in <div class="loadable" id="contents">
            # Section headings are <div class="phx-name"> inside the loadable div
            # Text content appears as direct text/children after the phx-name div's parent
            
            # Find the main content area
            contents_div = soup.find('div', class_='loadable', id='contents')
            if not contents_div:
                return ethics_sections
            
            # Find all section headings within the content area
            section_divs = contents_div.find_all('div', class_='phx-name')
            
            for section_div in section_divs:
                # Get the heading text from the <a> tag
                heading_link = section_div.find('a', class_='k-link')
                if not heading_link:
                    continue
                
                heading_text = heading_link.get_text(strip=True)
                
                # Skip chapter-level titles (e.g., "3 Ethics", "2 Administration")
                # These are too broad and contain entire chapters
                # We want specific sections like "3-1-2" or "3.12.070"
                words = heading_text.split()
                if len(words) >= 1:
                    first_word = words[0]
                    # If first word is just a single digit or single digit-hyphen (like "3" or "3-1" without further detail)
                    # and there's no dot or multiple hyphens, it's likely a chapter title
                    if first_word.replace('-', '').replace('.', '').isdigit():
                        # Count dots and hyphens
                        if first_word.count('.') < 2 and first_word.count('-') < 2:
                            # This is likely a chapter/part title, not a specific section
                            continue
                
                # Check if this is an ethics-related section
                if not self.search_for_ethics_sections(heading_text):
                    continue
                
                # Extract content
                # The content appears right after the section_div's parent div
                content_parts = []
                
                parent = section_div.parent
                if parent:
                    # Get all text nodes and elements after the phx-name div
                    # but before the next section heading
                    for sibling in parent.next_siblings:
                        # Skip if we're just seeing whitespace
                        if isinstance(sibling, str):
                            text = sibling.strip()
                            if text:
                                # Check if this text starts with a section number (stop here)
                                # Section numbers look like: "3.12.090" or "2.01.140" (dots) or "3-1-2" (hyphens)
                                if len(text) > 3 and text[0].isdigit() and ('.' in text[:10] or '-' in text[:10]):
                                    break
                                content_parts.append(text)
                        elif sibling.name == 'div':
                            # Stop at next section or at history/docs section
                            if 'phx-name' in sibling.get('class', []) or 'phx-docs' in sibling.get('class', []):
                                break
                            # Otherwise get text from this div
                            text = sibling.get_text(strip=True)
                            if text:
                                # Check if text starts with section number pattern
                                if len(text) > 3 and text[0].isdigit() and '.' in text[:10]:
                                    break
                                content_parts.append(text)
                        else:
                            # Get text from other elements (p, span, etc.)
                            if hasattr(sibling, 'get_text'):
                                text = sibling.get_text(strip=True)
                                if text:
                                    # Check for section number at start
                                    if len(text) > 3 and text[0].isdigit() and '.' in text[:10]:
                                        break
                                    content_parts.append(text)
                        
                        # Safety limit - stop if we have enough content
                        total_length = sum(len(p) for p in content_parts)
                        if total_length > 5000:  # Max 5000 chars per section
                            break
                
                # Add the section with clean text
                if content_parts:
                    ethics_sections.append({
                        'title': heading_text,
                        'content': ' '.join(content_parts),
                        'type': 'section'
                    })
                else:
                    # Even if no content, add the section (might be empty but valid)
                    ethics_sections.append({
                        'title': heading_text,
                        'content': '',
                        'type': 'section'
                    })
        
        else:  # Municode
            # Original Municode strategies
            # Strategy 1: Look for links in the TOC
            for link in soup.find_all('a', href=True):
                link_text = link.get_text(strip=True)
                if self.search_for_ethics_sections(link_text):
                    ethics_sections.append({
                        'title': link_text,
                        'url': self._make_absolute_url(link['href'], base_url),
                        'type': 'link'
                    })
            
            # Strategy 2: Look for section headers
            for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                header_text = header.get_text(strip=True)
                if self.search_for_ethics_sections(header_text):
                    # Try to find associated link or section
                    parent = header.find_parent(['div', 'section', 'article'])
                    if parent:
                        ethics_sections.append({
                            'title': header_text,
                            'content': str(parent),
                            'type': 'header'
                        })
        
        return ethics_sections
    
    def _extract_section_content(self, element) -> str:
        """Extract content from an element and its siblings until next section."""
        content_parts = [str(element)]
        
        # Get following siblings until we hit another section heading
        for sibling in element.find_next_siblings():
            # Stop if we hit another heading
            if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                break
            # Stop if we hit a div with an id (likely another section)
            if sibling.name == 'div' and sibling.get('id'):
                break
            content_parts.append(str(sibling))
            
            # Limit content length
            if len(''.join(content_parts)) > 50000:
                break
        
        return ''.join(content_parts)
    
    def _make_absolute_url(self, url: str, base_url: str) -> str:
        """Convert relative URL to absolute."""
        if url.startswith('http'):
            return url
        from urllib.parse import urljoin
        return urljoin(base_url, url)
    
    def extract_section_content(self, section_url: str) -> Optional[str]:
        """Extract the full content of a section."""
        try:
            # Try regular request first
            response = self.session.get(section_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Look for main content area
            content_areas = soup.find_all(['div', 'article', 'section'], 
                                         class_=re.compile(r'content|main|body|text|section'))
            
            if content_areas:
                return str(content_areas[0])
            else:
                # Fallback: return body content
                body = soup.find('body')
                return str(body) if body else response.text
                
        except Exception as e:
            print(f"  ❌ Error extracting content from {section_url}: {e}")
            return None
    
    def scrape_city(self, city_info: Dict[str, str]) -> Tuple[bool, Optional[List[Dict]]]:
        """
        Scrape a city's municipal code for ethics sections.
        
        Returns:
            (success: bool, sections: Optional[List[Dict]])
        """
        city_name = city_info.get('city', 'Unknown')
        url = city_info.get('url')
        platform = city_info.get('platform', 'Unknown')
        
        print(f"\n🔍 Scraping {city_name}...")
        print(f"  Platform: {platform}")
        print(f"  URL: {url}")
        
        if not url:
            print("  ⚠️  No URL provided")
            return False, None
        
        # Municipal Code Online requires JavaScript, use Playwright
        if platform == 'Municipal Code Online':
            html = self.fetch_with_playwright(url)
            if html:
                soup = BeautifulSoup(html, 'lxml')
            else:
                return False, None
        else:
            # Fetch main page for other platforms
            soup = self.fetch_municode_toc(url)
            if not soup:
                # Try with Playwright for JavaScript-rendered content
                print("  🔄 Trying with Playwright...")
                html = self.fetch_with_playwright(url)
                if html:
                    soup = BeautifulSoup(html, 'lxml')
                else:
                    return False, None
        
        # Search for ethics sections
        ethics_sections = self.find_ethics_sections(soup, url, platform)
        
        if not ethics_sections:
            print(f"  ℹ️  No ethics code found in {city_name}")
            return True, None
        
        print(f"  ✅ Found {len(ethics_sections)} ethics-related section(s)")
        
        # Fetch content for each section
        full_sections = []
        for section in ethics_sections:
            print(f"    - {section['title']}")
            
            if section['type'] == 'link' and 'url' in section:
                time.sleep(config.REQUEST_DELAY)
                content = self.extract_section_content(section['url'])
                if content:
                    section['content'] = content
            
            full_sections.append(section)
        
        return True, full_sections if full_sections else None


if __name__ == '__main__':
    # Test with a sample URL
    parser = MunicodeParser()
    
    test_city = {
        'city': 'Test City',
        'url': 'https://library.municode.com/',
        'platform': 'Municode'
    }
    
    success, sections = parser.scrape_city(test_city)
    
    if sections:
        print(f"\n✅ Successfully scraped {len(sections)} sections")
        for section in sections:
            print(f"  - {section['title']}")
    else:
        print("\n❌ No sections found or error occurred")
