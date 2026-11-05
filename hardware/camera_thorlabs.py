# -*- coding: utf-8 -*-
"""
Thorlabs sCMOS camera wrapper for pyCPL (Thorlabs CS2100M-USB).
Controls acquisition and exposure through Thorlabs TLCameraSDK.
"""
import os
import platform
import sys
import numpy as np
from hardware.camera_base import BaseCamera

# Enregistrement du répertoire des DLLs Thorlabs pour Windows (Python >= 3.8)
_dll_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "sCMOS_Thorlabs"))
if platform.system() == "Windows" and os.path.isdir(_dll_dir):
    if hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(_dll_dir)
        except OSError:
            pass
    os.environ["PATH"] = _dll_dir + os.pathsep + os.environ.get("PATH", "")

try:
    from hardware.sCMOS_Thorlabs.tl_camera import TLCameraSDK
    HAS_THORLABS_SDK = True
except (ImportError, OSError):
    try:
        from thorlabs_tsi_sdk.tl_camera import TLCameraSDK
        HAS_THORLABS_SDK = True
    except (ImportError, OSError):
        HAS_THORLABS_SDK = False


class CameraThorlabs(BaseCamera):
    """
    Thorlabs CS2100M-USB sCMOS scientific camera controller.
    """
    def __init__(self, full_well=23000, adc_bits=16):
        # Le capteur physique natif est en 1920 x 1080.
        # Le montage optique à 90 deg oriente la dispersion spectrale selon les colonnes (1080)
        # et la separation spatiale des voies polarisees selon les lignes (1920).
        super().__init__(width=1080, height=1920, full_well=full_well, adc_bits=adc_bits)
        self.sdk = None
        self.camera = None
        self.connect()

    def connect(self):
        """Discover and open connection to first available Thorlabs sCMOS camera."""
        if not HAS_THORLABS_SDK:
            raise ImportError(
                "Thorlabs TLCameraSDK is not installed or libraries (.dll/.so) were not found. "
                "Ensure Thorlabs TSI SDK DLLs are placed in hardware/sCMOS_Thorlabs/, "
                "or run pyCPL with --dummy."
            )

        self.sdk = TLCameraSDK()
        available_cameras = self.sdk.discover_available_cameras()
        if len(available_cameras) == 0:
            self.shutdown()
            raise RuntimeError("No Thorlabs camera detected. Check USB3 connection and power.")

        self.camera = self.sdk.open_camera(available_cameras[0])
        self.camera.frames_per_trigger_zero_for_unlimited = 0
        self.camera.image_poll_timeout_ms = 5000
        self.set_exposure(100.0)

    def snap(self) -> np.ndarray:
        """
        Trigger and retrieve a single 2D sCMOS frame.
        Applies transposition and vertical flip to match optical dispersion geometry.
        """
        if self.camera is None:
            raise RuntimeError("Thorlabs camera is not connected.")

        old_roi = self.camera.roi
        try:
            self.camera.arm(2)
            self.camera.issue_software_trigger()
            frame = self.camera.get_pending_frame_or_null()
            if frame is None:
                raise TimeoutError("Thorlabs camera timed out while waiting for frame buffer.")

            # Orientation optique du capteur sur le banc :
            # Transposition (1080, 1920) -> (1920, 1080), puis retournement sur l'axe 1
            buffer_copy = np.copy(frame.image_buffer)
            self.current_image = np.flip(np.transpose(buffer_copy), axis=1).astype(np.float32)
            self.height, self.width = self.current_image.shape
            return self.current_image
        finally:
            self.camera.disarm()
            self.camera.roi = old_roi

    def set_exposure(self, exposure_ms: float):
        """Set sensor exposure time in milliseconds."""
        self.exposure_ms = float(exposure_ms)
        if self.camera is not None:
            self.camera.exposure_time_us = int(self.exposure_ms * 1000.0)

    def get_exposure(self) -> float:
        """Read actual exposure time in milliseconds from hardware."""
        if self.camera is not None:
            self.exposure_ms = float(self.camera.exposure_time_us) / 1000.0
        return self.exposure_ms

    def shutdown(self):
        """Release camera and dispose SDK instance."""
        if self.camera is not None:
            try:
                self.camera.dispose()
            except Exception:
                pass
            self.camera = None

        if self.sdk is not None:
            try:
                self.sdk.dispose()
            except Exception:
                pass
            self.sdk = None
