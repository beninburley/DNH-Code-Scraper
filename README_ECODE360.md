# eCode360 Municipal Ethics Scraper

A specialized scraper for extracting municipal codes of ethics from ecode360.com, operated by General Code.

## Overview

This scraper is designed to:

1. Collect a list of municipalities from General Code's library (generalcode.com/library)
2. Navigate to each municipality's ecode360 page
3. Search for ethics/conduct chapters
4. Extract the full text of ethics codes
5. Identify aspirational language ("strive", "shall endeavor", etc.)
6. Generate human-readable PDFs

## Files

- **`ecode360_collector.py`** - Scrapes municipality lists from General Code library
- **`ecode360_parser.py`** - Parses individual ecode360 pages for ethics content
- **`main_360.py`** - Main orchestrator script
- **`config.py`** - Configuration settings (updated with ecode360 settings)

## Configuration

Edit `config.py` to configure:

```python
# States to scrape
ECODE360_STATES = ["NY"]  # Add more states as needed

# Output directory
ECODE360_OUTPUT_DIR = "output_pdfs/ecode360"

# Aspirational terms to identify
ASPIRATIONAL_TERMS = [
    "strive", "shall endeavor", "aspire", "seek to",
    "best interest", "shall pursue", "commit to"
]
```

## Usage

### Basic Usage

Scrape all configured states:

```powershell
venv/Scripts/python.exe main_360.py
```

### Test Mode

Process only a few cities for testing:

```powershell
venv/Scripts/python.exe main_360.py --test --test-limit 3
```

### Specify States

Scrape specific states:

```powershell
venv/Scripts/python.exe main_360.py --states NY CA TX
```

### Force Recollection

Ignore cached city list and recollect from web:

```powershell
venv/Scripts/python.exe main_360.py --recollect
```

## Important Notes

### Cloudflare Protection

**⚠️ CRITICAL:** ecode360.com uses Cloudflare bot protection. This means:

1. **The scraper may be blocked** by "Verify you are human" challenges
2. **Running in headed mode** (browser window visible) may help bypass detection
3. **Manual intervention** may be needed to complete Cloudflare challenges
4. **Add delays** between requests to avoid triggering rate limits
5. **Use during off-peak hours** to reduce chance of blocks

### Current Limitations

Due to Cloudflare protection discovered during development:

1. **Content extraction is not yet fully working** - The parser successfully finds ethics chapters but Cloudflare blocks access to the full content pages
2. **Workarounds needed:**
   - Use Cloudflare bypass services (not recommended for ethical reasons)
   - Add manual pauses for CAPTCHA solving
   - Use residential proxies (additional cost)
   - Contact General Code for API access or data partnership

### Architecture

The scraper follows a two-phase approach:

**Phase 1: Collection**

1. Navigate to `generalcode.com/library/#NY`
2. The library page loads municipalities in an iframe from `/source-library/?state=NY`
3. Extract all ecode360 links and municipality names
4. Cache results to `ecode360_cities.json`

**Phase 2: Parsing**

1. For each municipality, load the main code page (e.g., `ecode360.com/MA1379`)
2. Parse the table of contents for chapters
3. Identify ethics-related chapters (containing "ethics", "code of", etc.)
4. Navigate to ethics chapter pages
5. Extract full text content
6. Check for aspirational language
7. Generate formatted PDF

## Search Strategy

### Chapter Identification

Chapters are identified if their title contains:

- "ethic"
- "code of conduct"
- "conflict of interest"
- "financial disclosure"
- "public officer"
- "standards of conduct"

### Aspirational Language Detection

Content is flagged as containing aspirational language if it includes:

- "strive"
- "shall endeavor"
- "aspire"
- "seek to"
- "best interest"
- "shall pursue"
- "commit to"

## Output Format

PDFs are generated with:

- **Filename pattern:** `{STATE}_{CITY}_Ethics_{YYYYMMDD}.pdf`
- **Formatting:**
  - Readable font (Times New Roman, 12pt)
  - Proper indentation and spacing
  - Section headings clearly marked
  - Source URL included in metadata
  - Aspirational language highlighted (if found)

## Example Output

```
NY_Malta_Ethics_20260202.pdf
NY_Albany_Ethics_20260202.pdf
NY_Buffalo_Ethics_20260202.pdf
```

## Troubleshooting

### "Just a moment..." page

This is Cloudflare's challenge page. Solutions:

1. Run in headed mode (set `headless=False` in parser)
2. Add longer delays between requests
3. Use a different IP address or proxy
4. Solve challenges manually

### No content extracted

Check the debug HTML files:

- `debug_{STATE}_library.html` - Municipality list page
- `debug_malta_home.html` - Homepage structure
- `debug_section_{ID}.html` - Section content page

### Empty or missing PDFs

Ensure:

1. Output directory exists
2. Playwright browsers are installed: `playwright install`
3. Required Python packages are installed

## Future Enhancements

1. **Cloudflare bypass:** Implement stealth techniques or use bypass services
2. **Better content extraction:** Improve HTML parsing for various ecode360 layouts
3. **Parallel processing:** Speed up scraping with concurrent requests
4. **Resume capability:** Save progress and resume interrupted scrapes
5. **Integration:** Merge with main scraper pipeline
6. **Database storage:** Store results in database instead of just PDFs

## Development Notes

Created February 2, 2026

The scraper architecture is complete and functional for:

- ✅ Municipality list collection
- ✅ Chapter identification
- ✅ URL construction
- ⚠️ Content extraction (blocked by Cloudflare)
- ✅ PDF generation

Next steps require addressing the Cloudflare protection issue before full deployment.

## Contact

For questions or issues, refer to the main project README or documentation.
