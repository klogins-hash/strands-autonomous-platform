"""
Code Editor for Agents

Gives agents the ability to:
- Read files in the codebase
- Edit files with precision (like Cascade does)
- Create new files
- Search code
- Refactor code
- Fix bugs in their own code
- Modify their own behavior
"""

import os
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import json

from anthropic import AsyncAnthropic
from ..core.config import settings
from ..core.utils import extract_json_from_response


class CodeEditor:
    """Enables agents to edit code like Cascade"""
    
    def __init__(self, workspace_root: str = None):
        self.anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.workspace_root = workspace_root or os.getcwd()
    
    async def read_file(self, file_path: str, start_line: int = None, end_line: int = None) -> str:
        """
        Read a file (with optional line range)
        
        Args:
            file_path: Path to file (absolute or relative to workspace)
            start_line: Optional starting line (1-indexed)
            end_line: Optional ending line (1-indexed)
            
        Returns:
            File contents with line numbers
        """
        full_path = self._resolve_path(file_path)
        
        try:
            with open(full_path, 'r') as f:
                lines = f.readlines()
            
            if start_line is not None:
                start_idx = start_line - 1
                end_idx = end_line if end_line else len(lines)
                lines = lines[start_idx:end_idx]
                line_offset = start_line
            else:
                line_offset = 1
            
            # Add line numbers
            numbered_lines = []
            for i, line in enumerate(lines, start=line_offset):
                numbered_lines.append(f"{i:4d}→{line.rstrip()}")
            
            return "\n".join(numbered_lines)
            
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    async def edit_file(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        explanation: str = ""
    ) -> Dict[str, Any]:
        """
        Edit a file by replacing old_string with new_string
        
        Args:
            file_path: Path to file
            old_string: Exact string to replace
            new_string: Replacement string
            explanation: Why this change is being made
            
        Returns:
            Result of the edit
        """
        full_path = self._resolve_path(file_path)
        
        try:
            # Read current content
            with open(full_path, 'r') as f:
                content = f.read()
            
            # Check if old_string exists
            if old_string not in content:
                return {
                    "success": False,
                    "error": f"String not found in file: {old_string[:100]}..."
                }
            
            # Check if it's unique
            count = content.count(old_string)
            if count > 1:
                return {
                    "success": False,
                    "error": f"String appears {count} times. Be more specific or use replace_all."
                }
            
            # Perform replacement
            new_content = content.replace(old_string, new_string)
            
            # Write back
            with open(full_path, 'w') as f:
                f.write(new_content)
            
            return {
                "success": True,
                "file": file_path,
                "explanation": explanation,
                "changes": {
                    "old": old_string[:200],
                    "new": new_string[:200]
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def multi_edit_file(
        self,
        file_path: str,
        edits: List[Dict[str, str]],
        explanation: str = ""
    ) -> Dict[str, Any]:
        """
        Make multiple edits to a file in sequence
        
        Args:
            file_path: Path to file
            edits: List of {old_string, new_string} dicts
            explanation: Why these changes are being made
            
        Returns:
            Result of all edits
        """
        full_path = self._resolve_path(file_path)
        
        try:
            with open(full_path, 'r') as f:
                content = f.read()
            
            applied_edits = []
            
            for i, edit in enumerate(edits):
                old_str = edit["old_string"]
                new_str = edit["new_string"]
                
                if old_str not in content:
                    return {
                        "success": False,
                        "error": f"Edit {i+1}: String not found: {old_str[:100]}..."
                    }
                
                content = content.replace(old_str, new_str, 1)
                applied_edits.append({
                    "edit_number": i + 1,
                    "old": old_str[:100],
                    "new": new_str[:100]
                })
            
            # Write all changes
            with open(full_path, 'w') as f:
                f.write(content)
            
            return {
                "success": True,
                "file": file_path,
                "explanation": explanation,
                "edits_applied": len(edits),
                "changes": applied_edits
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Create a new file
        
        Args:
            file_path: Path for new file
            content: File contents
            
        Returns:
            Result of creation
        """
        full_path = self._resolve_path(file_path)
        
        try:
            # Create parent directories if needed
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Write file
            with open(full_path, 'w') as f:
                f.write(content)
            
            return {
                "success": True,
                "file": file_path,
                "size": len(content)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_code(self, query: str, file_pattern: str = "*.py") -> List[Dict[str, Any]]:
        """
        Search for code in the workspace
        
        Args:
            query: Search string or regex
            file_pattern: File pattern to search (e.g., "*.py")
            
        Returns:
            List of matches with file, line, and context
        """
        try:
            # Use ripgrep if available, otherwise grep
            cmd = [
                "rg", "-n", "--no-heading",
                "-g", file_pattern,
                query,
                self.workspace_root
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            matches = []
            for line in result.stdout.split('\n'):
                if line:
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        matches.append({
                            "file": parts[0],
                            "line": int(parts[1]),
                            "content": parts[2]
                        })
            
            return matches
            
        except subprocess.TimeoutExpired:
            return []
        except FileNotFoundError:
            # Fallback to grep
            try:
                cmd = [
                    "grep", "-rn", query,
                    "--include", file_pattern,
                    self.workspace_root
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                matches = []
                for line in result.stdout.split('\n'):
                    if line and ':' in line:
                        parts = line.split(':', 2)
                        if len(parts) >= 3:
                            matches.append({
                                "file": parts[0],
                                "line": int(parts[1]),
                                "content": parts[2]
                            })
                
                return matches
            except:
                return []
    
    async def analyze_and_fix_error(
        self,
        error_message: str,
        file_path: str = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze an error and generate a fix
        
        Args:
            error_message: The error message
            file_path: File where error occurred (optional)
            context: Additional context
            
        Returns:
            Proposed fix with edits
        """
        # Read the problematic file if provided
        file_content = ""
        if file_path:
            file_content = await self.read_file(file_path)
        
        # Search for related code
        search_results = []
        if error_message:
            # Extract key terms from error
            key_terms = self._extract_key_terms(error_message)
            for term in key_terms[:3]:  # Top 3 terms
                results = await self.search_code(term)
                search_results.extend(results[:5])
        
        prompt = f"""
Analyze this error and propose a fix:

Error: {error_message}

File Content:
{file_content[:2000] if file_content else "Not provided"}

Related Code:
{json.dumps(search_results[:10], indent=2)}

Context: {json.dumps(context, indent=2) if context else "None"}

Return JSON with:
{{
    "analysis": "what's wrong",
    "root_cause": "why it's happening",
    "solution": "how to fix it",
    "edits": [
        {{
            "file": "path/to/file.py",
            "old_string": "exact code to replace",
            "new_string": "fixed code",
            "explanation": "why this fixes it"
        }}
    ],
    "additional_steps": ["step1", "step2"],
    "confidence": 0.0-1.0
}}
"""
        
        response = await self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return extract_json_from_response(response.content[0].text)
    
    async def refactor_code(
        self,
        file_path: str,
        refactoring_goal: str
    ) -> Dict[str, Any]:
        """
        Refactor code to improve it
        
        Args:
            file_path: File to refactor
            refactoring_goal: What to improve
            
        Returns:
            Refactored code with edits
        """
        # Read current code
        current_code = await self.read_file(file_path)
        
        prompt = f"""
Refactor this code to: {refactoring_goal}

Current Code:
{current_code}

Return JSON with:
{{
    "improvements": ["improvement1", "improvement2"],
    "edits": [
        {{
            "old_string": "code to replace",
            "new_string": "improved code",
            "explanation": "why this is better"
        }}
    ],
    "benefits": ["benefit1", "benefit2"]
}}
"""
        
        response = await self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return extract_json_from_response(response.content[0].text)
    
    async def apply_fix(self, fix: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a generated fix
        
        Args:
            fix: Fix dictionary with edits
            
        Returns:
            Result of applying the fix
        """
        results = []
        
        for edit in fix.get("edits", []):
            result = await self.edit_file(
                file_path=edit["file"],
                old_string=edit["old_string"],
                new_string=edit["new_string"],
                explanation=edit.get("explanation", "")
            )
            results.append(result)
        
        success_count = sum(1 for r in results if r.get("success"))
        
        return {
            "success": success_count == len(results),
            "total_edits": len(results),
            "successful_edits": success_count,
            "failed_edits": len(results) - success_count,
            "results": results
        }
    
    def _resolve_path(self, file_path: str) -> str:
        """Resolve file path relative to workspace"""
        if os.path.isabs(file_path):
            return file_path
        return os.path.join(self.workspace_root, file_path)
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from error message"""
        # Remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text)
        
        # Filter and return unique terms
        terms = [w for w in words if w.lower() not in common_words and len(w) > 3]
        return list(dict.fromkeys(terms))  # Unique, preserving order


# Global code editor instance
code_editor = CodeEditor()
