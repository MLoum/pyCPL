# pyCPL: Acquisition and Processing Suite for Fast Full-Spectrum CPL Spectrometry

`pyCPL` is an open-source Python instrument control and spectroscopic analysis suite designed for compact, all-free-space Circularly Polarized Luminescence (CPL) spectrometers using a single sCMOS image sensor and a motorized quarter-wave plate.

This software accompanies the paper:
> **A Compact Spectrometer for Circularly Polarized Luminescence with Sub-Minute Full-Spectrum Acquisition**  
> G. Delhaye, M. H. V. Werts, and M. Loumaigne (2026).

---

## 1. Physical Principle & Optical Auto-Compensation

The instrument couples a super-achromatic quarter-wave retarder ($\lambda/4$), an $\alpha$-BBO Rochon polarizing prism, a transmission grating, and a scientific CMOS sensor. 

The Rochon prism splits the emission into two orthogonal linear polarization channels imaged simultaneously as two vertically separated tracks on the sensor (Track 1 and Track 2).

To cancel instrumental transmission imbalances ($T_1 \neq T_2$) and grating polarization dependencies without external calibration standards, two successive frames are acquired with the quarter-wave plate fast axis rotated by $90^\circ$ ($+45^\circ$ and $-45^\circ$):

| Angle | Track 1 (Top, $T_1$) | Track 2 (Bottom, $T_2$) |
|---|---|---|
| **Angle A ($+45^\circ$)** | $S_1^A = I_L \cdot T_1$ | $S_2^A = I_R \cdot T_2$ |
| **Angle B ($-45^\circ$)** | $S_1^B = I_R \cdot T_1$ | $S_2^B = I_L \cdot T_2$ |

### Auto-Compensation Methods

1. **Linear Summation (Default, Delhaye et al.)**:
   $$I_L = S_1^A + S_2^B = I_L (T_1 + T_2)$$
   $$I_R = S_1^B + S_2^A = I_R (T_1 + T_2)$$
   $$g_{\text{lum}} = \frac{2(I_L - I_R)}{I_L + I_R}$$
   The transmission terms cancel out identically while strictly preserving Poisson photon statistics.

2. **Geometric Cross-Ratio (Baguenard et al., Nat. Commun. 2023)**:
   $$R = \sqrt{\frac{S_1^A \cdot S_2^B}{S_1^B \cdot S_2^A}} = \frac{I_L}{I_R}, \quad g_{\text{lum}} = 2 \frac{R - 1}{R + 1}$$
   Compensates additionally for slow excitation source intensity variations.

### Poisson Shot-Noise Uncertainty

In the photo-electron domain ($N = \text{ADU} \times \text{gain}$), the exact standard error on $g_{\text{lum}}$ is:
$$\sigma_{g_{\text{lum}}} = \frac{4 \sqrt{N_L \cdot N_R}}{(N_L + N_R)^{3/2}} \approx \frac{2}{\sqrt{N_{\text{total}}}}$$

---

## 2. Repository Structure

```text
pyCPL/
├── config.json             # Default parameters (ROIs, calibrations, motor port)
├── core.py                # CPLCore class (autonomous calculation & orchestration)
├── gui.py                 # Tkinter GUI with non-blocking threads
├── main.py                # Application entry point (GUI and CLI)
└── hardware/
    ├── camera_base.py     # Base abstract camera interface
    ├── camera_thorlabs.py # Driver for Thorlabs CS2100M-USB sCMOS
    ├── camera_dummy.py    # Synthetic camera with Poisson noise and glum
    ├── rotator_elliptec.py# Driver for Thorlabs Elliptec ELL14 rotator
    └── test_hardware.py   # Standalone hardware test script

3. Installation
Requirements

    Python 3.9+

    numpy, scipy, matplotlib

    elliptec (optional, for physical rotation stage)

    Thorlabs TSI SDK (optional, for physical Thorlabs sCMOS camera)

Bash

git clone [https://github.com/MLoum/pyCPL.git](https://github.com/MLoum/pyCPL.git)
cd pyCPL
pip install numpy scipy matplotlib

4. Usage
Hardware Diagnostic Test

Test connected instruments or synthetic hardware in the terminal:
Bash

# Test synthetic dummy hardware (no physical devices needed)
python hardware/test_hardware.py --camera dummy --rotator dummy

# Test physical laboratory hardware
python hardware/test_hardware.py --camera thorlabs --rotator elliptec --port COM9

Running the Graphical Interface
Bash

# Offline simulation mode (ideal for demonstration or data re-processing)
python main.py --dummy

# Laboratory operation mode
python main.py --thorlabs --port COM9

Headless CLI Mode (Automated Batch Measurements)
Bash

python main.py --dummy --cli --accumulate 20 --output synthetic_camphorquinone.csv

5. Output Data Format

Exported CSV files include full provenance metadata in accordance with FAIR scientific data principles:
Extrait de code

# Instrument: Compact Free-Space CPL Spectrometer (pyCPL)
# Sample: Camphorquinone
# Date: 2026-11-05 14:00:00
# Exposure_ms: 100.00
# Auto_Compensation_Method: linear
# Calibration_Coefficients: [0.0, 0.0001, 0.25, 400.0]
# Electron_Conversion_Factor: 0.350957 e-/ADU
wavelength_nm,i_left_adu,i_right_adu,i_total_adu,delta_i_adu,glum,glum_error
500.0,1250.2,1238.1,2488.3,12.1,0.00972,0.00112
...

6. Citation

If you use pyCPL in your research, please cite:
Extrait de code

@article{delhaye2026compact,
  title={A Compact Spectrometer for Circularly Polarized Luminescence with Sub-Minute Full-Spectrum Acquisition},
  author={Delhaye, G. and Werts, M. H. V. and Loumaigne, M.},
  journal={Rev. Sci. Instrum.},
  year={2026}
}
