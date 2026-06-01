import os
from jinja2 import Environment, FileSystemLoader
from application.services.publishing.models import CanonicalModel

class MarkdownRenderer:
    def __init__(self):
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.env = Environment(
            loader=FileSystemLoader(template_dir)
        )

    def render(self, model: CanonicalModel, run_id: int) -> str:
        template = self.env.get_template('master_report.md.j2')
        return template.render(
            model=model,
            run_id=run_id
        )
