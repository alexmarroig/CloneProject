import os

path = r"C:\Users\gaming\.env"
if os.path.exists(path):
    print(f"Reading {path} as UTF-16...")
    try:
        with open(path, 'rb') as f:
            content = f.read()
        
        # Try decoding as UTF-16 LE (most common for \xff\xfe)
        decoded = content.decode('utf-16')
        print("Successfully decoded as UTF-16.")
        
        print(f"Rewriting {path} as UTF-8...")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(decoded)
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"File not found at {path}")
