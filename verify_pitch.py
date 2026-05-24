import librosa
import numpy as np

def get_pitch(path):
    y, sr = librosa.load(path, sr=None)
    f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=50, fmax=500, sr=sr)
    f0_filtered = f0[voiced_flag]
    if len(f0_filtered) == 0:
        return 0
    return np.median(f0_filtered)

input_pitch = get_pitch("reels_audio_esposa_voice.wav")
target_pitch = get_pitch("dataset_alex/voice.wav")

print(f"Input Pitch Median: {input_pitch:.2f} Hz")
print(f"Target Pitch Median: {target_pitch:.2f} Hz")

if input_pitch > 0 and target_pitch > 0:
    # f0up_key = 12 * log2(target / input)
    semitones = 12 * np.log2(target_pitch / input_pitch)
    print(f"Suggested f0up_key: {semitones:.2f} semitones")
else:
    print("Could not detect pitch in one of the files.")
