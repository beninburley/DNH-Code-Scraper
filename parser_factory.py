"""Parser factory to route cities to the correct platform parser."""

from municode_parser import MunicodeParser  # Municipal Code Online
from municode_library_parser import MunicodeLibraryParser  # Municode.com
from generalcode_parser import GeneralCodeParser  # General Code (municipal.codes)
from amlegal_parser import AmlegalParser  # Amlegal
from civiclinq_parser import CivicLinQParser  # CivicLinQ
from codepublishing_parser import CodePublishingParser  # Code Publishing
from encodeplus_parser import EncodePlusParser  # EncodePlus


class ParserFactory:
    """Factory to create the appropriate parser based on platform."""
    
    def __init__(self):
        self.parsers = {
            'Municipal Code Online': MunicodeParser(),
            'Municode': MunicodeLibraryParser(),
            'General Code': GeneralCodeParser(),
            'Amlegal': AmlegalParser(),
            'CivicLinQ': CivicLinQParser(),
            'Code Publishing': CodePublishingParser(),
            'EncodePlus': EncodePlusParser(),
        }
    
    def get_parser(self, platform: str):
        """Get the appropriate parser for the platform."""
        parser = self.parsers.get(platform)
        if not parser:
            raise ValueError(f"No parser available for platform: {platform}")
        return parser
    
    def scrape_city(self, city_info: dict):
        """
        Route to the appropriate parser and scrape the city.
        Returns: (success, sections_list) for compatibility
        """
        platform = city_info.get('platform', 'Unknown')
        
        try:
            parser = self.get_parser(platform)
            result = parser.scrape_city(city_info)
            
            # Handle different return formats
            if isinstance(result, tuple):
                # Old format: (success, sections_list)
                return result
            elif isinstance(result, dict):
                # New format: dict with 'ethics_sections' or None
                sections = result.get('ethics_sections', [])
                return True, sections
            elif result is None:
                # No ethics found
                return True, []
            else:
                return True, []
                
        except ValueError as e:
            print(f"  ⚠️  {str(e)}")
            return True, []  # Success but no sections (unsupported platform)
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            return False, []


if __name__ == '__main__':
    # Test with both platforms
    test_cities = [
        {
            'city': 'Alpine City Municipal Code (Utah)',
            'url': 'https://alpine.municipalcodeonline.com/book?type=ordinances',
            'platform': 'Municipal Code Online'
        },
        {
            'city': 'Hurricane City Code (Utah)',
            'url': 'https://library.municode.com/ut/hurricane/codes/code_of_ordinances',
            'platform': 'Municode'
        }
    ]
    
    factory = ParserFactory()
    
    for city in test_cities:
        print("\n" + "="*80)
        success, sections = factory.scrape_city(city)
        
        if success and sections:
            print(f"✅ Found {len(sections)} section(s)")
        elif success:
            print("ℹ️  No sections found")
        else:
            print("❌ Failed")
