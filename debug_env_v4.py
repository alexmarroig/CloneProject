import dotenv
import os

path = dotenv.find_dotenv()
print(f"PATH_START:{path}:PATH_END")

if path and os.path.exists(path):
    with open(path, 'rb') as f:
        print(f"BYTES_START:{f.read(20)}:BYTES_END")
