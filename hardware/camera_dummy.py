# -*- coding: utf-8 -*-
"""
Synthetic dummy camera simulating realistic circularly polarized luminescence
signals, beam spatial splitting, transmission imbalances, and Poisson photon noise.
Allows offline testing and validation without laboratory hardware.
"""
import numpy as np
from hardware.camera_base import BaseCamera


class DummyCamera(BaseCamera):
    """
    Simulated camera producing two spatially separated dispersed tracks
    with configurable emission band, intrinsic dissymmetry factor (glum),
    optical transmission mismatch, and Poisson noise.
    """
    def __init__(self, width=1080, height=1920, full_well=23000, adc_bits=16):
        super().__init__(width=width, height=height, full_well=full_well, adc_bits=adc_bits)
        self.exposure_ms = 100.0
        self.rotator_angle_deg = 0.0

        # Synthetic spectroscopic properties
        self.peak_col = width * 0.48        # Emission peak horizontal position
        self.peak_width = width * 0.12      # Spectral bandwidth (sigma)
        self.track_top_row = height * 0.30  # Center row of top channel (Track 1)
        self.track_bot_row = height * 0.70  # Center row of bottom channel (Track 2)
        self.track_sigma = height * 0.03    # Beam vertical profile width

        # Optical parameters
        self.intrinsic_glum = +0.005        # Molecular CPL dissymmetry factor
        self.transmission_top = 1.00        # Transmission of ordinary path
        self.transmission_bot = 0.88        # Transmission mismatch of extraordinary path
        self.baseline_counts = 120.0        # Electronic baseline offset (ADU)

    def set_rotator_angle(self, angle_deg: float):
        """Receive waveplate angle from rotator stage."""
        self.rotator_angle_deg = float(angle_deg)

    def snap(self) -> np.ndarray:
        """
        Generate a synthetic 2D frame matching the current exposure time
        and waveplate orientation.
        """
        rows = np.arange(self.height)[:, np.newaxis]
        cols = np.arange(self.width)[np.newaxis, :]

        # 1D Gaussian spectral profile along dispersion axis
        spectral_profile = np.exp(-0.5 * ((cols - self.peak_col) / self.peak_width) ** 2)

        # Baseline photon flux
        peak_electrons = 15000.0 * (self.exposure_ms / 100.0)

        # Intrinsic left and right circularly polarized photon rates
        i_left = peak_electrons * (1.0 + 0.5 * self.intrinsic_glum) * spectral_profile
        i_right = peak_electrons * (1.0 - 0.5 * self.intrinsic_glum) * spectral_profile

        # Optical routing by quarter-wave plate orientation:
        # At 0 deg: Top track receives LCP, Bottom track receives RCP
        # At 90 deg: Top track receives RCP, Bottom track receives LCP
        angle_rad = np.radians(self.rotator_angle_deg)
        weight_left_to_top = 0.5 * (1.0 + np.cos(2.0 * angle_rad))

        flux_top = (weight_left_to_top * i_left + (1.0 - weight_left_to_top) * i_right) * self.transmission_top
        flux_bot = ((1.0 - weight_left_to_top) * i_left + weight_left_to_top * i_right) * self.transmission_bot

        spatial_top = np.exp(-0.5 * ((rows - self.track_top_row) / self.track_sigma) ** 2)
        spatial_bot = np.exp(-0.5 * ((rows - self.track_bot_row) / self.track_sigma) ** 2)

        noiseless_electrons = (spatial_top * flux_top) + (spatial_bot * flux_bot)

        # Poisson shot noise
        noisy_electrons = np.random.poisson(noiseless_electrons).astype(np.float32)

        # Conversion to ADU and readout noise
        adu_image = (noisy_electrons / self.electrons_per_count) + self.baseline_counts
        adu_image += np.random.normal(loc=0.0, scale=3.0, size=(self.height, self.width))

        self.current_image = np.clip(adu_image, 0, self.adc_max).astype(np.float32)
        return self.current_image
