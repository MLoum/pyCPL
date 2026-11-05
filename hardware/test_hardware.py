# -*- coding: utf-8 -*-
"""
Standalone diagnostic test script for pyCPL hardware devices.
Tests camera and rotation stage individually.

Usage:
    python hardware/test_hardware.py --camera dummy --rotator dummy
    python hardware/test_hardware.py --camera thorlabs --rotator elliptec --port COM9
"""
import os
import sys
import argparse
import numpy as np

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_camera_test(camera_type="dummy"):
    print(f"\n--- Testing Camera ({camera_type}) ---")
    camera = None
    try:
        if camera_type.lower() == "thorlabs":
            from hardware.camera_thorlabs import CameraThorlabs
            camera = CameraThorlabs()
        else:
            from hardware.camera_dummy import DummyCamera
            camera = DummyCamera()

        print("  [PASS] Camera initialized successfully.")
        print(f"         Dimensions : {camera.height} rows x {camera.width} cols")
        print(f"         Exposure   : {camera.get_exposure():.2f} ms")

        camera.set_exposure(50.0)
        print(f"         Set 50 ms  -> readback: {camera.get_exposure():.2f} ms")

        print("  Capturing single frame...")
        img = camera.snap()
        print("  [PASS] Frame acquired.")
        print(f"         Min intensity  : {np.min(img):.1f} ADU")
        print(f"         Max intensity  : {np.max(img):.1f} ADU")
        print(f"         Mean intensity : {np.mean(img):.1f} ADU")
        return True
    except Exception as e:
        print(f"  [FAIL] Camera error: {e}")
        return False
    finally:
        if camera is not None:
            camera.shutdown()


def run_rotator_test(rotator_type="dummy", port="COM9"):
    print(f"\n--- Testing Rotator Stage ({rotator_type} on {port}) ---")
    rotator = None
    try:
        if rotator_type.lower() == "elliptec":
            from hardware.rotator_elliptec import ElliptecRotator
            rotator = ElliptecRotator(port=port)
        else:
            from hardware.rotator_elliptec import DummyRotator
            rotator = DummyRotator(port=port)

        print("  [PASS] Rotator connected.")
        print(f"         Initial angle: {rotator.get_angle():.2f} deg")

        rotator.set_angle(0.0, settle_time_s=0.1)
        print("         Moved to 0.0 deg.")
        rotator.set_angle(90.0, settle_time_s=0.1)
        print("         Moved to 90.0 deg.")
        rotator.set_angle(0.0, settle_time_s=0.1)
        print("         Returned to 0.0 deg.")
        print("  [PASS] Motion sequence completed successfully.")
        return True
    except Exception as e:
        print(f"  [FAIL] Rotator error: {e}")
        return False
    finally:
        if rotator is not None:
            rotator.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test pyCPL hardware devices.")
    parser.add_argument("--camera", choices=["dummy", "thorlabs"], default="dummy")
    parser.add_argument("--rotator", choices=["dummy", "elliptec"], default="dummy")
    parser.add_argument("--port", default="COM9")
    args = parser.parse_args()

    cam_ok = run_camera_test(args.camera)
    rot_ok = run_rotator_test(args.rotator, args.port)

    print("\n" + "=" * 30)
    print(f"Camera  : {'OK' if cam_ok else 'FAILED'}")
    print(f"Rotator : {'OK' if rot_ok else 'FAILED'}")
    print("=" * 30 + "\n")
    if not (cam_ok and rot_ok):
        sys.exit(1)
