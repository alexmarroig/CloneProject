import dotenv
import os

original_find_dotenv = dotenv.main.find_dotenv

def patched_find_dotenv(*args, **kwargs):
    path = original_find_dotenv(*args, **kwargs)
    print(f"DEBUG: find_dotenv returned: {path}")
    return path

dotenv.main.find_dotenv = patched_find_dotenv
dotenv.load_dotenv = patched_find_dotenv # Also try patching other entry points if needed

try:
    print("Running find_dotenv()...")
    path = dotenv.find_dotenv()
    print(f"Path found: {path}")
    
    if path and os.path.exists(path):
        print(f"Checking file encoding for: {path}")
        with open(path, 'rb') as f:
            head = f.read(10)
            print(f"First 10 bytes: {head}")
            
    print("\nRunning load_dotenv()...")
    dotenv.main.load_dotenv()
except Exception as e:
    print(f"\nCAUGHT ERROR: {e}")
    import traceback
    traceback.print_exc()
