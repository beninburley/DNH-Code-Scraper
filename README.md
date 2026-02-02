# Municipal Ethics Code Scraper

A web scraper that collects municipal codes of ethics from BYU's state and local government repository.

## Features

- Scrapes all state ranges (A-H, I-P, Q-Z) from BYU's repository
- Focuses on Municode format initially
- Searches for ethics/conduct code variations
- Generates PDFs preserving original formatting
- Respects rate limiting and scraper policies

## Setup

1. Create virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Install Playwright browsers (for JavaScript-rendered sites):

```powershell
playwright install
```

## Usage

Run the scraper:

```powershell
python main.py
```

Output PDFs will be saved to `output_pdfs/` directory.

## Configuration

Edit `config.py` to adjust:

- Request delays
- Search terms
- Test mode settings
- Output directory

## Test Mode

By default, the scraper runs in test mode (processes only 5 cities).
To run full scraper, set `TEST_MODE = False` in `config.py`.
