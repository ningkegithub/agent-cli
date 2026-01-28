import os
import sys
import subprocess
from PIL import Image

# Setup paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) # tests/ 
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # image-to-pdf/
MERGE_SCRIPT = os.path.join(PROJECT_ROOT, 'scripts', 'merge.py')

def create_dummy_image(filename, color):
    img = Image.new('RGB', (100, 100), color=color)
    img.save(filename)

def run_merge_script(args):
    """Runs the merge script as a subprocess."""
    cmd = [sys.executable, MERGE_SCRIPT] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

def test_basic_merge():
    print("--- Test 1: Basic Merge (CLI) ---")
    files = ['t1.png', 't2.png', 't3.png']
    colors = ['red', 'green', 'blue']
    for f, c in zip(files, colors):
        create_dummy_image(f, c)
    
    output = "test_output.pdf"
    if os.path.exists(output): os.remove(output)

    # Execute
    res = run_merge_script([output])
    
    if res.returncode != 0:
        print(f"❌ Script failed: {res.stderr}")
        sys.exit(1)

    # Verify
    if os.path.exists(output):
        print(f"✅ PDF created: {output}")
        print(res.stdout)
    else:
        print(f"❌ PDF not found")
        sys.exit(1)

    # Cleanup
    for f in files: os.remove(f)
    if os.path.exists(output): os.remove(output)

def test_replacement_and_sort():
    print("\n--- Test 2: Merge with Replacement & Sort (CLI) ---")
    # Files: A, B, C. 
    # By default time sort might be messy if created fast.
    # We will use --sort name to ensure order A, B, C
    files = ['A.png', 'B.png', 'C.png', 'Rep.png']
    for f in files:
        create_dummy_image(f, 'white')
    
    output = "test_rep.pdf"
    
    # Replace page 2 (B) with Rep. Sort by name.
    # Expected order: A, Rep, C
    res = run_merge_script([output, '--replace', '2:Rep.png', '--sort', 'name'])
    
    if res.returncode != 0:
        print(f"❌ Script failed: {res.stderr}")
        sys.exit(1)
        
    if "Replacing Page 2 (B.png) with Rep.png" in res.stdout:
        print("✅ Replacement logic verified in stdout")
    else:
        print("❌ Replacement output missing")
        print(res.stdout)

    if os.path.exists(output):
        print(f"✅ PDF created: {output}")
    
    # Cleanup
    for f in files: os.remove(f)
    if os.path.exists(output): os.remove(output)

if __name__ == "__main__":
    test_basic_merge()
    test_replacement_and_sort()