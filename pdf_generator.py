"""PDF generator - converts HTML content to PDF with formatting."""

import os
from playwright.sync_api import sync_playwright
from datetime import datetime
from typing import List, Dict, Optional
import config
import re
import html


class PDFGenerator:
    """Generate PDFs from HTML content with preserved formatting."""
    
    def __init__(self, output_dir: str = config.OUTPUT_DIR):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def sanitize_filename(self, text: str) -> str:
        """Clean text for use in filename."""
        # Remove invalid filename characters
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        # Replace spaces with underscores
        text = text.replace(' ', '_')
        # Limit length
        text = text[:100]
        return text
    
    def format_section_content(self, raw: str) -> str:
        """
        Convert scraped plain-text-ish code content into readable HTML:
        - Paragraphs
        - Hanging indents for A./B./1./(a) style items
        - Definition blocks (ALL CAPS term followed by its definition)
        - Preserve § references as bold tokens
        """
        if not raw:
            return ""

        # Normalize newlines
        text = raw.replace("\r\n", "\n").replace("\r", "\n").strip()

        # Escape any HTML to avoid broken markup / injection
        text = html.escape(text)

        lines = [ln.strip() for ln in text.split("\n")]

        out = []
        i = 0

        # Helpers
        def is_caps_term(s: str) -> bool:
            # e.g., CLERK / COMMITTEE / EMPLOYEE
            return bool(re.fullmatch(r"[A-Z][A-Z0-9 \-]{2,}", s or ""))

        def is_marker(s: str) -> Optional[str]:
            # A. / B. / 1. / 1A. / 7A. etc.
            m = re.fullmatch(r"([A-Z]|\d{1,3}[A-Z]?)\.", s)
            return m.group(1) if m else None

        def is_section_symbol(s: str) -> bool:
            return bool(re.match(r"^§\s*\d", s))

        while i < len(lines):
            ln = lines[i]
            if not ln:
                i += 1
                continue

            # Join stray "§ 54-3" line with its title line ("Declaration of policy.")
            if is_section_symbol(ln) and i + 1 < len(lines) and lines[i + 1] and not is_section_symbol(lines[i + 1]):
                sec = ln
                title = lines[i + 1]
                out.append(f'<div class="sec-head"><span class="sec-symbol">{sec}</span> {title}</div>')
                i += 2
                continue

            # Definition term (ALL CAPS) followed by one+ definition lines until next caps-term/marker/§/blank
            if is_caps_term(ln):
                term = ln
                i += 1
                defs = []
                while i < len(lines):
                    nxt = lines[i]
                    if (not nxt) or is_caps_term(nxt) or is_section_symbol(nxt) or is_marker(nxt):
                        break
                    defs.append(nxt)
                    i += 1
                definition = " ".join(defs).strip()
                if definition:
                    out.append(f'<div class="def"><div class="def-term">{term}</div><div class="def-text">{definition}</div></div>')
                else:
                    out.append(f'<div class="def"><div class="def-term">{term}</div></div>')
                continue

            # Hanging-indent list item marker line by itself: "A." then the next line(s)
            mark = is_marker(ln)
            if mark:
                i += 1
                parts = []
                while i < len(lines):
                    nxt = lines[i]
                    if (not nxt) or is_marker(nxt) or is_caps_term(nxt) or is_section_symbol(nxt):
                        break
                    parts.append(nxt)
                    i += 1
                body = " ".join(parts).strip()
                out.append(f'<div class="li"><span class="li-mark">{mark}.</span><span class="li-body">{body}</span></div>')
                continue

            # Bold § references that appear inline (e.g., "pursuant to § 54-5 of this chapter")
            ln = re.sub(r"(§\s*\d[\w\-\.\(\)]*)", r"<span class='sec-symbol'>\1</span>", ln)

            # Default: normal paragraph
            out.append(f"<p>{ln}</p>")
            i += 1

        return "\n".join(out)

    
    def create_html_document(self, city_name: str, sections: List[Dict], source_url: str) -> str:
        """Create complete HTML document from sections."""
        html_parts = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '  <meta charset="utf-8">',
            f'  <title>{city_name} - Code of Ethics</title>',
            '  <style>',
            '    body {',
            '      font-family: "Times New Roman", Times, serif;',
            '      font-size: 12pt;',
            '      line-height: 1.6;',
            '      margin: 0;',
            '      padding: 0;',
            '      color: #000;',
            '    }',
            '    h1 {',
            '      font-size: 18pt;',
            '      margin-top: 0;',
            '      margin-bottom: 20px;',
            '      color: #003366;',
            '      border-bottom: 2px solid #003366;',
            '      padding-bottom: 10px;',
            '    }',
            '    .metadata {',
            '      font-size: 10pt;',
            '      color: #666;',
            '      margin-bottom: 30px;',
            '      padding: 10px;',
            '      background-color: #f5f5f5;',
            '      border-left: 3px solid #003366;',
            '    }',
            '    .section {',
            '      margin-bottom: 40px;',
            '      page-break-inside: auto;',
            '    }',
            '    .section-title {',
            '      font-weight: bold;',
            '      font-size: 14pt;',
            '      margin-bottom: 15px;',
            '      color: #000;',
            '    }',
                        '    .section-content {',
            '      font-size: 12pt;',
            '      line-height: 1.65;',
            '      color: #000;',
            '      margin: 0;',
            '    }',
            '    .section-content p {',
            '      margin: 0 0 10px 0;',
            '      text-indent: 0.25in;',
            '    }',
            '    .sec-head {',
            '      margin: 14px 0 8px 0;',
            '      font-weight: 700;',
            '      text-indent: 0;',
            '    }',
            '    .sec-symbol {',
            '      font-weight: 700;',
            '      white-space: nowrap;',
            '    }',
            '    .li {',
            '      margin: 0 0 10px 0;',
            '      display: flex;',
            '      gap: 10px;',
            '      align-items: flex-start;',
            '    }',
            '    .li-mark {',
            '      width: 0.35in;',
            '      font-weight: 700;',
            '      flex: 0 0 0.35in;',
            '    }',
            '    .li-body {',
            '      flex: 1;',
            '    }',
            '    .def {',
            '      margin: 8px 0 12px 0;',
            '      padding: 8px 10px;',
            '      border-left: 3px solid #999;',
            '      background: #fafafa;',
            '    }',
            '    .def-term {',
            '      font-weight: 700;',
            '      letter-spacing: 0.02em;',
            '      margin-bottom: 4px;',
            '    }',
            '    .def-text {',
            '      text-indent: 0;',
            '    }',

            '    @page {',
            '      margin: 1in;',
            '    }',
            '  </style>',
            '</head>',
            '<body>',
            f'  <h1>{city_name} - Ethics Code</h1>',
            '  <div class="metadata">',
            f'    <strong>Source:</strong> {source_url}<br>',
            f'    <strong>Retrieved:</strong> {datetime.now().strftime("%B %d, %Y")}<br>',
            f'    <strong>Number of Sections:</strong> {len(sections)}',
            '  </div>',
        ]
        
        # Add each section with clean text
        for section in sections:
            html_parts.append('  <div class="section">')
            
            # Section title
            title = section.get('title', 'Untitled')
            html_parts.append(f'    <div class="section-title">{title}</div>')
            
            # Section content - clean text only
            content = section.get('content', '')
            if content:
                # Clean the content: just plain text, no HTML tags
                formatted = self.format_section_content(content)
                html_parts.append(f'    <div class="section-content">{formatted}</div>')
            
            html_parts.append('  </div>')
        
        html_parts.extend([
            '</body>',
            '</html>'
        ])
        
        return '\n'.join(html_parts)
    
    def generate_pdf(self, city_name: str, state: str, sections: List[Dict], 
                    source_url: str) -> Optional[str]:
        """
        Generate a PDF from sections.
        
        Args:
            city_name: Name of the city
            state: State abbreviation
            sections: List of section dictionaries
            source_url: Original source URL
            
        Returns:
            Path to generated PDF or None if failed
        """
        try:
            # Create filename
            safe_city = self.sanitize_filename(city_name)
            safe_state = self.sanitize_filename(state) if state else 'Unknown'
            filename = f"{safe_city}_{safe_state}_Ethics_Code.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            # Create HTML document
            html_content = self.create_html_document(city_name, sections, source_url)
            
            # Generate PDF using Playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_content(html_content)
                page.pdf(
                    path=filepath,
                    format='Letter',
                    print_background=True,
                    display_header_footer=True,
                    header_template=(
                        "<div style='font-size:9px;width:100%;text-align:right;"
                        "padding-right:24px;color:#666;'>"
                        f"{html.escape(city_name)} — Ethics Code"
                        "</div>"
                    ),
                    footer_template=(
                        "<div style='font-size:9px;width:100%;text-align:center;color:#666;'>"
                        "Page <span class='pageNumber'></span> of <span class='totalPages'></span>"
                        "</div>"
                    ),
                    margin={
                        'top': '0.75in',
                        'right': '0.75in',
                        'bottom': '0.75in',
                        'left': '0.75in'
                    }
                )
                browser.close()
            
            print(f"  📄 Generated PDF: {filename}")
            return filepath
            
        except Exception as e:
            print(f"  ❌ Error generating PDF for {city_name}: {e}")
            return None


if __name__ == '__main__':
    # Test PDF generation
    generator = PDFGenerator()
    
    test_sections = [
        {
            'title': 'Code of Ethics - General Provisions',
            'content': '<p>All municipal officers and employees shall conduct themselves in a manner that reflects positively on the city...</p>'
        },
        {
            'title': 'Conflicts of Interest',
            'content': '<p>No officer or employee shall engage in any activity that creates a conflict of interest...</p>'
        }
    ]
    
    pdf_path = generator.generate_pdf(
        city_name='Test City',
        state='UT',
        sections=test_sections,
        source_url='https://example.com/municode'
    )
    
    if pdf_path:
        print(f"\n✅ Test PDF created: {pdf_path}")
    else:
        print("\n❌ Test PDF generation failed")
