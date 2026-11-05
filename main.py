# -*- coding: utf-8 -*-
"""
Main launcher script for pyCPL. Supports both graphical (GUI) and headless CLI execution.

Examples:
    python main.py --dummy
    python main.py --thorlabs --port COM9
    python main.py --cli --accumulate 20 --output spectrum.csv
"""
import os
import argparse
import tkinter as tk

from core import CPLCore


def parse_arguments():
    parser = argparse.ArgumentParser(description="pyCPL: Compact Free-Space CPL Spectrometer")
    parser.add_argument("--dummy", action="store_true", help="Run with simulated dummy camera and rotator.")
    parser.add_argument("--thorlabs", action="store_true", help="Connect to physical Thorlabs sCMOS camera.")
    parser.add_argument("--port", default="COM9", help="Serial port for Elliptec rotation stage (default: COM9).")
    parser.add_argument("--config", default="config.json", help="Path to JSON configuration file.")
    parser.add_argument("--cli", action="store_true", help="Run in headless command-line mode without GUI.")
    parser.add_argument("--accumulate", type=int, default=10, help="Number of accumulations for CLI mode.")
    parser.add_argument("--output", default="cpl_output.csv", help="Output CSV path for CLI mode.")
    return parser.parse_args()


def init_hardware(args):
    camera = None
    rotator = None

    if args.dummy or (not args.thorlabs):
        from hardware.camera_dummy import DummyCamera
        from hardware.rotator_elliptec import DummyRotator
        camera = DummyCamera()
        rotator = DummyRotator()
        rotator.link_camera(camera)
    else:
        from hardware.camera_thorlabs import CameraThorlabs
        from hardware.rotator_elliptec import ElliptecRotator
        camera = CameraThorlabs()
        rotator = ElliptecRotator(port=args.port)

    return camera, rotator


def main():
    args = parse_arguments()
    camera, rotator = init_hardware(args)

    cfg_path = args.config if os.path.exists(args.config) else None
    core = CPLCore(camera=camera, rotator=rotator, config_path=cfg_path)

    if args.cli:
        print(f"Acquiring CPL with {args.accumulate} accumulations...")
        core.accumulate_cpl(n_accumulations=args.accumulate)
        core.export_spectrum_csv(args.output)
        print(f"Data saved to {args.output}")
        if camera is not None:
            camera.shutdown()
        if rotator is not None:
            rotator.close()
    else:
        from gui import pyCPL_GUI
        root = tk.Tk()
        app = pyCPL_GUI(root, core)
        root.mainloop()


if __name__ == "__main__":
    main()
