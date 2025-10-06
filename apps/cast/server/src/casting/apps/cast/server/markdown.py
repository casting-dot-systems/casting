from fastapi import APIRouter, HTTPException
from pathlib import Path
import os
from .models import MarkdownContent, MarkdownCreate

router = APIRouter(prefix="/markdown", tags=["markdown"])


def get_markdown_folder():
    """Get the configured markdown folder path from environment variables"""
    folder_path = os.getenv("MARKDOWN_FOLDER_PATH", "./")
    return Path(folder_path)


def ensure_markdown_folder_exists():
    """Ensure the markdown folder exists, create if it doesn't"""
    folder_path = get_markdown_folder()
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path


@router.post("/create")
async def create_markdown_file(file_data: MarkdownCreate):
    """Create a new markdown file or append to existing file"""
    folder_path = ensure_markdown_folder_exists()
    filename = file_data.filename
    if not filename.endswith(".md"):
        filename += ".md"

    file_path = folder_path / filename
    file_existed = file_path.exists()

    try:
        if file_existed:
            # File exists, append content
            with open(file_path, "r", encoding="utf-8") as f:
                existing_content = f.read()

            # Append new content with a newline separator if existing content doesn't end with newline
            separator = "" if existing_content.endswith("\n") or not existing_content else "\n"
            new_content = existing_content + separator + file_data.content

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return {
                "message": f"Content appended to existing file {filename}",
                "filename": filename,
                "file_existed": True,
                "action": "appended",
            }
        else:
            # File doesn't exist, create new
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_data.content)

            return {
                "message": f"File {filename} created successfully",
                "filename": filename,
                "file_existed": False,
                "action": "created",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.put("/{filename}")
async def write_to_markdown_file(filename: str, content: MarkdownContent):
    """Write content to a markdown file (create if doesn't exist)"""
    folder_path = ensure_markdown_folder_exists()
    if not filename.endswith(".md"):
        filename += ".md"

    file_path = folder_path / filename
    file_existed = file_path.exists()

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.content)

        if file_existed:
            return {
                "message": f"Content updated in {filename} successfully",
                "filename": filename,
                "file_existed": True,
                "action": "updated",
            }
        else:
            return {
                "message": f"File {filename} created successfully (did not exist)",
                "filename": filename,
                "file_existed": False,
                "action": "created",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing to file: {str(e)}")


@router.get("/{filename}")
async def read_markdown_file(filename: str):
    """Read content from a markdown file"""
    folder_path = get_markdown_folder()
    if not filename.endswith(".md"):
        filename += ".md"

    file_path = folder_path / filename

    if not file_path.exists():
        return {
            "success": False,
            "message": f"File {filename} does not exist",
            "filename": filename,
            "error": "file_not_found",
            "content": "",
            "action": "read_failed",
        }

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {
            "success": True,
            "filename": filename,
            "content": content,
            "message": f"File {filename} read successfully",
            "action": "read",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error reading file: {str(e)}",
            "filename": filename,
            "error": "read_error",
            "content": "",
            "action": "read_failed",
        }


@router.delete("/{filename}")
async def delete_markdown_file(filename: str):
    """Delete a markdown file"""
    folder_path = get_markdown_folder()
    if not filename.endswith(".md"):
        filename += ".md"

    file_path = folder_path / filename

    if not file_path.exists():
        return {
            "success": False,
            "message": f"File {filename} does not exist",
            "filename": filename,
            "error": "file_not_found",
            "action": "delete_failed",
        }

    try:
        file_path.unlink()
        return {
            "success": True,
            "message": f"File {filename} deleted successfully",
            "filename": filename,
            "action": "deleted",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error deleting file: {str(e)}",
            "filename": filename,
            "error": "delete_error",
            "action": "delete_failed",
        }


@router.get("/")
async def list_markdown_files():
    """List all markdown files in the configured directory"""
    try:
        folder_path = get_markdown_folder()
        md_files = [f.name for f in folder_path.glob("*.md")] if folder_path.exists() else []
        return {"files": md_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")
