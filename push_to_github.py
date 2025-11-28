"""Push dashboard files to GitHub repository"""
import os
import subprocess
import sys

# Set environment variables to prevent git from hanging
os.environ['GIT_TERMINAL_PROMPT'] = '0'
os.environ['GIT_ASKPASS'] = ''
os.environ['GIT_CREDENTIAL_HELPER'] = ''

def run_git_command(cmd):
    """Run a git command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
            env=os.environ.copy()
        )
        print(f"Command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {cmd}")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False

print("Setting up git repository...")

# Add files
print("\n1. Adding files...")
run_git_command(['git', 'add', 'dashboard.py'])
run_git_command(['git', 'add', 'requirements.txt'])
run_git_command(['git', 'add', 'README.md'])
run_git_command(['git', 'add', '.gitignore'])

# Check status
print("\n2. Checking status...")
run_git_command(['git', 'status'])

# Commit
print("\n3. Committing...")
run_git_command(['git', 'commit', '-m', 'Initial commit: Streamlit dashboard for bet analysis'])

# Set branch to main
print("\n4. Setting branch to main...")
run_git_command(['git', 'branch', '-M', 'main'])

# Check remote
print("\n5. Checking remote...")
run_git_command(['git', 'remote', '-v'])

# Add remote if needed
result = subprocess.run(['git', 'remote', 'get-url', 'origin'], capture_output=True, timeout=5, env=os.environ.copy())
if result.returncode != 0:
    print("\n6. Adding remote origin...")
    run_git_command(['git', 'remote', 'add', 'origin', 'https://github.com/jonDomino/grades-dashboard.git'])

# Push
print("\n7. Pushing to GitHub...")
print("Note: You may need to authenticate. If this hangs, please run manually.")
run_git_command(['git', 'push', '-u', 'origin', 'main'])

print("\nDone!")

