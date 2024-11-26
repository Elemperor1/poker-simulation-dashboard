import time
import subprocess
import datetime
from pathlib import Path

def run_git_command(command):
    try:
        subprocess.run(command, cwd=str(Path(__file__).parent), check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}")
        return False

def auto_push():
    while True:
        # Add all changes
        if run_git_command(['git', 'add', '.']):
            # Create commit with timestamp
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if run_git_command(['git', 'commit', '-m', f'Auto-commit: {timestamp}']):
                # Push changes
                if run_git_command(['git', 'push']):
                    print(f"Successfully pushed changes at {timestamp}")
                else:
                    print("Failed to push changes")
            else:
                print("No changes to commit")
        else:
            print("Failed to add changes")
        
        # Wait for 10 minutes
        time.sleep(600)

if __name__ == '__main__':
    print("Starting auto-push script. Press Ctrl+C to stop.")
    try:
        auto_push()
    except KeyboardInterrupt:
        print("\nAuto-push script stopped.")
