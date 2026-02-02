"""
Main orchestrator for ecode360 scraper.
Standalone script to scrape municipal ethics codes from ecode360.com.

IMPORTANT NOTES:
- Cloudflare Protection: ecode360.com uses Cloudflare bot protection
- This may require running in headed (non-headless) mode
- Manual intervention may be needed to complete challenges
- Consider adding delays between requests

Usage:
    python main_360.py
"""

import os
import sys
from typing import List, Dict
from datetime import datetime
import json

# Import our custom modules
from ecode360_collector import Ecode360Collector
from ecode360_parser import Ecode360Parser
from pdf_generator import PDFGenerator
import config


class Ecode360Scraper:
    """Main orchestrator for ecode360 scraping."""
    
    def __init__(self, states: List[str] = None):
        """
        Initialize the scraper.
        
        Args:
            states: List of state codes to scrape (e.g., ['NY', 'CA'])
                   If None, uses config.ECODE360_STATES
        """
        self.states = states or config.ECODE360_STATES
        self.collector = Ecode360Collector()
        self.parser = Ecode360Parser()
        self.pdf_generator = PDFGenerator(output_dir=config.ECODE360_OUTPUT_DIR)
        self.results = {
            'total_cities': 0,
            'processed': 0,
            'ethics_found': 0,
            'errors': 0,
            'cloudflare_blocks': 0
        }
    
    def collect_all_cities(self, force_recollect: bool = False) -> List[Dict]:
        """
        Collect cities from all configured states.
        
        Args:
            force_recollect: If True, ignore cache and recollect from web
            
        Returns:
            List of city dictionaries
        """
        cache_file = "ecode360_cities.json"
        
        if not force_recollect and os.path.exists(cache_file):
            print(f"📂 Loading cached cities from {cache_file}...")
            return self.collector.load_cities(cache_file)
        
        all_cities = []
        for state in self.states:
            cities = self.collector.collect_state_cities(state)
            all_cities.extend(cities)
        
        # Save to cache
        self.collector.save_cities(all_cities, cache_file)
        
        return all_cities
    
    def process_city(self, city_info: Dict) -> bool:
        """
        Process a single city.
        
        Args:
            city_info: Dictionary with city information
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Scrape the city
            result = self.parser.scrape_city(city_info)
            
            if result and result.get('ethics_sections'):
                # Generate PDF
                city_name = city_info['city']
                state = city_info['state']
                
                # Prepare sections for PDF
                sections = []
                for section in result['ethics_sections']:
                    sections.append({
                        'title': section['title'],
                        'content': section['full_text'],
                        'url': section['url']
                    })
                
                # Generate PDF
                filepath = self.pdf_generator.generate_pdf(
                    city_name=city_name,
                    state=state,
                    sections=sections,
                    source_url=city_info['url']
                )
                
                if filepath:
                    print(f"  ✅ PDF generated: {filepath}")
                    self.results['ethics_found'] += 1
                    return True
                else:
                    print(f"  ⚠️  PDF generation failed")
                    return False
            else:
                print(f"  ⚠️  No ethics code found")
                return False
                
        except Exception as e:
            print(f"  ❌ Error processing city: {e}")
            self.results['errors'] += 1
            return False
    
    def run(self, test_mode: bool = False, test_limit: int = 5):
        """
        Run the scraper.
        
        Args:
            test_mode: If True, only process a limited number of cities
            test_limit: Number of cities to process in test mode
        """
        print("=" * 70)
        print("ECODE360 ETHICS CODE SCRAPER")
        print("=" * 70)
        print(f"\nConfiguration:")
        print(f"  States: {', '.join(self.states)}")
        print(f"  Test Mode: {test_mode}")
        if test_mode:
            print(f"  Test Limit: {test_limit} cities")
        print(f"  Output Directory: {config.ECODE360_OUTPUT_DIR}")
        print()
        
        # Collect cities
        print("📋 Collecting municipality list...")
        cities = self.collect_all_cities()
        self.results['total_cities'] = len(cities)
        
        if not cities:
            print("❌ No cities found to process!")
            return
        
        print(f"✅ Found {len(cities)} municipalities")
        print()
        
        # Apply test mode limit
        if test_mode:
            cities = cities[:test_limit]
            print(f"🧪 Test mode: Processing only {len(cities)} cities")
            print()
        
        # Process each city
        for i, city_info in enumerate(cities, 1):
            print(f"[{i}/{len(cities)}] Processing {city_info['city']}, {city_info['state']}...")
            
            self.process_city(city_info)
            self.results['processed'] += 1
            
            print()  # Blank line between cities
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print final summary of scraping results."""
        print()
        print("=" * 70)
        print("SCRAPING SUMMARY")
        print("=" * 70)
        print(f"Total municipalities: {self.results['total_cities']}")
        print(f"Processed: {self.results['processed']}")
        print(f"Ethics codes found: {self.results['ethics_found']}")
        print(f"Errors: {self.results['errors']}")
        print(f"Output directory: {config.ECODE360_OUTPUT_DIR}")
        print("=" * 70)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Scrape municipal ethics codes from ecode360.com'
    )
    parser.add_argument(
        '--states',
        nargs='+',
        help='State codes to scrape (e.g., NY CA). Default: from config.py'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode (limited cities)'
    )
    parser.add_argument(
        '--test-limit',
        type=int,
        default=5,
        help='Number of cities to process in test mode (default: 5)'
    )
    parser.add_argument(
        '--recollect',
        action='store_true',
        help='Force recollection of city list (ignore cache)'
    )
    
    args = parser.parse_args()
    
    # Create scraper
    scraper = Ecode360Scraper(states=args.states)
    
    # Recollect if requested
    if args.recollect:
        print("🔄 Recollecting city list...")
        scraper.collect_all_cities(force_recollect=True)
    
    # Run
    try:
        scraper.run(test_mode=args.test, test_limit=args.test_limit)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        scraper.print_summary()
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
