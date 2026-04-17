import subprocess
import os
import sys

def run_ingestion():
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Path to the main ingestion script
    main_script = os.path.join(project_root, "src", "ingestion", "main.py")
    
    print("=" * 60)
    print("Triggering Ingestion Pipeline Locally")
    print("=" * 60)
    
    # Run the ingestion script using the current python interpreter
    # This ensures and virtual environment is used if the script is run from one
    try:
        # We run it as a module or directly. Since main.py has __main__ block, we can run it directly.
        # We use sys.executable to ensure we use the same Python environment.
        process = subprocess.Popen(
            [sys.executable, main_script],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Stream the output to the console in real-time
        for line in process.stdout:
            print(line, end="")
            
        process.wait()
        
        if process.returncode == 0:
            print("\n" + "=" * 60)
            print("Local Ingestion Triggered Successfully")
            print("Check 'logs/' directory for detailed activity logs")
            print("=" * 60)
        else:
            print(f"\nIngestion failed with exit code {process.returncode}")
            
    except Exception as e:
        print(f"Error triggering ingestion: {e}")

if __name__ == "__main__":
    run_ingestion()
