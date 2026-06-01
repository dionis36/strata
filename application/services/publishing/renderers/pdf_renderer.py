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

        import markdown
        html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
        
        minimal_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Technical Assessment</title>
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """
        
        # Override with print styles (white background, black text, etc.)
        print_css = CSS(string='''
            body { background-color: white !important; color: black !important; font-size: 10pt; font-family: Arial, sans-serif; padding: 0; }
            h1, h2, h3 { color: #333 !important; border-bottom: 1px solid #eee; padding-bottom: 5px; }
            a { color: #0056b3 !important; text-decoration: none !important; }
            @page { margin: 2cm; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 2rem; }
            th, td { padding: 0.5rem; text-align: left; border-bottom: 1px solid #ccc; }
            th { background-color: #f8f9fa; font-weight: bold; }
            pre { background-color: #f1f5f9; padding: 1rem; border-radius: 5px; overflow-x: auto; font-size: 8pt; white-space: pre-wrap; }
            code { font-family: monospace; background-color: #f1f5f9; padding: 2px 4px; border-radius: 3px; }
            pre code { padding: 0; background-color: transparent; }
            /* Hide mermaid source text in PDF since JS won't run */
            pre.mermaid { display: none; }
            pre code.language-mermaid { display: none; }
        ''')
        
        try:
            HTML(string=minimal_html).write_pdf(output_path, stylesheets=[print_css])
            return output_path
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return ""
