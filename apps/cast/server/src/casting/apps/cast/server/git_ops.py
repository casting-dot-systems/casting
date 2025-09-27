from fastapi import APIRouter, HTTPException
from pathlib import Path
import os
import subprocess
from typing import Optional, Dict, Any
from .models import GitCommit, GitMerge, GitPush, GitBranch, GitRemote

router = APIRouter(prefix="/git", tags=["git"])

def get_git_folder() -> Path:
    """Get the configured git folder path from environment variables"""
    folder_path = os.getenv('GIT_FOLDER_PATH', './')
    return Path(folder_path)

def execute_git_command(command: list, cwd: Optional[Path] = None) -> Dict[str, Any]:
    """Execute a git command in the specified directory with error handling"""
    if cwd is None:
        cwd = get_git_folder()

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timed out",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

@router.post("/add")
async def git_add():
    """Stage all changes (git add .)"""
    result = execute_git_command(["git", "add", "."])

    if not result["success"]:
        raise HTTPException(status_code=500, detail=f"Git add failed: {result['stderr']}")

    return {"message": "All changes staged successfully", "output": result["stdout"]}

@router.post("/commit")
async def git_commit(commit_data: GitCommit):
    """Commit staged changes with a message"""
    command = ["git", "commit", "-m", commit_data.message]

    if commit_data.author_name and commit_data.author_email:
        command.extend(["--author", f"{commit_data.author_name} <{commit_data.author_email}>"])

    result = execute_git_command(command)

    if not result["success"]:
        if "nothing to commit" in result["stdout"]:
            return {"message": "Nothing to commit, working tree clean", "output": result["stdout"]}
        raise HTTPException(status_code=500, detail=f"Git commit failed: {result['stderr']}")

    return {"message": "Commit created successfully", "output": result["stdout"]}

@router.post("/push")
async def git_push(push_data: GitPush):
    """Push commits to remote repository"""
    command = ["git", "push"]

    # Add set-upstream flag if requested
    if push_data.set_upstream:
        command.extend(["-u", push_data.remote])
        if push_data.branch:
            command.append(push_data.branch)
    else:
        command.append(push_data.remote)
        if push_data.branch:
            command.append(push_data.branch)

    result = execute_git_command(command)

    if not result["success"]:
        error_msg = result['stderr']

        # Check for common push errors and provide helpful messages
        if "no upstream branch" in error_msg.lower():
            return {
                "success": False,
                "error": "No upstream branch set. Try again with set_upstream=true or configure remote repository first.",
                "suggestion": "Use set_upstream=true parameter or run: git remote add origin <repository-url>",
                "detailed_error": error_msg
            }
        elif "remote rejected" in error_msg.lower():
            return {
                "success": False,
                "error": "Push rejected by remote repository. Check permissions or branch protection rules.",
                "detailed_error": error_msg
            }
        elif "failed to push" in error_msg.lower():
            return {
                "success": False,
                "error": "Failed to push. Repository may not exist or you don't have access.",
                "suggestion": "Verify remote repository URL and access permissions",
                "detailed_error": error_msg
            }
        else:
            return {
                "success": False,
                "error": f"Git push failed: {error_msg}",
                "detailed_error": error_msg
            }

    return {"message": "Push completed successfully", "output": result["stdout"]}

@router.post("/pull")
async def git_pull(remote: str = "origin", branch: str = None):
    """Pull changes from remote repository"""
    command = ["git", "pull", remote]

    if branch:
        command.append(branch)

    result = execute_git_command(command)

    if not result["success"]:
        error_msg = result['stderr']

        # Check for common pull errors and provide helpful messages
        if "merge conflict" in error_msg.lower() or "conflict" in error_msg.lower():
            return {
                "success": False,
                "error": "Merge conflicts detected during pull",
                "suggestion": "Resolve conflicts manually or use git reset --hard to discard local changes",
                "conflicts": True,
                "detailed_error": error_msg
            }
        elif "divergent branches" in error_msg.lower():
            return {
                "success": False,
                "error": "Local and remote branches have diverged",
                "suggestion": "Consider using git pull --rebase or merge manually",
                "detailed_error": error_msg
            }
        elif "no such remote" in error_msg.lower():
            return {
                "success": False,
                "error": f"Remote '{remote}' does not exist",
                "suggestion": "Check remote name with git remote -v or add remote first",
                "detailed_error": error_msg
            }
        else:
            return {
                "success": False,
                "error": f"Git pull failed: {error_msg}",
                "detailed_error": error_msg
            }

    return {"message": "Pull completed successfully", "output": result["stdout"]}

@router.get("/status")
async def git_status():
    """Show git status"""
    result = execute_git_command(["git", "status", "--porcelain"])

    if not result["success"]:
        raise HTTPException(status_code=500, detail=f"Git status failed: {result['stderr']}")

    status_result = execute_git_command(["git", "status"])

    return {
        "short_status": result["stdout"].split('\n') if result["stdout"] else [],
        "full_status": status_result["stdout"],
        "clean": not result["stdout"]
    }

@router.get("/log")
async def git_log(limit: int = 10):
    """Show commit history"""
    result = execute_git_command(["git", "log", f"-{limit}", "--oneline"])

    if not result["success"]:
        raise HTTPException(status_code=500, detail=f"Git log failed: {result['stderr']}")

    commits = result["stdout"].split('\n') if result["stdout"] else []

    return {"commits": commits, "total": len(commits)}

@router.post("/merge")
async def git_merge(merge_data: GitMerge):
    """Merge branch (auto-stage conflicts and commit if configured)"""
    result = execute_git_command(["git", "merge", merge_data.branch_name])

    if result["success"]:
        return {"message": f"Merged {merge_data.branch_name} successfully", "output": result["stdout"]}

    if "CONFLICT" in result["stderr"] or "CONFLICT" in result["stdout"]:
        if merge_data.allow_conflicts:
            add_result = execute_git_command(["git", "add", "."])
            if add_result["success"]:
                commit_result = execute_git_command(["git", "commit", "-m", f"Merge {merge_data.branch_name} with conflicts"])
                if commit_result["success"]:
                    return {
                        "message": f"Merged {merge_data.branch_name} with conflicts staged and committed",
                        "conflicts": True,
                        "output": result["stdout"] + "\n" + commit_result["stdout"]
                    }

        return {
            "message": f"Merge conflicts detected in {merge_data.branch_name}",
            "conflicts": True,
            "output": result["stdout"] + "\n" + result["stderr"]
        }

    raise HTTPException(status_code=500, detail=f"Git merge failed: {result['stderr']}")

@router.post("/branch")
async def git_create_branch(branch_data: GitBranch):
    """Create a new branch"""
    result = execute_git_command(["git", "branch", branch_data.branch_name])

    if not result["success"]:
        raise HTTPException(status_code=500, detail=f"Git branch creation failed: {result['stderr']}")

    return {"message": f"Branch {branch_data.branch_name} created successfully", "output": result["stdout"]}

@router.get("/branch")
async def git_list_branches():
    """List all branches"""
    result = execute_git_command(["git", "branch", "-a"])

    if not result["success"]:
        raise HTTPException(status_code=500, detail=f"Git branch list failed: {result['stderr']}")

    branches = []
    current_branch = None

    for line in result["stdout"].split('\n'):
        if line.strip():
            if line.startswith('* '):
                current_branch = line[2:].strip()
                branches.append({"name": current_branch, "current": True})
            else:
                branches.append({"name": line.strip(), "current": False})

    return {"branches": branches, "current_branch": current_branch}

@router.post("/checkout")
async def git_checkout(branch_data: GitBranch):
    """Switch to a branch"""
    result = execute_git_command(["git", "checkout", branch_data.branch_name])

    if not result["success"]:
        raise HTTPException(status_code=500, detail=f"Git checkout failed: {result['stderr']}")

    return {"message": f"Switched to branch {branch_data.branch_name}", "output": result["stdout"]}

@router.get("/diff")
async def git_diff(staged: bool = False):
    """Show changes (staged or unstaged)"""
    command = ["git", "diff"]
    if staged:
        command.append("--staged")

    result = execute_git_command(command)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=f"Git diff failed: {result['stderr']}")

    return {
        "diff": result["stdout"],
        "staged": staged,
        "has_changes": bool(result["stdout"])
    }

@router.post("/remote")
async def git_add_remote(remote_data: GitRemote):
    """Add a git remote"""
    result = execute_git_command(["git", "remote", "add", remote_data.remote_name, remote_data.remote_url])

    if not result["success"]:
        if "already exists" in result["stderr"]:
            return {
                "success": False,
                "error": f"Remote '{remote_data.remote_name}' already exists",
                "suggestion": f"Use 'git remote set-url {remote_data.remote_name} {remote_data.remote_url}' to update"
            }
        return {
            "success": False,
            "error": f"Failed to add remote: {result['stderr']}"
        }

    return {"message": f"Remote {remote_data.remote_name} added successfully", "output": result["stdout"]}

@router.get("/remote")
async def git_list_remotes():
    """List all git remotes"""
    result = execute_git_command(["git", "remote", "-v"])

    if not result["success"]:
        return {
            "success": False,
            "error": f"Failed to list remotes: {result['stderr']}"
        }

    remotes = []
    if result["stdout"]:
        for line in result["stdout"].split('\n'):
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0]
                    url = parts[1]
                    op_type = parts[2] if len(parts) > 2 else "fetch"
                    remotes.append({"name": name, "url": url, "type": op_type})

    return {"remotes": remotes, "count": len(remotes)}

@router.get("/conflicts")
async def git_get_conflicts():
    """Get detailed information about merge conflicts"""
    # Get list of conflicted files
    result = execute_git_command(["git", "diff", "--name-only", "--diff-filter=U"])

    if not result["success"]:
        return {
            "success": False,
            "error": f"Failed to get conflict info: {result['stderr']}"
        }

    conflicted_files = [f.strip() for f in result["stdout"].split('\n') if f.strip()]

    if not conflicted_files:
        return {
            "success": True,
            "has_conflicts": False,
            "files": [],
            "message": "No merge conflicts found"
        }

    # Get conflict details for each file
    conflicts_info = []
    for file in conflicted_files:
        # Get the conflicted content
        conflict_result = execute_git_command(["git", "show", f":{file}"], cwd=get_git_folder())
        if conflict_result["success"]:
            conflicts_info.append({
                "file": file,
                "content": conflict_result["stdout"],
                "status": "conflicted"
            })
        else:
            conflicts_info.append({
                "file": file,
                "content": "",
                "status": "error",
                "error": conflict_result["stderr"]
            })

    return {
        "success": True,
        "has_conflicts": True,
        "files": conflicts_info,
        "count": len(conflicted_files),
        "message": f"Found {len(conflicted_files)} conflicted file(s)"
    }