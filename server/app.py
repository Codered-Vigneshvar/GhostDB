from openenv.core.env_server import create_fastapi_app
from server.sql_env import SQLEnv

app = create_fastapi_app(SQLEnv)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000)
