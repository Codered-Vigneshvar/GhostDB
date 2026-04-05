import os
from ghost_query.environment.reset_manager import ResetManager

def test_reset():
    manager = ResetManager()
    
    print("Testing ResetManager...")
    result = manager.reset_workspace(seed=42)
    
    print(f"\nResult: {result}")
    
    # Verify outputs
    workspace_data = manager.workspace_data
    workspace_dbt = manager.workspace_dbt
    
    if os.path.exists(workspace_data) and os.listdir(workspace_data):
        print(f"✅ Data copied successfully to {workspace_data}")
    else:
        print("❌ Data copy failed!")
        
    if os.path.exists(workspace_dbt) and os.listdir(workspace_dbt):
        print(f"✅ DBT project copied successfully to {workspace_dbt}")
    else:
        print("❌ DBT copy failed!")

if __name__ == "__main__":
    test_reset()
