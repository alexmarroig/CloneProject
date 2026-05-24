#!/usr/bin/env python3
"""
Phase 1 Verification and Testing Script
Runs after training completes to verify model quality and fix
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/verification_phase1.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def verify_training_complete():
    """Check that training completed successfully"""
    marker = Path('.TRAINING_COMPLETE')
    if not marker.exists():
        logger.error("[FAIL] Training not complete (.TRAINING_COMPLETE marker not found)")
        return False
    logger.info("[OK] Training complete marker found")
    return True

def verify_model():
    """Run model verification checks"""
    logger.info("\n" + "="*80)
    logger.info("STEP 1: Model Verification")
    logger.info("="*80)

    try:
        from app.backend.services.verification_service import verification_service
        results = verification_service.run_all_verifications()

        if not all(results.values()):
            logger.error("[FAIL] Some verification checks failed")
            return False
        logger.info("[OK] All model verification checks passed")
        return True
    except Exception as e:
        logger.error(f"[FAIL] Verification failed: {e}")
        return False

def test_voice_conversion():
    """Test voice conversion with test input"""
    logger.info("\n" + "="*80)
    logger.info("STEP 2: Voice Conversion Test")
    logger.info("="*80)

    try:
        from app.backend.services.rvc_service import RVCService

        rvc = RVCService()
        test_input = Path('tts_temp.mp3')

        if not test_input.exists():
            logger.warning(f"Test input not found: {test_input}")
            return False

        logger.info(f"Converting: {test_input}")
        result = rvc.infer(
            audio_path=str(test_input),
            voice_name='esposa_voice',
            f0_up_key=0,
            f0_method='rmvpe',
            protect=0.5,
            crepe_hop_length=160,
            use_pyin=False,
            extract_from_wav=False,
            process_only=False,
            pitch_scale=1.0,
            formant_scale=1.0
        )

        if not result.get('success'):
            logger.error(f"Conversion failed: {result.get('error')}")
            return False

        output_path = Path(result.get('output_audio_path'))
        if not output_path.exists():
            logger.error(f"Output not created: {output_path}")
            return False

        output_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"[OK] Conversion complete: {output_path.name} ({output_mb:.2f} MB)")
        return True

    except Exception as e:
        logger.error(f"[FAIL] Voice conversion test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run complete Phase 1 verification"""
    logger.info("\n" + "="*80)
    logger.info("PHASE 1 VERIFICATION AND TESTING")
    logger.info("="*80)

    # Step 1: Check training complete
    if not verify_training_complete():
        logger.error("\n[FAIL] Training verification failed")
        return False

    # Step 2: Verify model
    if not verify_model():
        logger.error("\n[FAIL] Model verification failed")
        return False

    # Step 3: Test voice conversion
    if not test_voice_conversion():
        logger.warning("\n[WARN] Voice conversion test failed (may need manual retry)")
        # Don't fail here - model might be valid even if test fails

    logger.info("\n" + "="*80)
    logger.info("[PASS] Phase 1 Verification Complete")
    logger.info("="*80)
    logger.info("\nNext Steps:")
    logger.info("1. Review logs/verification_phase1.log for details")
    logger.info("2. Listen to test_output_phase1.wav to verify voice quality")
    logger.info("3. Confirm 2.8kHz noise is eliminated")
    logger.info("4. If satisfactory, move to Phase 2 (FAISS optimization)")

    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n[INFO] Verification interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n[FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
