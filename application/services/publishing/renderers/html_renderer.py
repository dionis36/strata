import os
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
from application.services.publishing.models import CanonicalModel

class HtmlRenderer:
    def __init__(self):
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def render(self, model: CanonicalModel, run_id: int) -> str:
        template = self.env.get_template('index.html.j2')
        
        # We dump the model to JSON so the frontend JS can use the data directly if needed
        model_json = model.model_dump_json()
        
        import datetime
        current_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        return template.render(
            model=model,
            run_id=run_id,
            model_json=model_json,
            current_date=current_date
        )
