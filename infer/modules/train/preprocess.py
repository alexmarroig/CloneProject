import multiprocessing
import os
import sys

from scipy import signal

now_dir = os.getcwd()
sys.path.append(now_dir)
print(*sys.argv[1:])
inp_root = sys.argv[1]
sr = int(sys.argv[2])
n_p = int(sys.argv[3])
exp_dir = sys.argv[4]
noparallel = sys.argv[5] == "True"
per = float(sys.argv[6])
normalize_audio = sys.argv[7] == "True" if len(sys.argv) > 7 else True
min_audio_seconds = float(sys.argv[8]) if len(sys.argv) > 8 else 0.0
max_audio_seconds = float(sys.argv[9]) if len(sys.argv) > 9 else 0.0
enable_slicing = sys.argv[10] == "True" if len(sys.argv) > 10 else True
import os
import traceback

import librosa
import numpy as np
from scipy.io import wavfile

from infer.lib.audio import load_audio
from infer.lib.slicer2 import Slicer

f = open("%s/preprocess.log" % exp_dir, "a+")


def println(strr):
    print(strr)
    f.write("%s\n" % strr)
    f.flush()


class PreProcess:
    def __init__(self, sr, exp_dir, per=3.7, normalize_audio=True, min_audio_seconds=0.0, max_audio_seconds=0.0, enable_slicing=True):
        self.slicer = Slicer(
            sr=sr,
            threshold=-42,
            min_length=1500,
            min_interval=400,
            hop_size=15,
            max_sil_kept=500,
        )
        self.sr = sr
        self.bh, self.ah = signal.butter(N=5, Wn=48, btype="high", fs=self.sr)
        self.per = per
        self.overlap = 0.3
        self.tail = self.per + self.overlap
        self.max = 0.9
        self.alpha = 0.75
        self.normalize_audio = normalize_audio
        self.min_audio_seconds = min_audio_seconds
        self.max_audio_seconds = max_audio_seconds
        self.enable_slicing = enable_slicing
        self.exp_dir = exp_dir
        self.gt_wavs_dir = "%s/0_gt_wavs" % exp_dir
        self.wavs16k_dir = "%s/1_16k_wavs" % exp_dir
        os.makedirs(self.exp_dir, exist_ok=True)
        os.makedirs(self.gt_wavs_dir, exist_ok=True)
        os.makedirs(self.wavs16k_dir, exist_ok=True)

    def norm_write(self, tmp_audio, idx0, idx1):
        tmp_max = np.abs(tmp_audio).max()
        if tmp_max == 0:
            return
        if tmp_max > 2.5:
            print("%s-%s-%s-filtered" % (idx0, idx1, tmp_max))
            return
        if self.normalize_audio:
            tmp_audio = (tmp_audio / tmp_max * (self.max * self.alpha)) + (
                1 - self.alpha
            ) * tmp_audio
        else:
            tmp_audio = np.clip(tmp_audio, -1.0, 1.0)
        wavfile.write(
            "%s/%s_%s.wav" % (self.gt_wavs_dir, idx0, idx1),
            self.sr,
            tmp_audio.astype(np.float32),
        )
        tmp_audio = librosa.resample(
            tmp_audio, orig_sr=self.sr, target_sr=16000
        )  # , res_type="soxr_vhq"
        wavfile.write(
            "%s/%s_%s.wav" % (self.wavs16k_dir, idx0, idx1),
            16000,
            tmp_audio.astype(np.float32),
        )

    def pipeline(self, path, idx0):
        try:
            audio = load_audio(path, self.sr)
            # zero phased digital filter cause pre-ringing noise...
            # audio = signal.filtfilt(self.bh, self.ah, audio)
            audio = signal.lfilter(self.bh, self.ah, audio)
            chunks = self.slicer.slice(audio) if self.enable_slicing else [audio]

            idx1 = 0
            for audio in chunks:
                i = 0
                should_write_tail = True
                while 1:
                    start = int(self.sr * (self.per - self.overlap) * i)
                    i += 1
                    if len(audio[start:]) > self.tail * self.sr:
                        tmp_audio = audio[start : start + int(self.per * self.sr)]
                        duration_seconds = len(tmp_audio) / float(self.sr)
                        if self.min_audio_seconds > 0 and duration_seconds < self.min_audio_seconds:
                            continue
                        if self.max_audio_seconds > 0 and duration_seconds > self.max_audio_seconds:
                            continue
                        self.norm_write(tmp_audio, idx0, idx1)
                        idx1 += 1
                    else:
                        tmp_audio = audio[start:]
                        duration_seconds = len(tmp_audio) / float(self.sr)
                        if self.min_audio_seconds > 0 and duration_seconds < self.min_audio_seconds:
                            should_write_tail = False
                            break
                        if self.max_audio_seconds > 0 and duration_seconds > self.max_audio_seconds:
                            should_write_tail = False
                            break
                        idx1 += 1
                        break
                if should_write_tail:
                    self.norm_write(tmp_audio, idx0, idx1)
            println("%s\t-> Success" % path)
        except:
            println("%s\t-> %s" % (path, traceback.format_exc()))

    def pipeline_mp(self, infos):
        for path, idx0 in infos:
            self.pipeline(path, idx0)

    def pipeline_mp_inp_dir(self, inp_root, n_p):
        try:
            infos = [
                ("%s/%s" % (inp_root, name), idx)
                for idx, name in enumerate(sorted(list(os.listdir(inp_root))))
            ]
            if noparallel:
                for i in range(n_p):
                    self.pipeline_mp(infos[i::n_p])
            else:
                ps = []
                for i in range(n_p):
                    p = multiprocessing.Process(
                        target=self.pipeline_mp, args=(infos[i::n_p],)
                    )
                    ps.append(p)
                    p.start()
                for i in range(n_p):
                    ps[i].join()
        except:
            println("Fail. %s" % traceback.format_exc())


def preprocess_trainset(inp_root, sr, n_p, exp_dir, per):
    pp = PreProcess(
        sr,
        exp_dir,
        per,
        normalize_audio=normalize_audio,
        min_audio_seconds=min_audio_seconds,
        max_audio_seconds=max_audio_seconds,
        enable_slicing=enable_slicing,
    )
    println("start preprocess")
    pp.pipeline_mp_inp_dir(inp_root, n_p)
    println("end preprocess")


if __name__ == "__main__":
    preprocess_trainset(inp_root, sr, n_p, exp_dir, per)
