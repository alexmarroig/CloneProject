import os
import shutil

exp_dir = "esposa_voice"
v = "v2"
sr = "40k"

# Directories
logs_dir = os.path.join(os.getcwd(), "logs", exp_dir)
gt_dir = os.path.join(logs_dir, "0_gt_wavs")
f0_dir = os.path.join(logs_dir, "2a_f0")
f0nsf_dir = os.path.join(logs_dir, "2b-f0nsf")
feat_dir = os.path.join(logs_dir, "3_feature768" if v == "v2" else "3_feature256")

# Copy config
config_src = os.path.join("configs", v, f"{sr}.json")
config_dst = os.path.join(logs_dir, "config.json")
shutil.copyfile(config_src, config_dst)

# Generate filelist
opt = []
names = []
for name in os.listdir(gt_dir):
    if name.endswith(".wav"):
        base_name = name.split(".")[0]
        names.append(base_name)

for name in names:
    p_gt = os.path.join(gt_dir, f"{name}.wav").replace("\\", "/")
    p_feat = os.path.join(feat_dir, f"{name}.npy").replace("\\", "/")
    p_f0 = os.path.join(f0_dir, f"{name}.wav.npy").replace("\\", "/")
    p_f0nsf = os.path.join(f0nsf_dir, f"{name}.wav.npy").replace("\\", "/")
    if os.path.exists(p_gt) and os.path.exists(p_feat) and os.path.exists(p_f0) and os.path.exists(p_f0nsf):
        opt.append(f"{p_gt}|{p_feat}|{p_f0}|{p_f0nsf}|0")

# Add mute sample for silence handling
mute_gt = os.path.join(os.getcwd(), "logs", "mute", "0_gt_wavs", f"mute{sr}.wav").replace("\\", "/")
mute_feat = os.path.join(os.getcwd(), "logs", "mute", "3_feature768" if v == "v2" else "3_feature256", "mute.npy").replace("\\", "/")
mute_f0 = os.path.join(os.getcwd(), "logs", "mute", "2a_f0", "mute.wav.npy").replace("\\", "/")
mute_f0nsf = os.path.join(os.getcwd(), "logs", "mute", "2b-f0nsf", "mute.wav.npy").replace("\\", "/")

if os.path.exists(mute_gt):
    opt.append(f"{mute_gt}|{mute_feat}|{mute_f0}|{mute_f0nsf}|0")

with open(os.path.join(logs_dir, "filelist.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(opt))

print(f"Generated filelist.txt with {len(opt)} entries.")
