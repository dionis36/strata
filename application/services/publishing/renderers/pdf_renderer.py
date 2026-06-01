import logging
from application.services.publishing.renderers.html_renderer import HtmlRenderer

logger = logging.getLogger(__name__)

class PdfRenderer:
    def render(self, md_content: str, output_path: str) -> str:
        try:
            from weasyprint import HTML, CSS
        except ImportError:
            logger.error("WeasyPrint is not installed. PDF generation failed.")
            return ""

        # First convert to HTML, but we need print-friendly CSS instead of dark mode
        html_renderer = HtmlRenderer()
        html_content = html_renderer.render(md_content)
        
        # Override with print styles (white background, black text, etc.)
        print_css = CSS(string='''
            body { background-color: white !important; color: black !important; font-size: 12pt; padding: 0; }
            h1, h2, h3 { color: #333 !important; }
            a { color: #000 !important; text-decoration: none !important; }
            @page { margin: 2cm; }
            /* Hide mermaid source text in PDF since JS won't run */
            pre.mermaid { display: none; }
        ''')
        
        try:
            # Note: Javascript won't execute in WeasyPrint.
            # Mermaid diagrams will either need pre-rendering or will just be hidden/shown as raw text.
            # We hide the raw mermaid code block via CSS above to keep the document clean.
            HTML(string=html_content).write_pdf(output_path, stylesheets=[print_css])
            return output_path
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return ""
