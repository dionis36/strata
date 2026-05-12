"""
Requirement 8: Modernization Score Model
Calculates the multi-dimensional modernization score based on FINAL.md specifications.
"""

class ModernizationModel:
    @staticmethod
    def calculate(stats: dict) -> dict:
        """
        Calculates scores for 7 dimensions.
        Stats should contain:
            - namespace_ratio (0-1)
            - legacy_db_ratio (0-1)
            - security_risk_count (int)
            - coupling_density (0-1)
            - has_composer (bool)
            - has_tests (bool)
        """
        
        # 1. Version Compatibility (Base 20)
        # Assuming if has composer and namespaces, it's fairly modern
        version_score = 10 if stats.get('has_composer') else 5
        version_score += 10 if stats.get('namespace_ratio', 0) > 0.5 else 0
        
        # 2. Namespace Adoption (Base 10)
        namespace_score = stats.get('namespace_ratio', 0.0) * 10
        
        # 3. DB Layer Quality (Base 15)
        # legacy_db_ratio is percentage of mysql_* calls vs modern PDO/mysqli/ORM
        db_layer_score = (1.0 - stats.get('legacy_db_ratio', 0.0)) * 15
        
        # 4. Security Risk (Base 20)
        # Deduction based on dangerous pattern count
        security_score = max(0, 20 - (stats.get('security_risk_count', 0) * 2))
        
        # 5. Framework Alignment (Base 10)
        # Heuristic: has composer + recognized structure
        framework_score = 10 if stats.get('has_composer') else 2
        
        # 6. Testability (Base 10)
        testability_score = 10 if stats.get('has_tests') else 0
        
        # 7. Coupling (Base 15)
        coupling_score = (1.0 - stats.get('coupling_density', 0.0)) * 15
        
        total = (version_score + namespace_score + db_layer_score + 
                 security_score + framework_score + testability_score + coupling_score)
        
        return {
            "version_score": round(version_score, 2),
            "namespace_score": round(namespace_score, 2),
            "db_layer_score": round(db_layer_score, 2),
            "security_score": round(security_score, 2),
            "framework_score": round(framework_score, 2),
            "testability_score": round(testability_score, 2),
            "coupling_score": round(coupling_score, 2),
            "total_modernization_score": round(total, 2)
        }
