#!/usr/bin/env python3
"""
Voice Data Preparation Script for RVC Training
===============================================

This script helps you:
1. Organize voice recordings
2. Validate audio quality
3. Prepare data for RVC training
4. Check if you have enough data

Usage:
    python prepare_voice_data.py --input <path_to_voice_files> --voice-name esposa_voice
"""

import argparse
import librosa
import numpy as np
from pathlib import Path
import sys
import json
from datetime import datetime


def validate_audio_quality(audio_path, min_duration=1.0, max_duration=600):
    """
    Validate if an audio file is suitable for training.

    Returns:
        dict with validation results
    """
    try:
        y, sr = librosa.load(str(audio_path), sr=None)
        duration = len(y) / sr

        results = {
            "file": audio_path.name,
            "valid": True,
            "duration": duration,
            "sample_rate": sr,
            "issues": []
        }

        # Check duration
        if duration < min_duration:
            results["issues"].append(f"Too short ({duration:.1f}s, need {min_duration}s)")
            results["valid"] = False
        if duration > max_duration:
            results["issues"].append(f"Too long ({duration:.1f}s, max {max_duration}s)")
            results["valid"] = False

        # Check audio quality
        rms = np.sqrt(np.mean(y**2))
        if rms < 0.01:
            results["issues"].append(f"Too quiet (RMS {rms:.4f})")
            results["valid"] = False

        # Check for clipping
        peak = np.max(np.abs(y))
        if peak > 0.99:
            results["issues"].append(f"Possible clipping (peak {peak:.3f})")
            results["valid"] = False

        # Check zero crossing rate (speech detection)
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        if zcr.mean() < 0.03 or zcr.mean() > 0.4:
            results["issues"].append(f"Unusual ZCR {zcr.mean():.3f} (maybe not speech)")
            results["valid"] = False

        # Check for silence ratio
        silent_ratio = np.sum(np.abs(y) < 0.001) / len(y)
        if silent_ratio > 0.5:
            results["issues"].append(f"Too much silence ({silent_ratio*100:.0f}%)")
            results["valid"] = False

        results["rms"] = rms
        results["peak"] = peak
        results["zcr_mean"] = zcr.mean()
        results["silence_ratio"] = silent_ratio

        return results
    except Exception as e:
        return {
            "file": audio_path.name,
            "valid": False,
            "error": str(e),
            "issues": [str(e)]
        }


def analyze_dataset(voice_dir):
    """
    Analyze all audio files in a directory.
    """
    voice_dir = Path(voice_dir)
    if not voice_dir.exists():
        print(f"[ERROR] Directory not found: {voice_dir}")
        return None

    audio_extensions = {'.wav', '.mp3', '.flac', '.m4a'}
    audio_files = [f for f in voice_dir.iterdir()
                   if f.suffix.lower() in audio_extensions]

    if not audio_files:
        print(f"[ERROR] No audio files found in {voice_dir}")
        return None

    print(f"\n{'='*70}")
    print(f"ANALYZING {len(audio_files)} AUDIO FILES")
    print(f"{'='*70}\n")

    results = []
    total_duration = 0
    valid_count = 0

    for audio_file in sorted(audio_files):
        print(f"Checking: {audio_file.name}...", end=" ")
        result = validate_audio_quality(audio_file)
        results.append(result)

        if result["valid"]:
            print(f"[OK] {result['duration']:.1f}s")
            total_duration += result["duration"]
            valid_count += 1
        else:
            print(f"[FAILED]")
            for issue in result["issues"]:
                print(f"  - {issue}")

    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Total files: {len(audio_files)}")
    print(f"Valid files: {valid_count}")
    print(f"Total duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")

    print(f"\nTraining readiness:")
    if total_duration < 10:
        print(f"  [ERROR] Need at least 10 seconds (you have {total_duration:.1f}s)")
        print(f"  Record more voice samples!")
    elif total_duration < 30:
        print(f"  [WARNING] Minimum met ({total_duration:.1f}s) but results may be poor")
        print(f"  Recommended: 30-300 seconds of diverse speech")
    elif total_duration < 300:
        print(f"  [GOOD] {total_duration:.1f}s - should work well")
    else:
        print(f"  [EXCELLENT] {total_duration:.1f}s - optimal for training")

    return {
        "total_files": len(audio_files),
        "valid_files": valid_count,
        "total_duration": total_duration,
        "results": results
    }


def print_recording_guide():
    """
    Print guide for recording voice samples.
    """
    guide = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    HOW TO RECORD VOICE SAMPLES FOR RVC TRAINING             ║
╚══════════════════════════════════════════════════════════════════════════════╝

RECORDING TIPS:
===============

1. ENVIRONMENT
   - Find a quiet room (minimize background noise)
   - Close windows and doors
   - Silence your phone and other devices
   - Avoid echo by using a room with soft furnishings

2. EQUIPMENT
   - Use built-in microphone or USB headset
   - Keep microphone consistent (don't switch between devices)
   - Position microphone 6-12 inches from mouth
   - Avoid touching or moving the microphone while recording

3. VOICE & CONTENT
   - Speak naturally and clearly
   - Record different sentences and topics
   - Use various emotional tones (happy, sad, neutral, excited)
   - Include questions, statements, and exclamations
   - Record for 30 seconds to 5 minutes total

4. SUGGESTED CONTENT TO RECORD:
   - Introduce yourself ("Oi, meu nome é...")
   - Describe daily activities
   - Tell a short story
   - Read a paragraph from a book
   - Have a conversation with natural pauses
   - Express different emotions in the same sentence

5. FILE FORMAT
   - Use WAV format (best quality)
   - Alternative: MP3, FLAC, or M4A
   - Sample rate: 16kHz, 22.05kHz, 44.1kHz, or 48kHz (auto-converted)
   - Mono or stereo (mono preferred for voice)

6. QUALITY CHECKLIST
   - ✓ Minimal background noise
   - ✓ Clear, audible speech
   - ✓ No distortion or clipping
   - ✓ Natural speaking voice
   - ✓ 30+ seconds total duration
   - ✓ Diverse content and emotions

RECORDING STEPS:
================

1. Open your phone's voice recorder or audio recording software
2. Press Record
3. Speak naturally for 30-300 seconds covering:
   - Greeting and introduction
   - Various sentences with different topics
   - Different emotional expressions
   - Natural pauses and conversational tone
4. Stop recording
5. Save as WAV file (e.g., "wife_voice_01.wav")
6. Repeat to get more samples

WHAT NOT TO DO:
================

❌ Don't record in a loud environment
❌ Don't whisper or speak too quietly
❌ Don't record at extremely high volume (risk of clipping)
❌ Don't record monologues without variation
❌ Don't use music or background sounds
❌ Don't record very short clips (less than 1 second)

FILE NAMING:
============

Save your recordings with descriptive names:
  - wife_voice_01.wav
  - esposa_greeting.wav
  - esposa_story.wav
  - wife_emotional_01.wav

AFTER RECORDING:
================

1. Copy all voice files to: app/runtime/datasets/
   (or any folder, then run: python prepare_voice_data.py --input <folder>)

2. Run this script to validate quality:
   python prepare_voice_data.py --input app/runtime/datasets/

3. If validation passes, upload to the web interface for training

TARGET DURATION:
================

  Minimum:  10 seconds  (not recommended, poor results)
  Good:     30 seconds  (okay, reasonable results)
  Better:   1-2 minutes (good quality)
  Best:     5-10 minutes (excellent quality)

TIPS FOR BEST RESULTS:

1. Record in a consistent voice/mood (don't mix calm and energetic)
2. Use clear pronunciation
3. Include varied content (not just one repeated phrase)
4. Ensure steady volume (not too quiet or too loud)
5. Multiple shorter clips (1-2 min each) are better than one long clip
"""
    print(guide)


def main():
    parser = argparse.ArgumentParser(description="Prepare voice data for RVC training")
    parser.add_argument("--input", type=str, help="Path to directory with voice files")
    parser.add_argument("--voice-name", type=str, default="esposa_voice",
                        help="Voice model name (default: esposa_voice)")
    parser.add_argument("--guide", action="store_true",
                        help="Show recording guide")
    parser.add_argument("--export", type=str,
                        help="Export validation report to JSON file")

    args = parser.parse_args()

    # Show guide if requested
    if args.guide or not args.input:
        print_recording_guide()
        if not args.input:
            print("\n[INFO] Use --input <directory> to analyze voice files")
            print("       Use --guide to show this recording guide")
            sys.exit(0)

    # Analyze dataset
    if args.input:
        analysis = analyze_dataset(args.input)

        # Export report if requested
        if args.export and analysis:
            report = {
                "timestamp": datetime.now().isoformat(),
                "voice_name": args.voice_name,
                "analysis": analysis
            }
            with open(args.export, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n[OK] Report saved to: {args.export}")


if __name__ == "__main__":
    main()
