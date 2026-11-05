# -*- coding: utf-8 -*-
"""
pyCPL Core Module: Orchestration, Calibration, Signal Processing, and Auto-Compensation.

Coordinates camera acquisition and quarter-wave plate rotation, performs
spatial track extraction, applies auto-compensation routines, computes Poisson
uncertainties, and handles wavelength calibration.

References:
- G. Delhaye, M. H. V. Werts, M. Loumaigne (2026), "A Compact Spectrometer for
  Circularly Polarized Luminescence with Sub-Minute Full-Spectrum Acquisition."
- B. Baguenard et al., Nature Communications 14, 1065 (2023).
"""

import os
import time
import json
import numpy as np


class CPLCore:
    """
    Main orchestration and spectroscopic processing engine for pyCPL.
    """
    def __init__(self, camera=None, rotator=None, config_path=None):
        self.camera = camera
        self.rotator = rotator

        # Optical track ROIs along vertical spatial axis (rows): [row_start, row_end]
        self.roi_track_top = [400, 750]
        self.roi_track_bottom = [1150, 1500]

        # Alignment ROIs for Rochon beam balance diagnostic: [x1, x2, y1, y2]
        self.roi_rochon_beam1 = [500, 600, 300, 400]
        self.roi_rochon_beam2 = [500, 600, 500, 600]

        # Quarter-wave plate rotator angles (degrees)
        self.angle_first_deg = 0.0
        self.angle_second_deg = 90.0
        self.settle_time_s = 0.25

        # Conversion factor from digital counts (ADU) to photo-electrons
        self.electrons_per_count = 23000.0 / 65535.0  # Thorlabs CS2100M-USB default

        # Processing thresholds
        self.spectrum_threshold_adu = 50.0
        self.glum_threshold = 1.0
        self.auto_compensation_method = "linear"  # "linear" (Gaetan's method) or "ratio" (Baguenard)

        # Wavelength calibration polynomial coefficients
        self.calib_degree = 2
        self.calib_coeffs = np.array([0.0, 0.0001, 0.25, 400.0], dtype=np.float64)
        self.calib_points = [
            {"pixel": 420.0, "wavelength_nm": 526.0},
            {"pixel": 488.0, "wavelength_nm": 548.0},
            {"pixel": 627.0, "wavelength_nm": 588.0}
        ]

        # Dispersion axis dimension
        self.nb_pixels = 1080
        if self.camera is not None and hasattr(self.camera, 'width'):
            self.nb_pixels = int(self.camera.width)

        self.wavelengths = np.zeros(self.nb_pixels, dtype=np.float64)
        self.update_wavelength_vector()

        # Measurement data buffers
        self.raw_frame_angle1 = None
        self.raw_frame_angle2 = None
        self.i_left = np.zeros(self.nb_pixels, dtype=np.float64)
        self.i_right = np.zeros(self.nb_pixels, dtype=np.float64)
        self.i_total = np.zeros(self.nb_pixels, dtype=np.float64)
        self.delta_i = np.zeros(self.nb_pixels, dtype=np.float64)
        self.glum = np.zeros(self.nb_pixels, dtype=np.float64)
        self.glum_error = np.zeros(self.nb_pixels, dtype=np.float64)

        # Diagnostics
        self.rochon_intensity1 = 0.0
        self.rochon_intensity2 = 0.0
        self.rochon_difference = 0.0
        self.rochon_difference_error = 0.0
        self.sharpness_score = 0.0
        self.magnitude_spectrum = None

        if config_path is not None and os.path.exists(config_path):
            self.load_config(config_path)

    # -------------------------------------------------------------------------
    # Configuration Management
    # -------------------------------------------------------------------------

    def load_config(self, filepath: str):
        """Load spectrometer parameters and calibration from JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        if "rois" in cfg:
            self.roi_track_top = cfg["rois"].get("track_top", self.roi_track_top)
            self.roi_track_bottom = cfg["rois"].get("track_bottom", self.roi_track_bottom)
            self.roi_rochon_beam1 = cfg["rois"].get("rochon_beam1", self.roi_rochon_beam1)
            self.roi_rochon_beam2 = cfg["rois"].get("rochon_beam2", self.roi_rochon_beam2)

        if "rotator" in cfg:
            self.angle_first_deg = cfg["rotator"].get("angle_first_deg", self.angle_first_deg)
            self.angle_second_deg = cfg["rotator"].get("angle_second_deg", self.angle_second_deg)
            self.settle_time_s = cfg["rotator"].get("settle_time_s", self.settle_time_s)

        if "wavelength_calibration" in cfg:
            w_cfg = cfg["wavelength_calibration"]
            self.calib_degree = w_cfg.get("degree", self.calib_degree)
            self.calib_coeffs = np.array(w_cfg.get("coefficients", self.calib_coeffs), dtype=np.float64)
            self.calib_points = w_cfg.get("reference_points", self.calib_points)
            self.update_wavelength_vector()

        if "processing" in cfg:
            p_cfg = cfg["processing"]
            self.auto_compensation_method = p_cfg.get("auto_compensation_method", self.auto_compensation_method)
            self.spectrum_threshold_adu = p_cfg.get("spectrum_threshold_adu", self.spectrum_threshold_adu)
            self.glum_threshold = p_cfg.get("glum_threshold", self.glum_threshold)

    def save_config(self, filepath: str):
        """Save current configuration to JSON file."""
        cfg = {
            "rois": {
                "track_top": self.roi_track_top,
                "track_bottom": self.roi_track_bottom,
                "rochon_beam1": self.roi_rochon_beam1,
                "rochon_beam2": self.roi_rochon_beam2
            },
            "rotator": {
                "angle_first_deg": self.angle_first_deg,
                "angle_second_deg": self.angle_second_deg,
                "settle_time_s": self.settle_time_s
            },
            "wavelength_calibration": {
                "degree": self.calib_degree,
                "coefficients": self.calib_coeffs.tolist(),
                "reference_points": self.calib_points
            },
            "processing": {
                "auto_compensation_method": self.auto_compensation_method,
                "spectrum_threshold_adu": self.spectrum_threshold_adu,
                "glum_threshold": self.glum_threshold
            }
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)

    # -------------------------------------------------------------------------
    # Wavelength Calibration
    # -------------------------------------------------------------------------

    def update_wavelength_vector(self):
        """Update 1D wavelength array from polynomial calibration coefficients."""
        pixel_indices = np.arange(self.nb_pixels, dtype=np.float64)
        self.wavelengths = np.polyval(self.calib_coeffs, pixel_indices)

    def fit_wavelength_calibration(self, pixel_points, wavelength_points, degree=2):
        """
        Fit a polynomial of specified degree using numpy least-squares regression.
        """
        pixels = np.array(pixel_points, dtype=np.float64)
        wavelengths = np.array(wavelength_points, dtype=np.float64)
        if len(pixels) < degree + 1:
            raise ValueError(f"Need at least {degree + 1} points for degree {degree} fit.")

        fitted_coeffs = np.polyfit(pixels, wavelengths, deg=degree)
        padded_coeffs = np.zeros(4, dtype=np.float64)
        padded_coeffs[-len(fitted_coeffs):] = fitted_coeffs

        self.calib_degree = degree
        self.calib_coeffs = padded_coeffs
        self.update_wavelength_vector()
        return self.calib_coeffs

    # -------------------------------------------------------------------------
    # Spatial Track Extraction
    # -------------------------------------------------------------------------

    def extract_spectra_from_frame(self, frame: np.ndarray):
        """
        Extract 1D spectra for Track 1 and Track 2 by vertical spatial integration.
        """
        if frame.shape[1] != self.nb_pixels:
            self.nb_pixels = frame.shape[1]
            self.update_wavelength_vector()

        row_t0, row_t1 = min(self.roi_track_top), max(self.roi_track_top)
        row_b0, row_b1 = min(self.roi_track_bottom), max(self.roi_track_bottom)

        track_top_2d = frame[row_t0:row_t1, :].astype(np.float64)
        track_bot_2d = frame[row_b0:row_b1, :].astype(np.float64)

        track_top_2d[track_top_2d < self.spectrum_threshold_adu] = 0.0
        track_bot_2d[track_bot_2d < self.spectrum_threshold_adu] = 0.0

        spec_top = np.sum(track_top_2d, axis=0)
        spec_bot = np.sum(track_bot_2d, axis=0)
        return spec_top, spec_bot

    # -------------------------------------------------------------------------
    # Auto-Compensation & CPL Extraction
    # -------------------------------------------------------------------------

    def compute_cpl_from_spectra(self, s1_a, s2_a, s1_b, s2_b, method=None):
        """
        Compute glum, Delta I, and Poisson uncertainties from the 4 recorded spectra:
        s1_a: Track 1 at +45 deg (LCP)
        s2_a: Track 2 at +45 deg (RCP)
        s1_b: Track 1 at -45 deg (RCP)
        s2_b: Track 2 at -45 deg (LCP)
        """
        method = method or self.auto_compensation_method

        if method == "ratio":
            numerator = s1_a * s2_b
            denominator = s1_b * s2_a
            valid_mask = (denominator > 0.0) & (numerator > 0.0)

            ratio_r = np.ones_like(s1_a)
            ratio_r[valid_mask] = np.sqrt(numerator[valid_mask] / denominator[valid_mask])

            self.glum = np.zeros_like(s1_a)
            self.glum[valid_mask] = 2.0 * (ratio_r[valid_mask] - 1.0) / (ratio_r[valid_mask] + 1.0)

            self.i_left = s1_a + s2_b
            self.i_right = s1_b + s2_a
        else:
            # Linear summation method (Gaetan Delhaye's implementation for paper data)
            self.i_left = s1_a + s2_b
            self.i_right = s1_b + s2_a

            total_intensity = self.i_left + self.i_right
            valid_mask = total_intensity > (2.0 * self.spectrum_threshold_adu)

            self.glum = np.zeros_like(self.i_left)
            self.glum[valid_mask] = 2.0 * (self.i_left[valid_mask] - self.i_right[valid_mask]) / total_intensity[valid_mask]

        self.i_total = self.i_left + self.i_right
        self.delta_i = self.i_left - self.i_right

        self.glum[np.abs(self.glum) > self.glum_threshold] = 0.0

        # Rigorous Poisson shot-noise uncertainty propagation
        n_left = np.maximum(self.i_left * self.electrons_per_count, 1e-9)
        n_right = np.maximum(self.i_right * self.electrons_per_count, 1e-9)
        n_total = n_left + n_right

        sigma_glum = (4.0 * np.sqrt(n_left * n_right)) / (n_total ** 1.5)
        self.glum_error = np.zeros_like(self.glum)
        self.glum_error[valid_mask] = sigma_glum[valid_mask]

        return self.glum, self.glum_error

    def process_pair(self, frame_a: np.ndarray, frame_b: np.ndarray, method=None):
        """Process a pair of full 2D frames (Angle A and Angle B)."""
        self.raw_frame_angle1 = frame_a
        self.raw_frame_angle2 = frame_b

        s1_a, s2_a = self.extract_spectra_from_frame(frame_a)
        s1_b, s2_b = self.extract_spectra_from_frame(frame_b)

        return self.compute_cpl_from_spectra(s1_a, s2_a, s1_b, s2_b, method=method)

    # -------------------------------------------------------------------------
    # Hardware Orchestration
    # -------------------------------------------------------------------------

    def snap_frame(self) -> np.ndarray:
        """Acquire a single 2D image from camera."""
        if self.camera is None:
            raise RuntimeError("Camera is not connected.")
        return self.camera.snap()

    def acquire_cpl_pair(self, angle1=None, angle2=None) -> np.ndarray:
        """
        Orchestrate a complete 2-angle CPL acquisition cycle.
        """
        if self.camera is None:
            raise RuntimeError("Camera is not connected.")

        ang1 = self.angle_first_deg if angle1 is None else float(angle1)
        ang2 = self.angle_second_deg if angle2 is None else float(angle2)

        if self.rotator is not None:
            self.rotator.set_angle(ang1, settle_time_s=self.settle_time_s)
        frame_a = self.camera.snap()

        if self.rotator is not None:
            self.rotator.set_angle(ang2, settle_time_s=self.settle_time_s)
        frame_b = self.camera.snap()

        if self.rotator is not None:
            self.rotator.set_angle(ang1, settle_time_s=self.settle_time_s)

        self.process_pair(frame_a, frame_b)
        self.compute_rochon_balance(frame_a)
        self.compute_fourier_sharpness(frame_a)
        return self.glum

    def accumulate_cpl(self, n_accumulations: int = 20, callback=None):
        """
        Acquire and accumulate N consecutive CPL measurement pairs.
        Accumulates raw photon counts before calculating glum to preserve Poisson statistics.
        """
        if n_accumulations < 1:
            raise ValueError("n_accumulations must be >= 1")

        accum_s1_a = np.zeros(self.nb_pixels, dtype=np.float64)
        accum_s2_a = np.zeros(self.nb_pixels, dtype=np.float64)
        accum_s1_b = np.zeros(self.nb_pixels, dtype=np.float64)
        accum_s2_b = np.zeros(self.nb_pixels, dtype=np.float64)

        for i in range(n_accumulations):
            if self.rotator is not None:
                self.rotator.set_angle(self.angle_first_deg, settle_time_s=self.settle_time_s)
            fa = self.camera.snap()
            s1_a, s2_a = self.extract_spectra_from_frame(fa)
            accum_s1_a += s1_a
            accum_s2_a += s2_a

            if self.rotator is not None:
                self.rotator.set_angle(self.angle_second_deg, settle_time_s=self.settle_time_s)
            fb = self.camera.snap()
            s1_b, s2_b = self.extract_spectra_from_frame(fb)
            accum_s1_b += s1_b
            accum_s2_b += s2_b

            if callback is not None:
                callback(i + 1, n_accumulations)

        if self.rotator is not None:
            self.rotator.set_angle(self.angle_first_deg, settle_time_s=self.settle_time_s)

        self.compute_cpl_from_spectra(accum_s1_a, accum_s2_a, accum_s1_b, accum_s2_b)
        return self.glum, self.glum_error

    # -------------------------------------------------------------------------
    # Diagnostics & Alignment
    # -------------------------------------------------------------------------

    def compute_rochon_balance(self, frame: np.ndarray):
        """Calculate integrated intensity balance across Rochon alignment ROIs."""
        r1 = self.roi_rochon_beam1
        r2 = self.roi_rochon_beam2

        beam1 = frame[r1[2]:r1[3], r1[0]:r1[1]].astype(np.float64)
        beam2 = frame[r2[2]:r2[3], r2[0]:r2[1]].astype(np.float64)

        self.rochon_intensity1 = float(np.sum(beam1))
        self.rochon_intensity2 = float(np.sum(beam2))
        self.rochon_difference = self.rochon_intensity1 - self.rochon_intensity2
        self.rochon_difference_error = float(np.sqrt(self.rochon_intensity1 + self.rochon_intensity2))
        return self.rochon_difference, self.rochon_difference_error

    def compute_fourier_sharpness(self, frame: np.ndarray):
        """Compute image sharpness score via 2D FFT high-frequency power."""
        f_transform = np.fft.fft2(frame.astype(np.float64))
        f_shifted = np.fft.fftshift(f_transform)
        self.magnitude_spectrum = np.abs(f_shifted)

        power_spectrum = np.square(self.magnitude_spectrum)
        rows, cols = frame.shape
        crow, ccol = rows // 2, cols // 2
        radius = 20

        r0, r1 = max(0, crow - radius), min(rows, crow + radius)
        c0, c1 = max(0, ccol - radius), min(cols, ccol + radius)

        power_high_freq = np.sum(power_spectrum[r0:r1, c0:c1])
        self.sharpness_score = float(np.sqrt(power_high_freq) / (rows * cols))
        return self.sharpness_score

    def auto_roi_detection(self, frame: np.ndarray):
        """Detect track positions from vertical spatial profile peaks."""
        vertical_profile = np.sum(frame.astype(np.float64), axis=1)
        bg_level = np.median(vertical_profile[:100])
        threshold = bg_level + 0.25 * (np.max(vertical_profile) - bg_level)

        peaks = []
        for i in range(1, len(vertical_profile) - 1):
            if vertical_profile[i] > threshold:
                if vertical_profile[i] > vertical_profile[i - 1] and vertical_profile[i] >= vertical_profile[i + 1]:
                    peaks.append(i)

        if len(peaks) >= 2:
            peaks.sort(key=lambda idx: vertical_profile[idx], reverse=True)
            p1, p2 = sorted(peaks[:2])
            half_width = int(abs(p2 - p1) * 0.25)
            self.roi_track_top = [max(0, p1 - half_width), min(len(vertical_profile), p1 + half_width)]
            self.roi_track_bottom = [max(0, p2 - half_width), min(len(vertical_profile), p2 + half_width)]
            return self.roi_track_top, self.roi_track_bottom
        return None

    def auto_exposure(self, min_fraction=0.70, max_fraction=0.92, max_iterations=6):
        """Adjust exposure time to target ~85% dynamic range without saturation."""
        if self.camera is None:
            return

        current_exp = self.camera.get_exposure()
        target_max = self.camera.adc_max * ((min_fraction + max_fraction) / 2.0)

        for _ in range(max_iterations):
            img = self.camera.snap()
            peak_val = np.max(img)
            if peak_val >= self.camera.adc_max * max_fraction:
                current_exp = max(1.0, current_exp * 0.7)
                self.camera.set_exposure(current_exp)
            elif peak_val <= self.camera.adc_max * min_fraction and peak_val > 0:
                scale = target_max / peak_val
                current_exp = min(10000.0, current_exp * min(scale, 2.0))
                self.camera.set_exposure(current_exp)
            else:
                break
        return self.camera.get_exposure()

    # -------------------------------------------------------------------------
    # Data Export
    # -------------------------------------------------------------------------

    def export_spectrum_csv(self, filepath: str, sample_name: str = "Sample"):
        """Export calibrated spectra and glum to standardized CSV with metadata header."""
        exposure_ms = self.camera.get_exposure() if self.camera is not None else 0.0

        header_lines = [
            "# Instrument: Compact Free-Space CPL Spectrometer (pyCPL)",
            f"# Sample: {sample_name}",
            f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"# Exposure_ms: {exposure_ms:.2f}",
            f"# Auto_Compensation_Method: {self.auto_compensation_method}",
            f"# Calibration_Coefficients: {list(self.calib_coeffs)}",
            f"# Electron_Conversion_Factor: {self.electrons_per_count:.6f} e-/ADU",
            "wavelength_nm,i_left_adu,i_right_adu,i_total_adu,delta_i_adu,glum,glum_error"
        ]
        header = "\n".join(header_lines)

        data = np.column_stack((
            self.wavelengths,
            self.i_left,
            self.i_right,
            self.i_total,
            self.delta_i,
            self.glum,
            self.glum_error
        ))

        np.savetxt(filepath, data, delimiter=",", header=header, comments="")

    def export_raw_chip(self, filepath: str, frame: np.ndarray = None):
        """Export raw 2D image matrix to file."""
        img = frame if frame is not None else (self.camera.current_image if self.camera is not None else None)
        if img is not None:
            np.savetxt(filepath, img, fmt="%.1f")

    def import_raw_chip(self, filepath: str) -> np.ndarray:
        """Load raw 2D image matrix from file."""
        data = np.loadtxt(filepath)
        if self.camera is not None:
            self.camera.current_image = data.astype(np.float32)
        return data
