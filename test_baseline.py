from ghost_query.environment.baseline_runner import BaselineRunner
from ghost_query.environment.project_summary import ProjectSummaryBuilder
from ghost_query.environment.engine import DBEngine

def test_baseline_logic():
    print("--- Testing Baseline Logic ---")
    
    # Initialize engine
    engine = DBEngine()
    
    # 1. Run Baseline
    runner = BaselineRunner(engine)
    baseline_data = runner.run_baseline()
    
    print("\n--- Raw Baseline Data ---")
    print(baseline_data)
    
    # 2. Build Summary
    builder = ProjectSummaryBuilder()
    summary = builder.build_summary(baseline_data)
    
    print("\n--- LLM-Readable Summary ---")
    print(summary)
    
    # Simple assertions
    assert "runtime_ms" in baseline_data
    assert "sales" in baseline_data["tables"]
    assert "No anomalies detected." in summary
    
    print("\n✅ Baseline verification successful!")
    engine.close()

if __name__ == "__main__":
    test_baseline_logic()
