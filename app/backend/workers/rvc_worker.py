from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

import faiss
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.backend.core.timeutils import utc_now_iso

RVC_ROOT = ROOT
LOGS_DIR = RVC_ROOT / "logs"
CONFIGS_DIR = RVC_ROOT / "configs"
WEIGHTS_DIR = RVC_ROOT / "assets" / "weights"
INDICES_DIR = RVC_ROOT / "assets" / "indices"
VOICE_MODELS_DIR = ROOT / "app" / "models" / "voices"
PYTHON = sys.executable

SR_MAP = {"32k": 32000, "40k": 40000, "48k": 48000}
MAX_INFERENCE_CACHE = 2
_VC_CACHE: OrderedDict[str, object] = OrderedDict()


def run(cmd: list[str], env: dict[str, str] | None = None, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        cmd,
        cwd=str(RVC_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "Command failed")
    return completed


def exp_dir(voice_name: str) -> Path:
    return LOGS_DIR / voice_name


def feature_dir(voice_name: str, version: str) -> Path:
    return exp_dir(voice_name) / ("3_feature256" if version == "v1" else "3_feature768")


def write_training_files(voice_name: str, sample_rate: str, version: str, learning_rate: float, mixed_precision: bool, epochs: int = 200) -> None:
    import json as _json

    current_exp = exp_dir(voice_name)
    gt_wavs_dir = current_exp / "0_gt_wavs"
    feats_dir = feature_dir(voice_name, version)
    f0_dir = current_exp / "2a_f0"
    f0nsf_dir = current_exp / "2b-f0nsf"
    names = (
        {p.stem for p in gt_wavs_dir.glob("*.wav")}
        & {p.stem for p in feats_dir.glob("*.npy")}
        & {p.stem.replace(".wav", "") for p in f0_dir.glob("*.npy")}
        & {p.stem.replace(".wav", "") for p in f0nsf_dir.glob("*.npy")}
    )
    if not names:
        raise RuntimeError("No aligned training items found after feature extraction")

    mute_fea_dim = "256" if version == "v1" else "768"
    lines = []
    for name in sorted(names):
        lines.append(
            f"{gt_wavs_dir.as_posix()}/{name}.wav|{feats_dir.as_posix()}/{name}.npy|{f0_dir.as_posix()}/{name}.wav.npy|{f0nsf_dir.as_posix()}/{name}.wav.npy|0"
        )
    for _ in range(2):
        lines.append(
            f"{RVC_ROOT.as_posix()}/logs/mute/0_gt_wavs/mute{sample_rate}.wav|{RVC_ROOT.as_posix()}/logs/mute/3_feature{mute_fea_dim}/mute.npy|{RVC_ROOT.as_posix()}/logs/mute/2a_f0/mute.wav.npy|{RVC_ROOT.as_posix()}/logs/mute/2b-f0nsf/mute.wav.npy|0"
        )
    (current_exp / "filelist.txt").write_text("\n".join(lines), encoding="utf-8")

    config_path = CONFIGS_DIR / ("v1" if version == "v1" or sample_rate == "40k" else "v2") / f"{sample_rate}.json"
    config_save_path = current_exp / "config.json"
    if not config_save_path.exists():
        config_save_path.write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        config_data = _json.loads(config_save_path.read_text(encoding="utf-8"))
        config_data.setdefault("train", {})
        config_data["train"]["epochs"] = epochs
        config_data["train"]["learning_rate"] = learning_rate
        config_data["train"]["fp16_run"] = bool(mixed_precision)
        config_save_path.write_text(_json.dumps(config_data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def latest_voice_weight(voice_name: str) -> Path:
    # Look for trained model in both locations:
    # 1. First check assets/weights/ (for manually placed models)
    # Match both "esposa_voice.pth" and "esposa_voice_*.pth" patterns
    candidates = sorted(WEIGHTS_DIR.glob(f"{voice_name}*.pth"), key=lambda p: p.stat().st_mtime, reverse=True)
    if candidates:
        return candidates[0]

    # 2. If not found, look for checkpoint in logs directory (from recent training)
    logs_dir = LOGS_DIR / voice_name
    checkpoint_candidates = sorted(logs_dir.glob("G_*.pth"), key=lambda p: p.stat().st_mtime, reverse=True)
    if checkpoint_candidates:
        return checkpoint_candidates[0]

    # 3. If still not found, raise error
    raise RuntimeError(f"No trained weight found for {voice_name} in {WEIGHTS_DIR} or {logs_dir}")


def preprocess(payload: dict) -> dict:
    sr = SR_MAP[payload["sample_rate"]]
    out = exp_dir(payload["voice_name"])
    out.mkdir(parents=True, exist_ok=True)
    run([
        PYTHON,
        "infer/modules/train/preprocess.py",
        payload["dataset_path"],
        str(sr),
        "4",
        str(out),
        "True",
        "3.7",
        "True" if payload.get("normalize", True) else "False",
        str(payload.get("min_audio_seconds", 0.0)),
        str(payload.get("max_audio_seconds", 0.0)),
        "True" if payload.get("silence_slicing", True) else "False",
    ])
    return {"status": "ok"}


def extract_pitch(payload: dict) -> dict:
    run([
        PYTHON,
        "infer/modules/train/extract/extract_f0_print.py",
        str(exp_dir(payload["voice_name"])),
        "4",
        payload["f0_method"],
    ])
    return {"status": "ok"}


def extract_features(payload: dict) -> dict:
    device = payload.get("device", "cpu")
    if device == "cuda":
        gpu_index = str(payload.get("gpu_index") or "0")
        args = [
            PYTHON,
            "infer/modules/train/extract_feature_print.py",
            device,
            "1",
            "0",
            gpu_index,
            str(exp_dir(payload["voice_name"])),
            payload["version"],
            "True",
        ]
    else:
        args = [
            PYTHON,
            "infer/modules/train/extract_feature_print.py",
            device,
            "1",
            "0",
            str(exp_dir(payload["voice_name"])),
            payload["version"],
            "False",
        ]
    run(args)
    if not any(feature_dir(payload["voice_name"], payload["version"]).glob("*.npy")):
        raise RuntimeError("Feature extraction completed without output files")
    return {"status": "ok"}


def train_model(payload: dict) -> dict:
    voice_name = payload["voice_name"]
    sample_rate = payload["sample_rate"]
    version = payload["version"]
    write_training_files(
        voice_name,
        sample_rate,
        version,
        learning_rate=float(payload.get("learning_rate", 0.0001)),
        mixed_precision=bool(payload.get("mixed_precision", False)),
        epochs=int(payload.get("epochs", 200)),
    )
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    # PyTorch on Windows CPU can request libuv even when the wheel is built without it.
    # Forcing this off prevents the hidden child-process crash in train.py.
    env["USE_LIBUV"] = "0"
    # Ensure FFmpeg is in PATH for train.py
    ffmpeg_dir = str(RVC_ROOT.parent)
    if ffmpeg_dir not in env.get("PATH", ""):
        env["PATH"] = f"{ffmpeg_dir}{os.pathsep}{env.get('PATH', '')}"
    gpus = str(payload.get("gpu_index") or "0") if payload.get("device") == "cuda" else ""
    batch_size = max(1, int(payload.get("batch_size", 1)))
    save_every_epoch = max(1, int(payload.get("save_every_epoch", max(1, min(10, payload["epochs"])))))
    run([
        PYTHON,
        "infer/modules/train/train.py",
        "-e",
        voice_name,
        "-sr",
        sample_rate,
        "-f0",
        "1",
        "-bs",
        str(batch_size),
        "-g",
        gpus,
        "-te",
        str(payload["epochs"]),
        "-se",
        str(save_every_epoch),
        "-pg",
        "",
        "-pd",
        "",
        "-l",
        "1",
        "-c",
        "0",
        "-sw",
        "1",
        "-v",
        version,
    ], env=env)
    weight = latest_voice_weight(voice_name)
    voice_dir = VOICE_MODELS_DIR / voice_name
    voice_dir.mkdir(parents=True, exist_ok=True)
    model_target = voice_dir / "model.pth"
    shutil.copy2(weight, model_target)
    return {"model_path": str(model_target)}


def build_index(payload: dict) -> dict:
    voice_name = payload["voice_name"]
    version = payload["version"]
    feats = []
    for item in sorted(feature_dir(voice_name, version).glob("*.npy")):
        feats.append(np.load(item))
    if not feats:
        raise RuntimeError("No features found to build index")
    big_npy = np.concatenate(feats, axis=0)
    if big_npy.shape[0] > 200000:
        from sklearn.cluster import MiniBatchKMeans

        big_npy = MiniBatchKMeans(n_clusters=10000, batch_size=256, compute_labels=False, init="random").fit(big_npy).cluster_centers_
    np.save(exp_dir(voice_name) / "total_fea.npy", big_npy)
    n_ivf = min(int(16 * np.sqrt(big_npy.shape[0])), max(1, big_npy.shape[0] // 39))
    index = faiss.index_factory(256 if version == "v1" else 768, f"IVF{n_ivf},Flat")
    index_ivf = faiss.extract_index_ivf(index)
    index_ivf.nprobe = 1
    index.train(big_npy)
    trained_path = exp_dir(voice_name) / f"trained_IVF{n_ivf}_Flat_nprobe_{index_ivf.nprobe}_{voice_name}_{version}.index"
    faiss.write_index(index, str(trained_path))
    for start in range(0, big_npy.shape[0], 8192):
        index.add(big_npy[start : start + 8192])
    added_path = exp_dir(voice_name) / f"added_IVF{n_ivf}_Flat_nprobe_{index_ivf.nprobe}_{voice_name}_{version}.index"
    faiss.write_index(index, str(added_path))

    voice_dir = VOICE_MODELS_DIR / voice_name
    voice_dir.mkdir(parents=True, exist_ok=True)
    index_target = voice_dir / "model.index"
    shutil.copy2(added_path, index_target)
    try:
        INDICES_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(added_path, INDICES_DIR / added_path.name)
    except Exception:
        pass
    return {"index_path": str(index_target)}


def convert(payload: dict) -> dict:
    input_path = Path(payload["input_path"])
    output_path = Path(payload["output_path"])
    model_path = Path(payload["model_path"])
    index_path = Path(payload["index_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["weight_root"] = str(model_path.parent)
    env["index_root"] = str(index_path.parent)
    env["outside_index_root"] = str(index_path.parent)
    env["weight_uvr5_root"] = str(RVC_ROOT / "assets" / "uvr5_weights")
    env["rmvpe_root"] = str(RVC_ROOT / "assets" / "rmvpe")
    torch_device = payload.get("torch_device") or payload.get("device", "cpu")

    if payload.get("enable_cache", True):
        try:
            from scipy.io import wavfile
            from configs.config import Config
            from infer.modules.vc.modules import VC

            cache_key = f"{model_path.resolve()}::{torch_device}"
            vc = _VC_CACHE.get(cache_key)
            if vc is None:
                argv = list(sys.argv)
                try:
                    sys.argv = [argv[0]]
                    config = Config()
                finally:
                    sys.argv = argv
                config.device = torch_device
                if torch_device in {"cpu", "mps"}:
                    config.is_half = False
                os.environ.update(env)
                vc = VC(config)
                vc.get_vc(model_path.name)
                _VC_CACHE[cache_key] = vc
                _VC_CACHE.move_to_end(cache_key, last=True)
                while len(_VC_CACHE) > MAX_INFERENCE_CACHE:
                    _VC_CACHE.popitem(last=False)
            else:
                _VC_CACHE.move_to_end(cache_key, last=True)

            os.environ.update(env)
            info, audio = vc.vc_single(
                0,
                str(input_path),
                int(payload.get("pitch_shift", 0)),
                None,
                payload.get("f0_method", "rmvpe"),
                str(index_path),
                None,
                float(payload.get("index_rate", 0.66)),
                int(payload.get("filter_radius", 3)),
                int(payload.get("resample_rate", 0)),
                float(payload.get("rms_mix_rate", 1.0)),
                float(payload.get("protect_consonants", 0.33)),
            )
            if not audio or audio[0] is None:
                raise RuntimeError(info)
            wavfile.write(str(output_path), int(audio[0]), audio[1])
            return {"output_path": str(output_path), "cached": True}
        except Exception:
            # Fall back to infer_cli path if cached in-process conversion fails.
            pass

    run([
        PYTHON,
        "tools/infer_cli.py",
        "--input_path",
        str(input_path),
        "--index_path",
        str(index_path),
        "--opt_path",
        str(output_path),
        "--model_name",
        model_path.name,
        "--f0up_key",
        str(payload.get("pitch_shift", 0)),
        "--index_rate",
        str(payload.get("index_rate", 0.66)),
        "--f0method",
        payload.get("f0_method", "rmvpe"),
        "--filter_radius",
        str(payload.get("filter_radius", 3)),
        "--resample_sr",
        str(payload.get("resample_rate", 0)),
        "--rms_mix_rate",
        str(payload.get("rms_mix_rate", 1)),
        "--protect",
        str(payload.get("protect_consonants", 0.33)),
        "--device",
        torch_device,
    ], env=env)
    return {"output_path": str(output_path)}


def handle_payload(payload: dict) -> dict:
    mode = payload["mode"]
    actions = {
        "convert": convert,
        "preprocess": preprocess,
        "extract_pitch": extract_pitch,
        "extract_features": extract_features,
        "train": train_model,
        "build_index": build_index,
    }
    result = actions[mode](payload)
    if mode == "train":
        result.update({"created_at": utc_now_iso()})
    return result


def daemon_loop() -> None:
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
            result = handle_payload(payload)
            message = {"ok": True, "result": result}
        except Exception as exc:
            message = {"ok": False, "error": str(exc)}
        print(json.dumps(message, ensure_ascii=False), flush=True)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        daemon_loop()
        return
    payload = json.loads(sys.argv[1])
    result = handle_payload(payload)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
