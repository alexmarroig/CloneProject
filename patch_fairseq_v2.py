import os

target = r'C:\Users\gaming\AppData\Local\Programs\Python\Python311\Lib\site-packages\fairseq\dataclass\configs.py'
if not os.path.exists(target):
    print(f"File {target} not found")
    exit(1)

content = open(target, 'r').read()

# Define the replacements to bypass dataclass validation issues
replacements = [
    ('common: "CommonConfig" = field(default_factory=lambda: CommonConfig())', 'common: "CommonConfig" = None'),
    ('common_eval: "CommonEvalConfig" = field(default_factory=lambda: CommonEvalConfig())', 'common_eval: "CommonEvalConfig" = None'),
    ('distributed_training: "DistributedTrainingConfig" = field(default_factory=lambda: DistributedTrainingConfig())', 'distributed_training: "DistributedTrainingConfig" = None'),
    ('dataset: "DatasetConfig" = field(default_factory=lambda: DatasetConfig())', 'dataset: "DatasetConfig" = None'),
    ('optimization: "OptimizationConfig" = field(default_factory=lambda: OptimizationConfig())', 'optimization: "OptimizationConfig" = None'),
    ('checkpoint: "CheckpointConfig" = field(default_factory=lambda: CheckpointConfig())', 'checkpoint: "CheckpointConfig" = None'),
    ('bmuf: "FairseqBMUFConfig" = field(default_factory=lambda: FairseqBMUFConfig())', 'bmuf: "FairseqBMUFConfig" = None'),
    ('generation: "GenerationConfig" = field(default_factory=lambda: GenerationConfig())', 'generation: "GenerationConfig" = None'),
    ('eval_lm: "EvalLMConfig" = field(default_factory=lambda: EvalLMConfig())', 'eval_lm: "EvalLMConfig" = None'),
    ('interactive: "InteractiveConfig" = field(default_factory=lambda: InteractiveConfig())', 'interactive: "InteractiveConfig" = None'),
    ('ema: "EMAConfig" = field(default_factory=lambda: EMAConfig())', 'ema: "EMAConfig" = None'),
]

for old, new in replacements:
    content = content.replace(old, new)

with open(target, 'w') as f:
    f.write(content)

print("Patch v2 applied successfully")
