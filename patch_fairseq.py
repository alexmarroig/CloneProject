import os
from dataclasses import field

target = r'C:\Users\gaming\AppData\Local\Programs\Python\Python311\Lib\site-packages\fairseq\dataclass\configs.py'
if not os.path.exists(target):
    print(f"File {target} not found")
    exit(1)

content = open(target, 'r').read()

# Define the replacements as a list of (target, replacement) tuples
replacements = [
    ('common: CommonConfig = CommonConfig()', 'common: "CommonConfig" = field(default_factory=lambda: CommonConfig())'),
    ('common_eval: CommonEvalConfig = CommonEvalConfig()', 'common_eval: "CommonEvalConfig" = field(default_factory=lambda: CommonEvalConfig())'),
    ('distributed_training: DistributedTrainingConfig = DistributedTrainingConfig()', 'distributed_training: "DistributedTrainingConfig" = field(default_factory=lambda: DistributedTrainingConfig())'),
    ('dataset: DatasetConfig = DatasetConfig()', 'dataset: "DatasetConfig" = field(default_factory=lambda: DatasetConfig())'),
    ('optimization: OptimizationConfig = OptimizationConfig()', 'optimization: "OptimizationConfig" = field(default_factory=lambda: OptimizationConfig())'),
    ('checkpoint: CheckpointConfig = CheckpointConfig()', 'checkpoint: "CheckpointConfig" = field(default_factory=lambda: CheckpointConfig())'),
    ('bmuf: FairseqBMUFConfig = FairseqBMUFConfig()', 'bmuf: "FairseqBMUFConfig" = field(default_factory=lambda: FairseqBMUFConfig())'),
    ('generation: GenerationConfig = GenerationConfig()', 'generation: "GenerationConfig" = field(default_factory=lambda: GenerationConfig())'),
    ('eval_lm: EvalLMConfig = EvalLMConfig()', 'eval_lm: "EvalLMConfig" = field(default_factory=lambda: EvalLMConfig())'),
    ('interactive: InteractiveConfig = InteractiveConfig()', 'interactive: "InteractiveConfig" = field(default_factory=lambda: InteractiveConfig())'),
    ('ema: EMAConfig = EMAConfig()', 'ema: "EMAConfig" = field(default_factory=lambda: EMAConfig())'),
]

for old, new in replacements:
    content = content.replace(old, new)

with open(target, 'w') as f:
    f.write(content)

print("Patch applied successfully")
