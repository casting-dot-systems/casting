from fastapi import FastAPI
from dotenv import load_dotenv
from .markdown import router as markdown_router
from .git_ops import router as git_router

load_dotenv()

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
