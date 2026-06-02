from application.services.publishing.models import CanonicalModel

class RectorGenerator:
    """Deterministically generates rector.php configuration based on CanonicalModel metrics."""
    
    def generate(self, model: CanonicalModel) -> str:
        framework = model.system_context.framework.lower()
        rules = [
            "LevelSetList::UP_TO_PHP_82",
            "SetList::DEAD_CODE",
            "SetList::CODE_QUALITY"
        ]
        
        # Add framework specific rules
        if "symfony" in framework:
            rules.append("SymfonySetList::SYMFONY_60")
        elif "laravel" in framework:
            rules.append("LaravelSetList::LARAVEL_100")
            
        # Add rules based on findings
        has_mysql_query = any("mysql_" in str(f.observation).lower() for f in model.findings)
        if has_mysql_query:
            rules.append("SetList::MYSQL_TO_MYSQLI")

        rules_str = ",\n        ".join(rules)
        
        return f"""<?php

declare(strict_types=1);

use Rector\\Config\\RectorConfig;
use Rector\\Set\\ValueObject\\LevelSetList;
use Rector\\Set\\ValueObject\\SetList;

return static function (RectorConfig $rectorConfig): void {{
    $rectorConfig->paths([
        __DIR__ . '/src',
        __DIR__ . '/app',
    ]);

    // Define rules deterministically based on Strata static analysis
    $rectorConfig->sets([
        {rules_str}
    ]);
}};
"""
