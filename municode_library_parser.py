"""Municode parser for ethics codes."""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
from config import ETHICS_TERMS

class MunicodeLibraryParser:
    def __init__(self):
        self.ethics_terms = ETHICS_TERMS
    
    def search_for_ethics_sections(self, text):
        """Check if text contains ethics-related terms."""
        text_lower = text.lower()
        return any(term.lower() in text_lower for term in self.ethics_terms)
    
    def scrape_city(self, city_info):
        """
        Scrape a Municode city.
        Returns: (success, sections_list)
        """
        city_name = city_info['city']
        url = city_info['url']
        
        print(f"🔍 Scraping {city_name}...")
        print(f"  Platform: Municode")
        print(f"  URL: {url}")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                page.goto(url, timeout=60000)
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(3000)
                
                print("  🔍 Searching table of contents for ethics sections...")
                
                html_content = page.content()
                soup = BeautifulSoup(html_content, 'lxml')
                
                # Look for links/buttons with ethics-related text in the TOC
                all_elements = soup.find_all(['a', 'button', 'span', 'div'])
                ethics_links = []
                
                for elem in all_elements:
                    text = elem.get_text(strip=True)
                    if self.search_for_ethics_sections(text):
                        # Found a TOC entry with ethics content
                        ethics_links.append({
                            'text': text,
                            'element': elem
                        })
                
                if not ethics_links:
                    print(f"  ℹ️  No ethics-related sections found in TOC for {city_name}")
                    browser.close()
                    return True, []
                
                print(f"  ✅ Found {len(ethics_links)} ethics-related TOC entries")
                
                # Municode platform uses JavaScript-heavy dynamic TOC that's difficult to extract
                # For now, we'll record that ethics content exists with URL to visit
                ethics_sections = []
                
                # Get unique chapter titles (deduplicate the 11 duplicate TOC entries)
                unique_chapters = {}
                for link_info in ethics_links:
                    title = link_info['text']
                    # Extract just the chapter name, removing all the UI clutter
                    if 'Chapter' in title and 'ETHICS' in title.upper():
                        # Try to extract clean chapter name
                        parts = title.split('Chapter')
                        for part in parts:
                            if 'ETHICS' in part.upper():
                                clean_title = 'Chapter' + part.split('Expand')[0].split('Close')[0].strip()
                                unique_chapters[clean_title] = True
                                break
                
                # If we found clean chapter names, use them
                if unique_chapters:
                    for chapter_title in unique_chapters.keys():
                        ethics_sections.append({
                            'title': chapter_title,
                            'content': f"Ethics chapter detected: {chapter_title}\n\nNote: {city_name}'s municipal code is hosted on Municode's JavaScript-heavy platform which requires interactive navigation to extract full content. The ethics chapter exists and can be viewed at: {url}\n\nTo extract the full text, visit the URL above and navigate to the ethics chapter."
                        })
                else:
                    # Fallback: just use first unique title
                    ethics_sections.append({
                        'title': f"{city_name} Ethics Code",
                        'content': f"Ethics content detected in {city_name}'s municipal code.\n\nNote: This code is hosted on Municode's JavaScript-heavy platform which requires interactive navigation. The ethics chapter can be viewed at: {url}\n\nManual extraction recommended for full content."
                    })
                
                browser.close()
                
                if ethics_sections:
                    print(f"  ✅ Found {len(ethics_sections)} ethics-related section(s)")
                    for section in ethics_sections:
                        print(f"    - {section['title']}")
                    return True, ethics_sections
                else:
                    print(f"  ℹ️  No extractable ethics sections found in {city_name}")
                    return True, []
                        
        except Exception as e:
            print(f"  ❌ Error scraping {city_name}: {str(e)}")
            return False, []

if __name__ == '__main__':
    # Test with multiple Municode cities
    test_cities = [
        {
            'city': 'Hurricane City Code (Utah)',
            'url': 'https://library.municode.com/ut/hurricane/codes/code_of_ordinances',
            'platform': 'Municode'
        },
        {
            'city': 'Sandy City Municipal Code (Utah)',
            'url': 'https://library.municode.com/ut/sandy/codes/city_code?nodeId=SACO',
            'platform': 'Municode'
        },
        {
            'city': 'Honeyville City Code (Utah)',
            'url': 'https://library.municode.com/ut/honeyville/codes/code_of_ordinances?nodeId=17273',
            'platform': 'Municode'
        }
    ]
    
    parser = MunicodeLibraryParser()
    
    for test_city in test_cities:
        print("\n" + "="*80)
        success, sections = parser.scrape_city(test_city)
        
        if success and sections:
            print(f"✅ SUCCESS: Found {len(sections)} sections")
            for i, section in enumerate(sections, 1):
                print(f"\nSection {i}:")
                print(f"  Title: {section['title']}")
                print(f"  Content length: {len(section['content'])} chars")
                print(f"  Content preview: {section['content'][:200]}...")
        elif success:
            print("⚠️  No ethics sections found")
        else:
            print("❌ Failed to scrape")
