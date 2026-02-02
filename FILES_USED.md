# Files Used by main.py

## Core Files (Required)

### Entry Point

1. **main.py** - Main orchestrator

### Configuration

2. **config.py** - Settings and configuration

### Core Modules

3. **byu_collector.py** - Collects city links from BYU repository
4. **parser_factory.py** - Routes to appropriate parser based on platform
5. **pdf_generator.py** - Generates formatted PDFs from scraped content
6. **utils.py** - Utility functions (ProgressTracker, URL parsing, etc.)

### Platform Parsers (7 total)

7. **municode_parser.py** - Municipal Code Online parser
8. **municode_library_parser.py** - Municode Library parser
9. **generalcode_parser.py** - General Code parser
10. **amlegal_parser.py** - Amlegal parser
11. **civiclinq_parser.py** - CivicLinQ parser
12. **codepublishing_parser.py** - Code Publishing parser
13. **encodeplus_parser.py** - EncodePlus parser

### Data Files

14. **city_links.json** - Cached city links (auto-generated)
15. **output_pdfs/** - Output directory for generated PDFs

### Documentation

16. **README.md** - Project documentation
17. **ARCHITECTURE.md** - Detailed architecture overview
18. **requirements.txt** - Python dependencies
19. **.gitignore** - Git ignore rules

---

## Total: 19 files + 2 directories

All test files and temporary scripts have been removed.
The codebase is now clean and production-ready.

## To Run:

```bash
# Test mode (processes first 5 cities)
python main.py

# Full scrape
python main.py --full

# Force re-collect links
python main.py --recollect
```
