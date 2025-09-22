import subprocess
import time
import os
import sys

REPO_DIR = r"C:\Users\Administrator\Downloads\tiktok-readcomment"  # <- Sửa path này
APP_FILE = "../app.py"  # File Flask app

CHECK_INTERVAL = 10 # Giây: thời gian kiểm tra lại
def get_latest_remote_commit():
    subprocess.run(["git", "fetch"], cwd=REPO_DIR)
    result = subprocess.run(["git", "rev-parse", "origin/main"], cwd=REPO_DIR, capture_output=True, text=True)
    return result.stdout.strip()

def get_current_commit():
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_DIR, capture_output=True, text=True)
    return result.stdout.strip()

def start_app():
    print("[INFO] Starting Flask app...")
    return subprocess.Popen(["python", APP_FILE], cwd=REPO_DIR)

def stop_app(process):
    print("[INFO] Stopping Flask app...")
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()

def main():
    print("[INFO] Starting Git watcher...")
    app_process = start_app()
    current_commit = get_current_commit()

    while True:
        try:
            remote_commit = get_latest_remote_commit()
            if remote_commit != current_commit:
                print(f"[INFO] New commit found: {remote_commit}")
                stop_app(app_process)
                subprocess.run(["git", "pull"], cwd=REPO_DIR)
                current_commit = get_current_commit()
                app_process = start_app()
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n[INFO] Interrupted. Stopping app.")
            stop_app(app_process)
            break

if __name__ == "__main__":
    main()
