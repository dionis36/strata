import os
import json
import tempfile
import pytest
from application.services.advisory_service import AdvisoryService

def test_autoload_mappings_resolver():
    # 1. Prepare temporary directory and serialized graph data
    with tempfile.TemporaryDirectory() as tmpdir:
        advisory_service = AdvisoryService(data_dir=tmpdir)
        
        # Define mock nodes
        nodes = [
            # File nodes
            {
                "id": "file::src/Controller/UserController.php",
                "fqn": "/data/my_project/src/Controller/UserController.php",
                "type": "file",
                "file_path": "/data/my_project/src/Controller/UserController.php"
            },
            {
                "id": "file::src/Model/User.php",
                "fqn": "/data/my_project/src/Model/User.php",
                "type": "file",
                "file_path": "/data/my_project/src/Model/User.php"
            },
            {
                "id": "file::lib/Vendor/Utility.php",
                "fqn": "/data/my_project/lib/Vendor/Utility.php",
                "type": "file",
                "file_path": "/data/my_project/lib/Vendor/Utility.php"
            },
            # Class nodes
            {
                "id": "class::App\\Controller\\UserController",
                "fqn": "App\\Controller\\UserController",
                "name": "UserController",
                "type": "class",
                "file_path": "/data/my_project/src/Controller/UserController.php"
            },
            {
                "id": "class::App\\Model\\User",
                "fqn": "App\\Model\\User",
                "name": "User",
                "type": "class",
                "file_path": "/data/my_project/src/Model/User.php"
            },
            {
                "id": "class::External\\Utility",
                "fqn": "External\\Utility",
                "name": "Utility",
                "type": "class",
                "file_path": "/data/my_project/lib/Vendor/Utility.php"
            }
        ]
        
        # Serialize graph
        graph_data = {
            "nodes": nodes,
            "links": []
        }
        
        run_id = 42
        graph_path = os.path.join(tmpdir, f"graph_{run_id}.json")
        with open(graph_path, "w") as f:
            json.dump(graph_data, f)
            
        # 2. Run resolver
        result = advisory_service.get_autoload_mappings(run_id)
        
        # 3. Assertions
        assert "psr-4" in result
        psr4 = result["psr-4"]
        
        # Expect:
        # App\Controller\UserController in src/Controller/UserController.php -> matching Controller, App vs src -> App\ maps to src/
        # App\Model\User in src/Model/User.php -> App\ maps to src/
        # External\Utility in lib/Vendor/Utility.php -> External\ maps to lib/Vendor/
        assert psr4.get("App\\") == "src/"
        assert psr4.get("External\\") == "lib/Vendor/"
        assert result["project_root"] == "/data/my_project"

if __name__ == "__main__":
    pytest.main([__file__])
