"""
Reset Manager

This module will be responsible for bringing the environment (workspace) back to a clean state by copying from baseline.
"""
import os
import shutil
import json
import time
from typing import Optional, Dict, Any

class ResetManager:
    def __init__(self):
        # Resolve base directories dynamically relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(current_dir)
        
        self.baseline_dir = os.path.join(self.base_dir, "baseline")
        self.workspace_dir = os.path.join(self.base_dir, "workspace")
        self.metadata_dir = os.path.join(self.base_dir, "metadata")
        
        # Specific baseline paths
        self.baseline_data = os.path.join(self.baseline_dir, "data")
        self.baseline_dbt = os.path.join(self.baseline_dir, "dbt_project_snapshot")
        
        # Specific workspace paths
        self.workspace_data = os.path.join(self.workspace_dir, "data")
        self.workspace_dbt = os.path.join(self.workspace_dir, "dbt_project")
        self.workspace_duckdb = os.path.join(self.workspace_dir, "duckdb")

    def reset_workspace(self, seed: Optional[int] = None) -> Dict[str, Any]:
        print("[RESET] Clearing workspace")
        self._clear_workspace()
        
        print("[RESET] Copying baseline data")
        self._copy_baseline_data()
        
        print("[RESET] Copying dbt project")
        self._copy_baseline_dbt_project()
        
        if seed is not None:
            self._log_seed(seed)
            
        print("[RESET] Done")
        
        # Calculate copied files
        files_copied = 0
        for directory in [self.workspace_data, self.workspace_dbt]:
            if os.path.exists(directory):
                for base, dirs, files in os.walk(directory):
                    files_copied += len(files)
                    
        return {
            "status": "success",
            "files_copied": files_copied,
            "seed": seed
        }

    def _clear_workspace(self):
        for directory in [self.workspace_data, self.workspace_dbt, self.workspace_duckdb]:
            if os.path.exists(directory):
                shutil.rmtree(directory)
            os.makedirs(directory, exist_ok=True)

    def _copy_baseline_data(self):
        if not os.path.exists(self.baseline_data):
            raise FileNotFoundError(f"Baseline data directory missing: {self.baseline_data}")
        
        shutil.copytree(self.baseline_data, self.workspace_data, dirs_exist_ok=True)

    def _copy_baseline_dbt_project(self):
        if not os.path.exists(self.baseline_dbt):
            raise FileNotFoundError(f"Baseline dbt project missing: {self.baseline_dbt}")
            
        shutil.copytree(self.baseline_dbt, self.workspace_dbt, dirs_exist_ok=True)
        
    def _log_seed(self, seed: int):
        log_dir = os.path.join(self.metadata_dir, "round_logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, "reset_log.json")
        log_entry = {
            "timestamp": time.time(),
            "seed": seed
        }
        
        logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            except json.JSONDecodeError:
                pass
                
        logs.append(log_entry)
        
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=4)
