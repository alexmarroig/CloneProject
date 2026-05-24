import dotenv
import os

original_parse_stream = dotenv.parser.parse_stream

def patched_parse_stream(stream):
    try:
        # Get the file path if possible
        name = getattr(stream, 'name', 'Unknown')
        print(f"DEBUG: Attempting to parse stream from: {name}")
    except:
        pass
    return original_parse_stream(stream)

dotenv.parser.parse_stream = patched_parse_stream

try:
    print("Running load_dotenv()...")
    dotenv.load_dotenv()
    print("load_dotenv() completed (unexpectedly succeeded).")
except Exception as e:
    print(f"\nCAUGHT ERROR: {e}")
    import traceback
    traceback.print_exc()
