import aiohttp
import os
from typing import Dict, Any, Optional

class APIClient:
    """Client for interacting with the FastAPI backend"""
    
    def __init__(self):
        self.base_url = os.getenv('API_URL', 'http://localhost:8000')
        self.session = None
    
    async def get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an HTTP request to the API"""
        session = await self.get_session()
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                async with session.get(url) as response:
                    return await self._handle_response(response)
            elif method.upper() == 'POST':
                async with session.post(url, json=data) as response:
                    return await self._handle_response(response)
            elif method.upper() == 'PUT':
                async with session.put(url, json=data) as response:
                    return await self._handle_response(response)
            elif method.upper() == 'DELETE':
                async with session.delete(url) as response:
                    return await self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _handle_response(self, response) -> Dict[str, Any]:
        """Handle HTTP response"""
        try:
            data = await response.json()
            data["success"] = response.status < 400
            data["status_code"] = response.status
            return data
        except Exception as e:
            return {
                "error": f"Failed to parse response: {str(e)}",
                "success": False,
                "status_code": response.status
            }
    
    # Markdown operations
    async def create_markdown(self, filename: str, content: str = "") -> Dict[str, Any]:
        return await self.make_request('POST', '/markdown/create', {
            'filename': filename,
            'content': content
        })
    
    async def read_markdown(self, filename: str) -> Dict[str, Any]:
        return await self.make_request('GET', f'/markdown/{filename}')
    
    async def update_markdown(self, filename: str, content: str) -> Dict[str, Any]:
        return await self.make_request('PUT', f'/markdown/{filename}', {
            'content': content
        })
    
    async def delete_markdown(self, filename: str) -> Dict[str, Any]:
        return await self.make_request('DELETE', f'/markdown/{filename}')
    
    async def list_markdown(self) -> Dict[str, Any]:
        return await self.make_request('GET', '/markdown')
    
    # Git operations
    async def git_status(self) -> Dict[str, Any]:
        return await self.make_request('GET', '/git/status')
    
    async def git_add(self) -> Dict[str, Any]:
        return await self.make_request('POST', '/git/add')
    
    async def git_commit(self, message: str, author_name: str = None, author_email: str = None) -> Dict[str, Any]:
        data = {'message': message}
        if author_name:
            data['author_name'] = author_name
        if author_email:
            data['author_email'] = author_email
        return await self.make_request('POST', '/git/commit', data)
    
    async def git_push(self, remote: str = 'origin', branch: str = None, set_upstream: bool = False) -> Dict[str, Any]:
        data = {'remote': remote, 'set_upstream': set_upstream}
        if branch:
            data['branch'] = branch
        return await self.make_request('POST', '/git/push', data)

    async def git_pull(self, remote: str = 'origin', branch: str = None) -> Dict[str, Any]:
        params = f'?remote={remote}'
        if branch:
            params += f'&branch={branch}'
        return await self.make_request('POST', f'/git/pull{params}')
    
    async def git_log(self, limit: int = 10) -> Dict[str, Any]:
        return await self.make_request('GET', f'/git/log?limit={limit}')
    
    async def git_merge(self, branch_name: str, allow_conflicts: bool = True) -> Dict[str, Any]:
        return await self.make_request('POST', '/git/merge', {
            'branch_name': branch_name,
            'allow_conflicts': allow_conflicts
        })
    
    async def git_create_branch(self, branch_name: str) -> Dict[str, Any]:
        return await self.make_request('POST', '/git/branch', {
            'branch_name': branch_name
        })
    
    async def git_list_branches(self) -> Dict[str, Any]:
        return await self.make_request('GET', '/git/branch')
    
    async def git_checkout(self, branch_name: str) -> Dict[str, Any]:
        return await self.make_request('POST', '/git/checkout', {
            'branch_name': branch_name
        })
    
    async def git_diff(self, staged: bool = False) -> Dict[str, Any]:
        return await self.make_request('GET', f'/git/diff?staged={staged}')

    async def git_get_conflicts(self) -> Dict[str, Any]:
        return await self.make_request('GET', '/git/conflicts')