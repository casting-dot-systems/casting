from pydantic import BaseModel
from typing import Optional


class MarkdownContent(BaseModel):
    content: str


class MarkdownCreate(BaseModel):
    filename: str
    content: str = ""


class GitCommit(BaseModel):
    message: str
    author_name: Optional[str] = None
    author_email: Optional[str] = None


class GitMerge(BaseModel):
    branch_name: str
    allow_conflicts: bool = True


class GitPush(BaseModel):
    remote: str = "origin"
    branch: Optional[str] = None
    set_upstream: bool = False


class GitBranch(BaseModel):
    branch_name: str


class GitRemote(BaseModel):
    remote_name: str = "origin"
    remote_url: str
