# Quick Start Guide - eCode360 Scraper

## 🚀 Get Started in 3 Steps

### Step 1: Activate Virtual Environment

```powershell
& "D:\DNH Code Scraper\venv\Scripts\Activate.ps1"
```

### Step 2: Run Test Scrape (Recommended First Run)

```powershell
venv/Scripts/python.exe main_360.py --test --test-limit 3
```

This will:

- ✅ Load 712 NY municipalities from cache
- ✅ Process only 3 cities for testing
- ✅ Generate PDFs in `output_pdfs/ecode360/`
- ✅ Show summary statistics

### Step 3: Run Full Scrape (When Ready)

```powershell
venv/Scripts/python.exe main_360.py
```

## 📊 What to Expect

**Browser Window Will Open** - This is normal! Running in headed mode helps avoid bot detection.

**Progress Output:**

```
======================================================================
ECODE360 ETHICS CODE SCRAPER
======================================================================

Configuration:
  States: NY
  Test Mode: True
  Test Limit: 3 cities
  Output Directory: output_pdfs/ecode360

[1/3] Processing Albany County, NY...
  ✅ Found potential ethics section: Chapter 17: Ethics and Financial Disclosure
  📝 Extracted 79 content elements
  ✅ PDF generated: output_pdfs/ecode360\Albany_County_NY_Ethics_Code.pdf

[2/3] Processing Cayuga County, NY...
...
```

## 🎯 Common Commands

### Test with Different Limits

```powershell
# Process just 1 city
venv/Scripts/python.exe main_360.py --test --test-limit 1

# Process 10 cities
venv/Scripts/python.exe main_360.py --test --test-limit 10
```

### Add More States

```powershell
# Edit config.py and change:
ECODE360_STATES = ["NY", "CA", "TX"]

# Then run:
venv/Scripts/python.exe main_360.py --recollect
```

### View Generated PDFs

```powershell
# List all PDFs
Get-ChildItem "output_pdfs/ecode360" -File

# Open output folder
explorer output_pdfs\ecode360
```

## ⚠️ Troubleshooting

### "Verify you are human" Page Appears

**This is Cloudflare protection.**

- ✅ **Solution:** The browser will stay open - just wait or click if needed
- ✅ The scraper is running in headed mode to handle this
- ✅ Most requests will go through automatically

### No Content Extracted

```powershell
# Check debug files:
Get-Content debug_section_*.html | Select-Object -First 50

# Try with a longer delay:
# Edit ecode360_parser.py and increase time.sleep() values
```

### Browser Won't Close

- This is normal during scraping
- Browser closes automatically when done
- Press Ctrl+C to stop early if needed

## 📝 Check Your Results

### View Statistics

The scraper shows a summary at the end:

```
======================================================================
SCRAPING SUMMARY
======================================================================
Total municipalities: 712
Processed: 3
Ethics codes found: 2
Errors: 1
Output directory: output_pdfs/ecode360
======================================================================
```

### Examine PDFs

```powershell
# Open a PDF
Start-Process "output_pdfs\ecode360\Albany_County_NY_Ethics_Code.pdf"
```

## 🔄 Update City List

If new municipalities are added to General Code's library:

```powershell
# Force recollection from website
venv/Scripts/python.exe main_360.py --recollect

# Then run normal scrape
venv/Scripts/python.exe main_360.py --test --test-limit 5
```

## 💡 Tips for Best Results

1. **Start Small:** Always use `--test` mode first
2. **Check PDFs:** Review a few PDFs to ensure quality
3. **Monitor Browser:** Watch the browser window for blocks
4. **Be Patient:** Some pages may take 10-15 seconds to load
5. **Off-Peak Hours:** Run during off-peak hours to avoid rate limits

## 🎓 Example Session

```powershell
# Activate environment
& "D:\DNH Code Scraper\venv\Scripts\Activate.ps1"

# Quick test
venv/Scripts/python.exe main_360.py --test --test-limit 2

# Review results
explorer output_pdfs\ecode360

# If good, run more
venv/Scripts/python.exe main_360.py --test --test-limit 10

# Eventually, full run
venv/Scripts/python.exe main_360.py
```

## 📚 More Information

- **Full Documentation:** See [README_ECODE360.md](README_ECODE360.md)
- **Project Summary:** See [ECODE360_SUMMARY.md](ECODE360_SUMMARY.md)
- **Configuration:** Edit [config.py](config.py)

## ✅ Success Criteria

You'll know it's working when you see:

- ✅ Browser window opens automatically
- ✅ Pages load showing ecode360.com
- ✅ Progress messages in terminal
- ✅ PDF files created in `output_pdfs/ecode360/`
- ✅ Summary shows "Ethics codes found: X" where X > 0

## 🆘 Need Help?

1. Check [README_ECODE360.md](README_ECODE360.md) - Troubleshooting section
2. Review debug HTML files
3. Check [ECODE360_SUMMARY.md](ECODE360_SUMMARY.md) - Known Issues section

---

**Ready to go! Run the test command above to start.** 🚀
