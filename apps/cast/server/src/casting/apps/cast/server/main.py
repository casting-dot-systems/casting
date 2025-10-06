from casting.platform.config import bootstrap_env, find_app_dir
from fastapi import FastAPI

from .git_ops import router as git_router
from .markdown import router as markdown_router

APP_DIR = find_app_dir(__file__)
bootstrap_env(app_dir=APP_DIR)

app = FastAPI(title="Markdown File API", description="API for managing markdown files and git operations")

app.include_router(markdown_router)
app.include_router(git_router)


@app.get("/")
async def root():
    return {"message": "Markdown File API"}


def main():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
