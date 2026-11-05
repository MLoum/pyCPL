# -*- coding: utf-8 -*-
"""
Motorized rotation stage interface for Thorlabs Elliptec ELL14 piezo rotator.
Controls the rotation of the super-achromatic quarter-wave plate (+45 deg / -45 deg).
Uses the embedded local 'elliptec' package located in hardware/elliptec/.
"""
import time

try:
    # 1. Import du package elliptec local embarqué
    from . import elliptec
    HAS_ELLIPTEC = True
except (ImportError, ValueError):
    try:
        from hardware import elliptec
        HAS_ELLIPTEC = True
    except ImportError:
        try:
            import elliptec
            HAS_ELLIPTEC = True
        except ImportError:
            HAS_ELLIPTEC = False


class ElliptecRotator:
    """
    Controller for Thorlabs Elliptec ELL14 rotation stage.
    """
    def __init__(self, port="COM9"):
        self.port = port
        self.current_angle_deg = 0.0
        self.controller = None
        self.rotator = None
        self.connect()

    def connect(self):
        """Connect to the Elliptec serial controller."""
        if not HAS_ELLIPTEC:
            raise ImportError(
                "The 'elliptec' package is missing and 'pyserial' is required. "
                "Ensure hardware/elliptec/ is present and install pyserial via 'pip install pyserial'."
            )
        try:
            self.controller = elliptec.Controller(self.port)
            self.rotator = elliptec.Rotator(self.controller)
            val = self.rotator.get_angle()
            self.current_angle_deg = float(val) if val is not None else 0.0
        except Exception as e:
            self.close()
            raise ConnectionError(f"Failed to connect to Elliptec stage on port {self.port}: {e}")

    def set_angle(self, angle_deg: float, settle_time_s: float = 0.25):
        """
        Move stage to absolute angle in degrees and wait for mechanical settling.
        """
        if self.rotator is None:
            raise RuntimeError("Rotator stage is not connected.")
        target_angle = float(angle_deg)
        self.rotator.set_angle(target_angle)
        self.current_angle_deg = target_angle
        if settle_time_s > 0:
            time.sleep(settle_time_s)

    def get_angle(self) -> float:
        """Query current angular position in degrees."""
        if self.rotator is not None:
            try:
                val = self.rotator.get_angle()
                if val is not None:
                    self.current_angle_deg = float(val)
            except Exception:
                pass
        return self.current_angle_deg

    def close(self):
        """Close serial connection cleanly."""
        if self.controller is not None:
            try:
                self.controller.close_connection()
            except Exception:
                try:
                    self.controller.close()
                except Exception:
                    pass
            self.controller = None
            self.rotator = None


class DummyRotator:
    """
    Virtual rotation stage for offline testing and hardware-free simulation.
    """
    def __init__(self, port="VIRTUAL"):
        self.port = port
        self.current_angle_deg = 0.0
        self.linked_camera = None

    def link_camera(self, camera):
        """Optionally link dummy camera to notify it of angle changes."""
        self.linked_camera = camera

    def set_angle(self, angle_deg: float, settle_time_s: float = 0.05):
        """Simulate rotation to target angle."""
        self.current_angle_deg = float(angle_deg)
        if self.linked_camera is not None and hasattr(self.linked_camera, 'set_rotator_angle'):
            self.linked_camera.set_rotator_angle(self.current_angle_deg)
        if settle_time_s > 0:
            time.sleep(settle_time_s)

    def get_angle(self) -> float:
        return self.current_angle_deg

    def close(self):
        pass
