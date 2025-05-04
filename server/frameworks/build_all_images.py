#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

def build_all():
    """
    Builds all docker compose projects which are contained in the subdirectories of this file's path
    """
    root_dir = Path(__file__).resolve().parent

    compose_files = list(root_dir.rglob('docker-compose.y*ml'))

    if not compose_files:
        print("No docker-compose.yml or docker-compose.yaml files found.")
        sys.exit(0)

    for i, compose_file in enumerate(compose_files):
        dir_path = compose_file.parent
        print("=============================================================================\n")
        print(f"Building Docker services with docker-compose in directory: {dir_path}")
        print(f"Progress: [{i+1} / {len(compose_files)}]")
        print("\n=============================================================================")
        try:
            subprocess.run(["docker", "compose", "build"], cwd=dir_path, check=True)
        except subprocess.CalledProcessError as e:
            print("=============================================================================\n")
            print(f"Error: Failed to build docker-compose services in {dir_path}")
            print("\n=============================================================================")
            sys.exit(1)

    print("=============================================================================\n")
    print("All docker-compose builds completed successfully.")
    print("\n=============================================================================")

if __name__ == "__main__":
    build_all()
