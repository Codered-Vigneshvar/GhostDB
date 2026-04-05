# GhostQuery: Autonomous Multi-Agent Incident Response Arena

### 🚀 Autonomous Multi-Agent Incident Response
GhostQuery is an LLM-driven simulation engine where an **AttackerAgent** injects silent data corruption, and a **DefenderAgent** (Autonomous AI Data Engineer) diagnoses and repairs the pipeline in real-time.

> [!IMPORTANT]
> - **Unified Master Guide**: [MASTER_TECHNICAL_GUIDE.md](file:///Users/vigneshvars/.gemini/antigravity/brain/0a995cd8-c13a-4757-a57d-176ab76cf762/MASTER_TECHNICAL_GUIDE.md) (The One Document to Rule Them All)
> - **Capability Deep Dive**: [AGENT_CAPABILITIES_DEEP_DIVE.md](file:///Users/vigneshvars/.gemini/antigravity/brain/0a995cd8-c13a-4757-a57d-176ab76cf762/AGENT_CAPABILITIES_DEEP_DIVE.md) (How the AI Solves Issues)
> - **Architectural Specification**: [GHOSTQUERY_SPEC.md](file:///Users/vigneshvars/.gemini/antigravity/brain/0a995cd8-c13a-4757-a57d-176ab76cf762/GHOSTQUERY_SPEC.md) (Ultra-Detailed Logic)
> - **Data Engineer's Guide**: [DATA_ENGINEER_GUIDE.md](file:///Users/vigneshvars/.gemini/antigravity/brain/0a995cd8-c13a-4757-a57d-176ab76cf762/DATA_ENGINEER_GUIDE.md) (Product Utility & Observability)

GhostQuery is a Meta OpenEnv 2026 RL Benchmark. It trains agents to resolve data incidents using high-fidelity DuckDB simulation.

## Hugging Face Space Deployment

- **Runtime:** Docker
- **Entry point:** `uvicorn ghost_query.api.openenv_app:app`
- **Port:** `8000`

## Multi-Agent Architecture

- **Attacker Agent**: Injects realistic data corruption and noise.
- **Defender Agent**: Monitors, diagnoses, and patches SQL regessions.
- **Evaluator Agent**: Grades interactions and maintains data fidelity.

## How to Run

### Local (Python)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the OpenEnv API server
export PYTHONPATH=$PYTHONPATH:.
uvicorn ghost_query.api.openenv_app:app --host 0.0.0.0 --port 8000

# 3. Execute inference benchmark (in another terminal)
python3 inference.py
```

### Local (Docker)
```bash
# 1. Build the image
docker build -t ghostquery-arena .

# 2. Run the container
docker run -p 8000:8000 \
  -e HF_TOKEN=your_token \
  -e MODEL_NAME=llama-3.3-70b-versatile \
  ghostquery-arena
```

## Environment Variables
The following variables are required for full agent functionality:
- `HF_TOKEN`: Your API authentication token.
- `MODEL_NAME`: The target LLM model name.
- `API_BASE_URL` (Optional): Custom OpenAI-compatible endpoint.

---
*Developed for the Meta OpenEnv 2026 Hackathon.*
