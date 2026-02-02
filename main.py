"""Main scraper orchestrator - coordinates the entire scraping process."""

import os
import sys
from typing import List, Dict
import config
from byu_collector import collect_all_links, save_links, load_links
from parser_factory import ParserFactory
from pdf_generator import PDFGenerator
from utils import ProgressTracker, extract_state_from_url, extract_city_from_text


class MunicipalCodeScraper:
    """Main orchestrator for the municipal code scraping process."""
    
    def __init__(self, test_mode: bool = config.TEST_MODE):
        self.test_mode = test_mode
        self.parser_factory = ParserFactory()
        self.pdf_generator = PDFGenerator()
        self.links = []
    
    def load_or_collect_links(self, force_recollect: bool = False) -> List[Dict]:
        """Load links from cache or collect from BYU."""
        if not force_recollect and os.path.exists(config.LINKS_CACHE_FILE):
            print("📂 Loading cached links...")
            self.links = load_links()
            print(f"✅ Loaded {len(self.links)} links from cache")
        else:
            print("🌐 Collecting links from BYU repository...")
            self.links = collect_all_links()
            save_links(self.links)
        
        return self.links
    
    def process_city(self, city_info: Dict, tracker: ProgressTracker) -> bool:
        """Process a single city."""
        city_name = city_info.get('city', 'Unknown')
        url = city_info.get('url')
        
        # Extract state from URL
        state = extract_state_from_url(url)
        
        # Clean city name
        clean_city = extract_city_from_text(city_name)
        
        try:
            # Scrape the city's code using the appropriate parser
            success, sections = self.parser_factory.scrape_city(city_info)
            
            if not success:
                tracker.update(success=False, has_ethics=False)
                return False
            
            if sections and len(sections) > 0:
                # Generate PDF
                pdf_path = self.pdf_generator.generate_pdf(
                    city_name=clean_city,
                    state=state,
                    sections=sections,
                    source_url=url
                )
                
                if pdf_path:
                    tracker.update(success=True, has_ethics=True)
                    return True
                else:
                    tracker.update(success=False, has_ethics=False)
                    return False
            else:
                # No ethics code found, but scraping was successful
                tracker.update(success=True, has_ethics=False)
                return True
                
        except Exception as e:
            print(f"  ❌ Unexpected error processing {city_name}: {e}")
            tracker.update(success=False, has_ethics=False)
            return False
    
    def run(self, force_recollect: bool = False):
        """Run the complete scraping process."""
        print("=" * 60)
        print("🚀 MUNICIPAL ETHICS CODE SCRAPER")
        print("=" * 60)
        
        if self.test_mode:
            print(f"⚠️  RUNNING IN TEST MODE (will process {config.TEST_LIMIT} cities)")
            print("   Set TEST_MODE = False in config.py to run full scraper\n")
        
        # Step 1: Collect links
        links = self.load_or_collect_links(force_recollect)
        
        if not links:
            print("❌ No links found. Exiting.")
            return
        
        # Step 2: Limit for test mode
        if self.test_mode:
            links = links[:config.TEST_LIMIT]
            print(f"\n📋 Processing {len(links)} cities in test mode")
        else:
            print(f"\n📋 Processing all {len(links)} cities")
        
        # Step 3: Process each city
        tracker = ProgressTracker(len(links))
        
        for i, city_info in enumerate(links, 1):
            print(f"\n[{i}/{len(links)}] ", end="")
            self.process_city(city_info, tracker)
            
            # Print progress every 10 cities
            if i % 10 == 0:
                tracker.print_status()
        
        # Final summary
        print("\n" + "=" * 60)
        print("✨ SCRAPING COMPLETE!")
        print("=" * 60)
        tracker.print_status()
        
        print(f"\n📁 PDFs saved to: {config.OUTPUT_DIR}/")
        
        # List generated PDFs
        if os.path.exists(config.OUTPUT_DIR):
            pdf_files = [f for f in os.listdir(config.OUTPUT_DIR) if f.endswith('.pdf')]
            if pdf_files:
                print(f"\n📄 Generated {len(pdf_files)} PDF(s):")
                for pdf in pdf_files[:10]:  # Show first 10
                    print(f"   - {pdf}")
                if len(pdf_files) > 10:
                    print(f"   ... and {len(pdf_files) - 10} more")


def main():
    """Main entry point."""
    # Check for command line arguments
    force_recollect = '--recollect' in sys.argv
    test_mode = '--test' in sys.argv or config.TEST_MODE
    
    # Override test mode if specified
    if '--full' in sys.argv:
        test_mode = False
    
    # Create scraper
    scraper = MunicipalCodeScraper(test_mode=test_mode)
    
    # Run
    try:
        scraper.run(force_recollect=force_recollect)
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
