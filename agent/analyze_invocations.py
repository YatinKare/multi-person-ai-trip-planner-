
import glob
import os

def analyze():
    files = glob.glob('**/*.py', recursive=True)
    for f in files:
        if 'tmp/' in f or '.venv' in f:
            continue
        try:
            with open(f, 'r') as file:
                content = file.read()
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if '.invoke(' in line or '.run(' in line or '.run_async(' in line:
                        print(f"{f}:{i+1}: {line.strip()}")
        except Exception as e:
            print(f"Error reading {f}: {e}")

if __name__ == "__main__":
    analyze()
