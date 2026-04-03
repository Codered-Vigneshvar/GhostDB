from openenv.core.env_server import create_fastapi_app
from ghost_query.environment.sql_env import SQLEnv

app = create_fastapi_app(SQLEnv)

if __name__ == "__main__":
    import uvicorn
    # Use the modular import path for the entrypoint
    uvicorn.run("ghost_query.app:app", host="0.0.0.0", port=8000)
