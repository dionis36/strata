import markdown

class HtmlRenderer:
    def render(self, md_content: str) -> str:
        html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
        
        full_html = f"""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>Strata Modernization Assessment</title>
    <script src='https://cdn.tailwindcss.com'></script>
    <script type='module'>
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
    </script>
    <link href='https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap' rel='stylesheet'>
    <style>
        body {{ font-family: 'Inter', sans-serif; background-color: #0f111a; color: #e2e8f0; line-height: 1.6; padding: 40px; }}
        h1, h2, h3 {{ color: #38bdf8; margin-top: 2rem; margin-bottom: 1rem; }}
        h1 {{ font-size: 2.5rem; font-weight: bold; border-bottom: 2px solid #334155; padding-bottom: 0.5rem; }}
        h2 {{ font-size: 1.8rem; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; }}
        h3 {{ font-size: 1.3rem; color: #fbbf24; }}
        ul, ol {{ margin-bottom: 1rem; padding-left: 1.5rem; }}
        li {{ margin-bottom: 0.5rem; }}
        p {{ margin-bottom: 1rem; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 2rem; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ background-color: #1e293b; color: #94a3b8; font-size: 0.875rem; text-transform: uppercase; }}
        code {{ background-color: #1e293b; padding: 0.2rem 0.4rem; border-radius: 0.25rem; font-family: monospace; }}
        pre code {{ background-color: transparent; padding: 0; }}
        pre {{ background-color: #1e293b; padding: 1rem; border-radius: 0.5rem; overflow-x: auto; margin-bottom: 1.5rem; }}
    </style>
</head>
<body class='max-w-6xl mx-auto'>
    {html_body}
</body>
</html>"""
        return full_html
