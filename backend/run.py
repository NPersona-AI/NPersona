"""Backend entry point – sets Windows-compatible asyncio event loop before uvicorn starts.

On Windows, Python 3.8+ defaults to ProactorEventLoop which is incompatible with
Neo4j's async SSL driver (causes WinError 10038). Setting WindowsSelectorEventLoopPolicy
here (before uvicorn creates the loop) fixes the connection.
"""
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )
