import os
from domain.models.node import NodeType

class FileClassifier:
    @staticmethod
    def classify(path: str, root_path: str) -> NodeType:
        filename = os.path.basename(path).lower()
        rel_path = os.path.relpath(path, root_path).lower()
        ext = os.path.splitext(filename)[1]

        # 1. Vendor/Library Check (Priority)
        vendor_markers = ["vendor/", "lib/", "3rdparty/", "externals/"]
        if any(marker in rel_path for marker in vendor_markers):
            return NodeType.VENDOR

        # 2. Config Detection
        config_exts = [".json", ".xml", ".yml", ".yaml", ".ini", ".env"]
        config_names = ["config.php", "settings.php", "constants.php", ".htaccess"]
        if ext in config_exts or filename in config_names or "config" in rel_path:
            return NodeType.CONFIG

        # 3. View/Template Detection
        view_exts = [".tpl", ".twig", ".blade.php", ".html", ".htm"]
        view_dirs = ["templates/", "views/", "themes/", "layouts/"]
        if ext in view_exts or any(vdir in rel_path for vdir in view_dirs):
            return NodeType.VIEW

        # 4. Entry Point Detection
        # Root level PHP files that are typical entry points
        entry_names = ["index.php", "main.php", "api.php", "router.php"]
        if rel_path.count(os.sep) == 0 and filename in entry_names:
            return NodeType.ENTRY_POINT

        # 5. Bootstrap Detection
        bootstrap_markers = ["bootstrap.php", "init.php", "autoload.php", "setup.php"]
        if filename in bootstrap_markers or "bootstrap" in rel_path:
            return NodeType.BOOTSTRAP

        # 6. Controller Detection
        if filename.endswith("controller.php") or filename.endswith("handler.php"):
            return NodeType.CONTROLLER

        # 7. Job/Cron Detection
        job_dirs = ["cron/", "jobs/", "tasks/", "bin/", "scripts/"]
        if any(jdir in rel_path for jdir in job_dirs):
            return NodeType.JOB

        # 8. Asset Detection
        asset_exts = [".css", ".js", ".sql", ".map"]
        if ext in asset_exts or "assets/" in rel_path or "public/" in rel_path:
            if ext in [".css", ".js", ".sql"]:
                return NodeType.ASSET

        # Default to generic FILE
        return NodeType.FILE
