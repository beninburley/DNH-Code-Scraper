"""PDF generator - converts HTML content to PDF with formatting."""

import os
from playwright.sync_api import sync_playwright
from datetime import datetime
from typing import List, Dict, Optional
import config
import re


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
            '      margin: 1in;',
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
            '      page-break-inside: avoid;',
            '    }',
            '    .section-title {',
            '      font-weight: bold;',
            '      font-size: 14pt;',
            '      margin-bottom: 15px;',
            '      color: #000;',
            '    }',
            '    .section-content {',
            '      font-size: 12pt;',
            '      line-height: 1.8;',
            '      color: #000;',
            '      white-space: pre-wrap;',
            '    }',
            '    @page {',
            '      margin: 0.75in;',
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
                html_parts.append(f'    <div class="section-content">{content}</div>')
            
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
