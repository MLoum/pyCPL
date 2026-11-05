# -*- coding: utf-8 -*-
"""
Standard abstract base class defining the hardware camera interface.
"""
import numpy as np


class BaseCamera:
    """
    Standard camera interface for pyCPL.
    All hardware drivers must inherit from this class.
    """
    def __init__(self, width=1080, height=1920, full_well=23000, adc_bits=16):
        self.width = width
        self.height = height
        self.full_well = full_well
        self.adc_max = (2 ** adc_bits) - 1
        self.electrons_per_count = float(self.full_well) / float(self.adc_max)
        self.current_image = np.zeros((self.height, self.width), dtype=np.float32)
        self.exposure_ms = 100.0

    def connect(self):
        """Initialize connection to hardware."""
        pass

    def snap(self) -> np.ndarray:
        """
        Acquire a single 2D image and update self.current_image.
        Returns the acquired 2D numpy array.
        """
        raise NotImplementedError("snap() must be implemented by subclass")

    def set_exposure(self, exposure_ms: float):
        """Set exposure time in milliseconds."""
        self.exposure_ms = float(exposure_ms)

    def get_exposure(self) -> float:
        """Get exposure time in milliseconds."""
        return self.exposure_ms

    def shutdown(self):
        """Safely close camera connection and release resources."""
        pass
