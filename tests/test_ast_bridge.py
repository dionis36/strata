import os
import unittest
from infrastructure.parser_bridge import ParserBridge
from domain.models.edge import EdgeType
from domain.models.node import NodeType
from domain.utils.id_generator import generate_deterministic_id

class TestASTBridge(unittest.TestCase):
    def setUp(self):
        self.bridge = ParserBridge()
        self.fixture_path = os.path.abspath("tests/fixtures/kitchen_sink.php")
        self.root_path = os.path.abspath(".")

    def test_kitchen_sink_extraction(self):
        """Verify that the AST bridge correctly extracts complex PHP structures."""
        if not os.path.exists(self.fixture_path):
            self.skipTest("Fixture not found")

        nodes, edges = self.bridge.parse_files([self.fixture_path], root_path=self.root_path)

        # --- Node Assertions ---
        # We check FQNs now because IDs are hashed
        fqns = [n.fqn for n in nodes]
        
        # Verify FQN resolution
        self.assertIn("Core\\Database\\BaseRepository", fqns)
        self.assertIn("App\\Services\\UserService", fqns)
        self.assertIn("App\\Services\\AuthManager", fqns)
        
        # Verify method extraction for UserService
        user_service = next(n for n in nodes if n.fqn == "App\\Services\\UserService")
        self.assertIn("find", user_service.methods)
        self.assertIn("__construct", user_service.methods)

        # --- Edge Assertions ---
        
        # Generate expected hashed IDs
        user_svc_id = generate_deterministic_id("App\\Services\\UserService", NodeType.CLASS.value)
        base_repo_id = generate_deterministic_id("Core\\Database\\BaseRepository", NodeType.CLASS.value)
        logger_id = generate_deterministic_id("App\\Log\\Logger", NodeType.CLASS.value)
        std_class_id = generate_deterministic_id("stdClass", NodeType.CLASS.value)

        # Inheritance: UserService -> BaseRepository
        inheritance = next((e for e in edges if e.source_id == user_svc_id 
                           and e.target_id == base_repo_id 
                           and e.edge_type == EdgeType.INHERITS), None)
        self.assertIsNotNone(inheritance, "UserService should inherit from BaseRepository")

        # Call: UserService -> App\Log\Logger (Static Call)
        static_call = next((e for e in edges if e.source_id == user_svc_id 
                           and e.target_id == logger_id 
                           and e.edge_type == EdgeType.CALLS), None)
        self.assertIsNotNone(static_call, "UserService should have a call to Logger")

        # Call: UserService -> stdClass (Instantiation)
        instantiation = next((e for e in edges if e.source_id == user_svc_id 
                             and e.target_id == std_class_id 
                             and e.edge_type == EdgeType.CALLS), None)
        self.assertIsNotNone(instantiation, "UserService should have a call to stdClass")

if __name__ == "__main__":
    unittest.main()
