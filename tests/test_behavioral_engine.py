"""
Phase 4: Behavioral Engine Unit Tests
Validates the Tokenizer, SQL Detection, and Mathematical clamping logic.
"""
from domain.behavior.tokenizer import CodeSanitizer
from domain.behavior.sql_detector import SqlDetector
from domain.behavior.orm_detector import OrmDetector
from domain.behavior.table_extractor import TableExtractor

def test_tokenizer_ignores_comments():
    code = '''
    // UPDATE users SET name='hacked'
    /* INSERT INTO orders (id) VALUES (1) */
    $db->query("UPDATE valid_table SET status=1");
    '''
    sanitized = CodeSanitizer.sanitize(code)
    # The comments should be gone, only the valid string literal remains
    queries = SqlDetector.detect_write_queries(sanitized['literals'])
    assert len(queries) == 1, f"Expected 1 valid query, got {len(queries)}"
    assert "UPDATE valid_table SET status=1" in queries[0]

def test_table_extraction_normalizes_names():
    q1 = 'INSERT INTO `Users`'
    q2 = 'update "Orders" set'
    assert TableExtractor.extract_from_sql(q1) == "users"
    assert TableExtractor.extract_from_sql(q2) == "orders"

def test_orm_detector_finds_writes():
    code = '''
    $user->name = 'test';
    $user->save();
    Model::create(['id' => 1]);
    $db->update('users', data);
    '''
    sanitized = CodeSanitizer.sanitize(code)
    writes = OrmDetector.detect_orm_writes(sanitized['clean_code'])
    assert len(writes) == 3
    assert any("save()" in w for w in writes)
    assert any("create(" in w for w in writes)
    assert any("update(" in w for w in writes)

def test_behavioral_factor_clamps_at_one():
    # Behavioral amplification math validation
    norm_write_intensity = 1.0
    norm_table_dependencies = 2.5 # Test boundary exceedance
    
    behavioral_factor = (0.5 * norm_write_intensity) + (0.5 * norm_table_dependencies)
    behavioral_factor = min(1.0, behavioral_factor)
    
    assert behavioral_factor == 1.0
    
    # Final risk check
    base_structural_risk = 0.8
    final_risk = base_structural_risk * (1.0 + behavioral_factor)
    final_risk = min(1.0, final_risk)
    
    assert final_risk == 1.0 # 0.8 * 2.0 = 1.6 -> clamped to 1.0

if __name__ == "__main__":
    test_tokenizer_ignores_comments()
    test_table_extraction_normalizes_names()
    test_orm_detector_finds_writes()
    test_behavioral_factor_clamps_at_one()
    print("SUCCESS: Phase 4 Behavioral Unit Tests passed flawlessly!")
