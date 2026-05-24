import fairseq.dataclass.configs
from dataclasses import dataclass

try:
    @dataclass
    class Test:
        common: fairseq.dataclass.configs.CommonConfig = fairseq.dataclass.configs.CommonConfig()
    print("Dataclass test: Success")
except ValueError as e:
    print(f"Dataclass test: Failed with {e}")
except Exception as e:
    print(f"Dataclass test: Other error {e}")
