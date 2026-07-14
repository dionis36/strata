#!/usr/bin/env python3
"""
generate_phpmetrics.py

Universal script to generate PhpMetrics baselines for Strata validation.
This script checks for Docker, handles cross-platform volume mounts, 
and generates the PhpMetrics JSON.

Usage:
    python3 evaluation/runners/generate_phpmetrics.py
"""
import os
import subprocess
import sys

# Paths
# Resolves to /home/dio/Documents/strata
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
AUDIT_DIR = os.path.join(BASE_DIR, "AUDIT")

def check_docker_installed():
    """Verify that Docker is installed and accessible."""
    try:
        subprocess.run(["docker", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n❌ ERROR: Docker is not installed or not running.")
        print("Please install Docker and ensure the daemon is running before using this script.")
        sys.exit(1)

def check_phpmetrics_image():
    """Verify that the phpmetrics image is available, pull if not."""
    print("[*] Checking for phpmetrics/phpmetrics Docker image...")
    try:
        # Check if it exists locally
        subprocess.run(["docker", "image", "inspect", "phpmetrics/phpmetrics"], 
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("[*] Image not found locally. Pulling phpmetrics/phpmetrics...")
        try:
            subprocess.run(["docker", "pull", "phpmetrics/phpmetrics"], check=True)
        except subprocess.CalledProcessError:
            print("\n❌ ERROR: Failed to pull phpmetrics/phpmetrics image.")
            print("Check your internet connection or Docker permissions.")
            sys.exit(1)

def get_data_directories():
    """Returns a list of subdirectories in the /data folder."""
    if not os.path.exists(DATA_DIR):
        print(f"Error: Data directory not found at {DATA_DIR}")
        sys.exit(1)
        
    return [d for d in os.listdir(DATA_DIR) 
            if os.path.isdir(os.path.join(DATA_DIR, d))]

def main():
    print("=" * 60)
    print("  PHPMETRICS BASELINE GENERATOR")
    print("=" * 60)
    
    # Pre-flight checks
    check_docker_installed()
    check_phpmetrics_image()
    
    dirs = get_data_directories()
    if not dirs:
        print("No project directories found in /data.")
        return

    print("\nAvailable projects in /data:")
    for i, d in enumerate(dirs, 1):
        print(f"  [{i}] {d}")
        
    choice = int(input("\nSelect a project by number to analyze: "))
    if choice < 1 or choice > len(dirs):
        print("Invalid selection.")
        return

    selected_project = dirs[choice - 1]
    project_path = os.path.join(DATA_DIR, selected_project)
    
    report_folder_name = f"phpmetrics_{selected_project}"
    report_dir = os.path.join(AUDIT_DIR, report_folder_name)
    
    # Create the report directory
    os.makedirs(report_dir, exist_ok=True)
    
    print(f"\n[+] Selected Project: {selected_project}")
    print(f"[+] Output Directory: {report_dir}")
    print("\nExecuting PhpMetrics via Docker. This may take a few minutes...")
    
    # Cross-platform volume mounting logic
    z_flag = ":z" if sys.platform.startswith("linux") else ""
    
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{project_path}:/project{z_flag}",
        "-v", f"{report_dir}:/report{z_flag}",
        "phpmetrics/phpmetrics",
        "--report-html=/report/html",
        "--report-json=/report/report.json",
        "/project"
    ]
    
    subprocess.run(docker_cmd, check=True)
    print("\n" + "=" * 60)
    print("✅ SUCCESS: PhpMetrics analysis complete.")
    print(f"   Baseline stored in: AUDIT/{report_folder_name}")
    print("   Ignored by Git/Docker to keep repository clean.")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Operation cancelled by user. Exiting cleanly...")
        sys.exit(0)
    except ValueError:
        print("\n[!] Please enter a valid number.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR: Docker execution failed.\n{e}")
        sys.exit(1)
