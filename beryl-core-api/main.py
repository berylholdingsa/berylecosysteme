import os

import uvicorn

from src.main import app


if __name__ == "__main__":
    port = int(os.environ.get("PORT"))
    uvicorn.run(app, host="0.0.0.0", port=port)
