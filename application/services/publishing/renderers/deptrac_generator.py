from application.services.publishing.models import CanonicalModel

class DeptracGenerator:
    """Deterministically generates deptrac.yaml configuration based on CanonicalModel metrics."""
    
    def generate(self, model: CanonicalModel) -> str:
        if not model.layered_architecture or not model.layered_architecture.bounded_contexts:
            return "# No layered architecture bounds identified.\n"

        layers = []
        ruleset = []
        
        for ctx in model.layered_architecture.bounded_contexts:
            layer_name = ctx.name.replace(" ", "_").replace("/", "_").replace(":", "").lower()
            layers.append(f"  - name: {layer_name}\n    collectors:\n      - type: className\n        regex: .*{layer_name}.*")
            
            # Simple rule: allow external calls only to generic/utils layers, restrict others
            ruleset.append(f"  {layer_name}:")
            if ctx.external_calls > 0:
                ruleset.append(f"    - Global_Utils")
                
        layers_str = "\n".join(layers)
        ruleset_str = "\n".join(ruleset)

        return f"""parameters:
  paths:
    - ./src
    - ./app
  layers:
{layers_str}
  ruleset:
{ruleset_str}
"""
