import os
import glob
import json
import time
import builtins
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

import groq
from ghost_query.environment.sql_env import SQLEnv
from ghost_query.models import SQLAction

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(AGENT_DIR)
TASKS_DIR = os.path.join(BASE_DIR, "tasks")
AGENT_CODE_DIR = os.path.join(AGENT_DIR, "AgentCode")

if not os.path.exists(AGENT_CODE_DIR):
    os.makedirs(AGENT_CODE_DIR)

def get_system_prompt() -> str:
    prompt_path = os.path.join(AGENT_DIR, "system_prompt.txt")
    with open(prompt_path, "r") as f:
        return f.read()

client = None

def setup_llm():
    global client
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY environment variable not set. Please add it to your .env file.")
        exit(1)
    client = groq.Groq(api_key=api_key)

def select_tasks() -> List[str]:
    print("─── PHASE 0: FILE SELECTION ────────────────────────────────────\n")
    task_files = sorted([os.path.basename(f) for f in glob.glob(os.path.join(TASKS_DIR, "*.sql"))])
    if not task_files:
        print("No SQL tasks found in /tasks.")
        exit(1)
        
    while True:
        print("Available SQL tasks:")
        print("[0] Run ALL files")
        for i, task in enumerate(task_files, start=1):
            print(f"[{i}] {task}")
            
        choice = input("\nEnter number(s) to run (e.g. 1  or  1,3  or  0 for all): ").strip()
        
        if choice == "0":
            selected = task_files
            break
        
        try:
            indices = [int(x.strip()) for x in choice.split(',')]
            selected = []
            valid = True
            for idx in indices:
                if 1 <= idx <= len(task_files):
                    selected.append(task_files[idx-1])
                else:
                    valid = False
            if valid and selected:
                break
        except:
            pass
        
        print("Invalid choice, try again.\n")
        
    print(f"\nRunning: {', '.join(selected)}")
    return selected

def check_environment():
    print("\n─── PHASE 1: STARTUP ───────────────────────────────────────────")
    try:
        env = SQLEnv()
        obs, state, info = env.reset()
        env.engine.close()
        print("Environment reachable and initialized successfully.")
    except Exception as e:
        print(f"Environment unreachable: {e}")
        exit(1)

def get_schema(env: SQLEnv) -> str:
    tables = env.engine.execute("SHOW TABLES").fetchall()
    schema_str = ""
    for t in tables:
        table_name = t[0]
        schema_str += f"Table: {table_name}\n"
        cols = env.engine.execute(f"DESCRIBE {table_name}").fetchall()
        for c in cols:
            schema_str += f"  - {c[0]} ({c[1]})\n"
    return schema_str

def process_task(task_file: str) -> Dict[str, Any]:
    task_id = os.path.splitext(task_file)[0]
    
    # ─── PHASE 2: BASELINE RUN
    env = SQLEnv()
    env.reset()
    
    # Force task
    task_path = os.path.join(TASKS_DIR, task_file)
    with open(task_path, 'r') as f:
        env.baseline_query = f.read()
    env.current_task_name = task_file
    
    obs, latency = env._execute_query(env.baseline_query)
    env.baseline_latency_ms = latency
    env.baseline_df = env.engine.execute(env.baseline_query).df()
    baseline_ms = latency
    
    print(f"{task_id} | {baseline_ms:.2f}ms | Baseline Recorded")
    schema_info = get_schema(env)
    
    # ─── PHASE 3, 4, 5: OPTIMISATION LOOP
    
    system_instruction = get_system_prompt()
    
    attempt = 1
    previous_error = None
    final_json = None
    new_ms = baseline_ms
    verdict = "FAILED"
    hash_match = False
    
    while attempt <= 3:
        prompt = f"TASK ID: {task_id}\n\n"
        prompt += f"SCHEMA:\n{schema_info}\n"
        prompt += f"BASELINE LATENCY: {baseline_ms:.2f} ms\n\n"
        prompt += f"ORIGINAL QUERY:\n{env.baseline_query}\n\n"
        prompt += f"QUERY PLAN (Annotate this):\n{obs.query_plan_json}\n\n"
        
        if previous_error:
            prompt += f"PREVIOUS ATTEMPT FAILED. ERROR: {previous_error}\n"
            
        prompt += f"ATTEMPT NUMBER: {attempt} of 3\n"
        
        try:
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            
            action = data.get("action")
            
            if action in ["NO_CHANGE", "ERROR_UNRESOLVED"]:
                verdict = action
                final_json = data
                break
                
            elif action == "OPTIMIZE":
                optimized_sql = data.get("optimized_sql")
                if not optimized_sql:
                    raise ValueError("Optimized SQL missing from response.")
                
                # Write to gn.sql file
                gn_path = os.path.join(AGENT_CODE_DIR, f"{task_id}gn.sql")
                with open(gn_path, "w") as f:
                    f.write(optimized_sql)
                    
                print(f"[{task_id}] EXECUTING OPTIMIZED SQL (Attempt {attempt})...")
                # ─── PHASE 4: RUN AGENT FILES
                action_obj = SQLAction(sql_query=optimized_sql)
                next_obs, reward, terminated, truncated, info = env.step(action_obj)
                
                if not next_obs.is_valid:
                    previous_error = info.get("reason", "Hash mismatch: rows differ from original")
                    print(f"[{task_id}] INTEGRITY FAILURE: {previous_error}")
                    attempt += 1
                    continue
                    
                # ─── PHASE 5: VERIFY + GATE
                new_ms = next_obs.latency_ms
                hash_match = True
                final_json = data
                
                if new_ms < baseline_ms:
                    verdict = "OPTIMIZED"
                else:
                    verdict = "NO_IMPROVEMENT"
                break
                
            else:
                raise ValueError(f"Unknown or missing action from LLM: {action}")
                
                
        except Exception as e:
            import traceback
            previous_error = f"ERROR: {str(e)}"
            print(f"[{task_id}] GROQ EXCEPTION: {previous_error}")
            traceback.print_exc()
            attempt += 1
            time.sleep(2)
            
    if attempt > 3 and verdict == "FAILED":
        verdict = "FAILED"
        
    env.engine.close()
    
    # ─── PHASE 6: GENERATE SUMMARY.md
    if final_json and verdict == "OPTIMIZED":
        improvement = ((baseline_ms - new_ms) / baseline_ms * 100) if baseline_ms > 0 else 0
        
        def format_plan(plan_str, markers, marker_text):
            try:
                import ast
                parsed = ast.literal_eval(plan_str)
                if isinstance(parsed, list) and isinstance(parsed[0], tuple):
                    plan_str = parsed[0][1]
            except:
                pass
            
            # handle raw literal \n vs actual newline
            lines = plan_str.replace('\\n', '\n').split('\n')
            formatted = []
            matched_items = []
            
            for i, line in enumerate(lines, start=1):
                clean_line = line.strip('\r\n')
                if not clean_line.strip() and i == len(lines):
                    continue
                
                line_str = f"line {str(i).rjust(2)}:  {clean_line}"
                marked = False
                if markers:
                    for k, v in markers.items():
                        if isinstance(v, str) and v.strip() and v.strip() in clean_line:
                            line_str += f"  ← {marker_text}"
                            matched_items.append(f"- **Line {i}:** {v.strip()}")
                            marked = True
                            break
                            
                formatted.append(line_str)
                
            out = "```\n" + "\n".join(formatted) + "\n```"
            if matched_items:
                if marker_text == "BOTTLENECK":
                    out += "\n\n### Bottleneck Lines\n" + "\n".join(matched_items)
                else:
                    out += "\n\n### Fixed Lines\n" + "\n".join(matched_items)
            return out

        summary = f"---\n\n# Agent Task Summary: {task_file}\n\n"
        summary += "## Metrics\n\n"
        summary += "| Metric      | Original   | Optimized  | Improvement |\n"
        summary += "|-------------|------------|------------|-------------|\n"
        summary += f"| Latency     | {baseline_ms:.2f} ms   | {new_ms:.2f} ms    | +{improvement:.2f}%     |\n"
        summary += f"| Hash match  | —          | {hash_match}       | —           |\n\n"
        summary += "---\n\n"
        
        summary += "## What Was Wrong\n\n"
        # Extract bottleneck from matches or fallback
        b_type = "Performance Issue"
        if "CAST" in final_json.get('reasoning', '').upper(): b_type = "FUNCTION_ON_FILTER"
        elif "JOIN" in final_json.get('reasoning', '').upper(): b_type = "SUBOPTIMAL_JOIN"
        
        summary += f"**Bottleneck:** {b_type}\n"
        summary += f"**Problem:** {final_json.get('reasoning', 'No reasoning provided.')}\n\n"
        summary += "---\n\n"
        
        summary += "## What Was Fixed\n\n"
        summary += f"**Change:** {final_json.get('confidence_reason', 'No specific fix listed.')}\n"
        summary += f"**Effect:** Latency reduced by {improvement:.2f}%.\n\n"
        summary += "---\n\n"
        
        summary += "## Original Query Plan\n\n"
        orig_markers = final_json.get('original_plan_annotation', {})
        summary += format_plan(obs.query_plan_json, orig_markers, "BOTTLENECK")
        summary += "\n\n---\n\n"
        
        summary += "## Optimized Query Plan\n\n"
        opt_markers = final_json.get('optimized_plan_diff', {})
        opt_plan_str = next_obs.query_plan_json if 'next_obs' in locals() else ""
        summary += format_plan(opt_plan_str, opt_markers, "FIXED")
        summary += "\n\n---\n\n"
        
        summary += "## Agent Reasoning\n\n"
        summary += f"{final_json.get('reasoning', 'N/A')}\n\n"
        summary += "---\n\n"
        
        summary += "## Confidence\n\n"
        summary += f"**{str(final_json.get('confidence', 'HIGH')).upper()}** — {final_json.get('confidence_reason', 'N/A')}\n\n"
        summary += "---\n\n"
        
        summary += "## Verdict\n\n"
        summary += "> Query successfully optimized.\n"
        summary += f"> {baseline_ms:.2f} ms → {new_ms:.2f} ms — {improvement:.2f}% faster with full \n"
        summary += "> hash fidelity confirmed.\n\n"
        summary += "---\n"
        
        summary += "---\n"
        
    elif verdict == "NO_CHANGE":
        summary = "Query already optimal — no rewrite performed.\n---\n"
    else:
        # For FAILED and NO_IMPROVEMENT, write only to terminal. No SUMMARY.md created.
        summary = ""
            
    return {
        "task_id": task_id,
        "baseline_ms": baseline_ms,
        "new_ms": new_ms,
        "improvement": ((baseline_ms - new_ms) / baseline_ms * 100) if baseline_ms > 0 else 0,
        "verdict": verdict,
        "summary": summary if 'summary' in locals() else ""
    }

def main():
    setup_llm()
    selected_tasks = select_tasks()
    check_environment()
    
    print("\n─── PHASE 2-6: ORCHESTRATION ─────────────────────────────────")
    results = []
    
    if len(selected_tasks) == 1:
        res = process_task(selected_tasks[0])
        results.append(res)
    else:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(process_task, task): task for task in selected_tasks}
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as exc:
                    task = futures[future]
                    print(f'{task} generated an exception: {exc}')
                    print(traceback.format_exc())

    print("\n─── TERMINAL OUTPUT (final) ────────────────────────────────────")
    print("task_id         | baseline_ms | new_ms    | improvement% | verdict")
    print("-" * 75)
    for r in results:
        t_id = str(r["task_id"]).ljust(15)
        b_ms = f'{r["baseline_ms"]:.2f}'.ljust(11)
        n_ms = f'{r["new_ms"]:.2f}'.ljust(9)
        imp = f'{r["improvement"]:.2f}%'.ljust(12)
        verd = r["verdict"]
        print(f"{t_id} | {b_ms} | {n_ms} | {imp} | {verd}")
        
    written_summaries = [r["summary"] for r in results if r.get("summary")]
    if written_summaries:
        combined_text = "\n\n".join(written_summaries)
        base_filename = "SUMMARY_allfiles" if len(selected_tasks) > 1 else f"SUMMARY_{results[0]['task_id']}"
        
        final_path = os.path.join(AGENT_CODE_DIR, f"{base_filename}.md")
        counter = 2
        while os.path.exists(final_path):
            final_path = os.path.join(AGENT_CODE_DIR, f"{base_filename}_{counter}x.md")
            counter += 1
            
        with open(final_path, "w") as f:
            f.write(combined_text)
            
        print(f"\nReport written to AgentCode/{os.path.basename(final_path)}")
    else:
        print("\nNo reports generated (all failed or NO_IMPROVEMENT).")

if __name__ == "__main__":
    main()
