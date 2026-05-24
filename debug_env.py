import os
from dotenv import load_dotenv

def find_problematic_env():
    print("Searching for .env files...")
    for root, dirs, files in os.walk("."):
        if ".env" in files:
            env_path = os.path.join(root, ".env")
            print(f"Found .env at: {env_path}")
            try:
                with open(env_path, "rb") as f:
                    content = f.read()
                    print(f"  Size: {len(content)} bytes")
                    print(f"  First 10 bytes: {content[:10]}")
                # Try loading it
                load_dotenv(env_path)
                print(f"  Status: Loaded successfully")
            except Exception as e:
                print(f"  Status: ERROR - {e}")

if __name__ == "__main__":
    find_problematic_env()
