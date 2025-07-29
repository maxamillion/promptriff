#!/usr/bin/env python3
"""Security verification script for PromptRiff."""

import ast
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


class SecurityChecker:
    """Check for common security issues in the codebase."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.issues: List[Tuple[str, str, str]] = []
    
    def check_all(self) -> bool:
        """Run all security checks."""
        print("Running security checks...")
        
        self.check_hardcoded_secrets()
        self.check_sql_injection()
        self.check_path_traversal()
        self.check_command_injection()
        self.check_sensitive_logging()
        self.check_ssl_verification()
        self.check_input_validation()
        self.check_file_permissions()
        
        if self.issues:
            print(f"\n❌ Found {len(self.issues)} security issues:\n")
            for file_path, line_num, issue in self.issues:
                print(f"  {file_path}:{line_num} - {issue}")
            return False
        else:
            print("\n✅ No security issues found!")
            return True
    
    def check_hardcoded_secrets(self):
        """Check for hardcoded API keys and secrets."""
        patterns = [
            (r'api_key\s*=\s*["\'](?!test-|YOUR_|{)', "Potential hardcoded API key"),
            (r'sk-[a-zA-Z0-9]{40,}', "Potential OpenAI API key"),
            (r'sk-ant-[a-zA-Z0-9]{40,}', "Potential Anthropic API key"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Potential hardcoded password"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Potential hardcoded secret"),
        ]
        
        for py_file in self.root_path.glob("**/*.py"):
            if "test" in py_file.parts or "example" in py_file.parts:
                continue
                
            content = py_file.read_text()
            for line_num, line in enumerate(content.splitlines(), 1):
                for pattern, message in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        if "os.environ" not in line and "${" not in line:
                            self.issues.append((str(py_file), str(line_num), message))
    
    def check_sql_injection(self):
        """Check for potential SQL injection vulnerabilities."""
        patterns = [
            (r'execute\s*\(\s*["\'].*%s', "Potential SQL injection - use parameterized queries"),
            (r'execute\s*\(\s*f["\']', "Potential SQL injection - avoid f-strings in queries"),
            (r'execute\s*\(.*\+', "Potential SQL injection - avoid string concatenation"),
        ]
        
        for py_file in self.root_path.glob("**/*.py"):
            content = py_file.read_text()
            for line_num, line in enumerate(content.splitlines(), 1):
                for pattern, message in patterns:
                    if re.search(pattern, line):
                        self.issues.append((str(py_file), str(line_num), message))
    
    def check_path_traversal(self):
        """Check for path traversal vulnerabilities."""
        for py_file in self.root_path.glob("**/*.py"):
            content = py_file.read_text()
            
            # Check for unsafe path operations
            if "os.path.join" in content or "Path(" in content:
                for line_num, line in enumerate(content.splitlines(), 1):
                    if ".." in line and ("open(" in line or "Path(" in line):
                        if "resolve()" not in line and "expanduser()" not in line:
                            self.issues.append((
                                str(py_file),
                                str(line_num),
                                "Potential path traversal - validate and resolve paths"
                            ))
    
    def check_command_injection(self):
        """Check for command injection vulnerabilities."""
        dangerous_funcs = [
            "subprocess.run",
            "subprocess.call",
            "os.system",
            "os.popen",
        ]
        
        for py_file in self.root_path.glob("**/*.py"):
            content = py_file.read_text()
            for line_num, line in enumerate(content.splitlines(), 1):
                for func in dangerous_funcs:
                    if func in line and "shell=True" in line:
                        self.issues.append((
                            str(py_file),
                            str(line_num),
                            f"Avoid {func} with shell=True - risk of command injection"
                        ))
    
    def check_sensitive_logging(self):
        """Check for logging of sensitive information."""
        patterns = [
            (r'log.*api_key', "Avoid logging API keys"),
            (r'log.*password', "Avoid logging passwords"),
            (r'print.*api_key', "Avoid printing API keys"),
            (r'print.*password', "Avoid printing passwords"),
        ]
        
        for py_file in self.root_path.glob("**/*.py"):
            content = py_file.read_text()
            for line_num, line in enumerate(content.splitlines(), 1):
                for pattern, message in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        if "test" not in py_file.parts:
                            self.issues.append((str(py_file), str(line_num), message))
    
    def check_ssl_verification(self):
        """Check for disabled SSL verification."""
        patterns = [
            (r'verify\s*=\s*False', "SSL verification disabled"),
            (r'ssl\.create_default_context\(\)\.check_hostname\s*=\s*False', "Hostname verification disabled"),
            (r'urllib3\.disable_warnings', "SSL warnings disabled"),
        ]
        
        for py_file in self.root_path.glob("**/*.py"):
            content = py_file.read_text()
            for line_num, line in enumerate(content.splitlines(), 1):
                for pattern, message in patterns:
                    if re.search(pattern, line):
                        self.issues.append((str(py_file), str(line_num), message))
    
    def check_input_validation(self):
        """Check for proper input validation."""
        for py_file in self.root_path.glob("**/*.py"):
            if "models" in py_file.parts or "utils" in py_file.parts:
                try:
                    tree = ast.parse(py_file.read_text())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            # Check if function handles user input
                            if any(param.arg in ["user_input", "content", "prompt", "query"] 
                                   for param in node.args.args):
                                # Look for validation
                                has_validation = any(
                                    isinstance(child, ast.If) and 
                                    any(keyword in ast.unparse(child.test) 
                                        for keyword in ["len", "strip", "validate", "check"])
                                    for child in node.body
                                )
                                if not has_validation:
                                    self.issues.append((
                                        str(py_file),
                                        str(node.lineno),
                                        f"Function '{node.name}' may need input validation"
                                    ))
                except:
                    pass
    
    def check_file_permissions(self):
        """Check for secure file permission recommendations."""
        # Check configuration files
        config_patterns = ["**/config.yaml", "**/config.yml", "**/.env"]
        for pattern in config_patterns:
            for config_file in self.root_path.glob(pattern):
                # This is a recommendation, not a code issue
                print(f"ℹ️  Remember to set secure permissions on {config_file}: chmod 600")


def main():
    """Run security checks."""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run checks
    checker = SecurityChecker(project_root / "src")
    success = checker.check_all()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()