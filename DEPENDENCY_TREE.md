# main.py Dependency Tree

```
main.py
│
├── config.py (settings)
│   └── ETHICS_TERMS, TEST_MODE, OUTPUT_DIR, etc.
│
├── byu_collector.py
│   ├── requests (external)
│   ├── bs4 (external)
│   └── config.py
│
├── parser_factory.py
│   ├── municode_parser.py
│   │   ├── playwright (external)
│   │   ├── bs4 (external)
│   │   └── config.py
│   │
│   ├── municode_library_parser.py
│   │   ├── playwright (external)
│   │   ├── bs4 (external)
│   │   └── config.py
│   │
│   ├── generalcode_parser.py
│   │   ├── playwright (external)
│   │   └── bs4 (external)
│   │
│   ├── amlegal_parser.py
│   │   ├── playwright (external)
│   │   └── bs4 (external)
│   │
│   ├── civiclinq_parser.py
│   │   ├── playwright (external)
│   │   └── bs4 (external)
│   │
│   ├── codepublishing_parser.py
│   │   ├── playwright (external)
│   │   └── bs4 (external)
│   │
│   └── encodeplus_parser.py
│       ├── playwright (external)
│       └── bs4 (external)
│
├── pdf_generator.py
│   ├── playwright (external)
│   ├── datetime (stdlib)
│   ├── re (stdlib)
│   └── config.py
│
└── utils.py
    ├── time (stdlib)
    ├── functools (stdlib)
    └── config.py
```

## External Dependencies (from requirements.txt)

- **playwright** - Browser automation for web scraping
- **beautifulsoup4** - HTML parsing
- **lxml** - XML/HTML parser (used by BeautifulSoup)
- **requests** - HTTP library (used by byu_collector)

## Data Flow

1. **main.py** starts execution
2. **byu_collector** fetches city links → saves to **city_links.json**
3. For each city:
   - **parser_factory** selects appropriate parser
   - Parser scrapes website for ethics content
   - If found: **pdf_generator** creates PDF → saves to **output_pdfs/**
   - **utils.ProgressTracker** updates statistics
4. Final summary printed

## File Count

- **Core modules**: 6 files (main, config, byu_collector, parser_factory, pdf_generator, utils)
- **Parsers**: 7 files (one per platform)
- **Data**: 2 items (city_links.json, output_pdfs/ directory)
- **Documentation**: 4 files (README, ARCHITECTURE, FILES_USED, .gitignore)
- **Config**: 1 file (requirements.txt)

**Total: 20 files + 2 directories**
