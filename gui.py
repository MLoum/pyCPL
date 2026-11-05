# -*- coding: utf-8 -*-
"""
pyCPL Graphical User Interface (Tkinter / Matplotlib).
Non-blocking threaded architecture for reliable scientific acquisitions.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.patches as patches


class pyCPL_GUI:
    """
    Tkinter graphical interface for pyCPL.
    """
    def __init__(self, root, core):
        self.root = root
        self.core = core
        self.root.title("pyCPL - Compact CPL Spectrometer")
        self.root.geometry("1400x900")

        self.video_active = False
        self.acquisition_thread = None

        self.create_menu()
        self.create_widgets()
        self.update_gui_from_core()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load Config...", command=self.menu_load_config)
        file_menu.add_command(label="Save Config...", command=self.menu_save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Export Spectrum CSV...", command=self.menu_export_csv)
        file_menu.add_command(label="Export Raw Chip...", command=self.menu_export_chip)
        file_menu.add_command(label="Import Raw Chip...", command=self.menu_import_chip)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.tab_acq = ttk.Frame(self.notebook)
        self.tab_roi = ttk.Frame(self.notebook)
        self.tab_calib = ttk.Frame(self.notebook)
        self.tab_diag = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_acq, text="Acquisition")
        self.notebook.add(self.tab_roi, text="ROIs & Optical Profiles")
        self.notebook.add(self.tab_calib, text="Wavelength Calibration")
        self.notebook.add(self.tab_diag, text="Focus & Alignment")

        self.build_tab_acq()
        self.build_tab_roi()
        self.build_tab_calib()
        self.build_tab_diag()

    # -------------------------------------------------------------------------
    # TAB 1: ACQUISITION
    # -------------------------------------------------------------------------

    def build_tab_acq(self):
        left_panel = ttk.Frame(self.tab_acq, width=320)
        left_panel.pack(side="left", fill="y", padx=8, pady=8)

        # Control Group
        cmd_group = ttk.LabelFrame(left_panel, text="Acquisition Commands")
        cmd_group.pack(fill="x", pady=4)

        ttk.Button(cmd_group, text="Snap Single Frame", command=self.action_snap_single).pack(fill="x", pady=2)
        ttk.Button(cmd_group, text="Acquire CPL Pair (2 Angles)", command=self.action_acquire_cpl).pack(fill="x", pady=2)
        ttk.Button(cmd_group, text="Start Video Preview", command=self.action_toggle_video).pack(fill="x", pady=2)
        ttk.Button(cmd_group, text="Auto Exposure", command=self.action_auto_exposure).pack(fill="x", pady=2)
        ttk.Button(cmd_group, text="Auto ROI Detection", command=self.action_auto_roi).pack(fill="x", pady=2)

        # Multi-Accumulation Group
        accum_group = ttk.LabelFrame(left_panel, text="Accumulation Series")
        accum_group.pack(fill="x", pady=4)

        acc_row = ttk.Frame(accum_group)
        acc_row.pack(fill="x", pady=2)
        ttk.Label(acc_row, text="Count:").pack(side="left")
        self.var_accum_count = tk.IntVar(value=10)
        ttk.Entry(acc_row, textvariable=self.var_accum_count, width=6).pack(side="left", padx=4)

        ttk.Button(accum_group, text="Start Accumulation", command=self.action_start_accumulation).pack(fill="x", pady=2)
        self.progress_bar = ttk.Progressbar(accum_group, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x", pady=4)
        self.lbl_progress = ttk.Label(accum_group, text="Ready")
        self.lbl_progress.pack()

        # Camera Parameters
        param_group = ttk.LabelFrame(left_panel, text="Parameters")
        param_group.pack(fill="x", pady=4)

        exp_row = ttk.Frame(param_group)
        exp_row.pack(fill="x", pady=2)
        ttk.Label(exp_row, text="Exposure (ms):").pack(side="left")
        self.var_exposure = tk.DoubleVar(value=100.0)
        e_exp = ttk.Entry(exp_row, textvariable=self.var_exposure, width=8)
        e_exp.pack(side="right")
        e_exp.bind("<Return>", lambda e: self.action_update_exposure())

        method_row = ttk.Frame(param_group)
        method_row.pack(fill="x", pady=2)
        ttk.Label(method_row, text="Compensation:").pack(side="left")
        self.var_method = tk.StringVar(value=self.core.auto_compensation_method)
        cb_m = ttk.Combobox(method_row, textvariable=self.var_method, values=["linear", "ratio"], state="readonly", width=8)
        cb_m.pack(side="right")
        cb_m.bind("<<ComboboxSelected>>", lambda e: self.action_update_method())

        # Display Toggles
        disp_group = ttk.LabelFrame(left_panel, text="Display Plots")
        disp_group.pack(fill="x", pady=4)
        self.var_disp_glum = tk.BooleanVar(value=True)
        self.var_disp_error = tk.BooleanVar(value=True)
        self.var_disp_raw_polar = tk.BooleanVar(value=True)
        ttk.Checkbutton(disp_group, text="Show glum", variable=self.var_disp_glum, command=self.refresh_cpl_plot).pack(anchor="w")
        ttk.Checkbutton(disp_group, text="Show glum Error Bars", variable=self.var_disp_error, command=self.refresh_cpl_plot).pack(anchor="w")
        ttk.Checkbutton(disp_group, text="Show I_L / I_R Channels", variable=self.var_disp_raw_polar, command=self.refresh_cpl_plot).pack(anchor="w")

        # Chip Thumbnail
        thumb_group = ttk.LabelFrame(left_panel, text="Sensor Preview")
        thumb_group.pack(fill="both", expand=True, pady=4)
        self.fig_thumb = Figure(figsize=(3, 2), dpi=80)
        self.ax_thumb = self.fig_thumb.add_subplot(111)
        self.canvas_thumb = FigureCanvasTkAgg(self.fig_thumb, master=thumb_group)
        self.canvas_thumb.get_tk_widget().pack(fill="both", expand=True)

        # Main CPL Plot Area
        plot_frame = ttk.Frame(self.tab_acq)
        plot_frame.pack(side="right", fill="both", expand=True, padx=8, pady=8)

        self.fig_cpl = Figure(figsize=(9, 6), dpi=100)
        self.ax_cpl = self.fig_cpl.add_subplot(111)
        self.ax_intensity = self.ax_cpl.twinx()
        self.canvas_cpl = FigureCanvasTkAgg(self.fig_cpl, master=plot_frame)
        self.toolbar_cpl = NavigationToolbar2Tk(self.canvas_cpl, plot_frame)
        self.canvas_cpl.get_tk_widget().pack(fill="both", expand=True)

    # -------------------------------------------------------------------------
    # TAB 2: ROIS & PROFILES
    # -------------------------------------------------------------------------

    def build_tab_roi(self):
        ctrl_frame = ttk.Frame(self.tab_roi)
        ctrl_frame.pack(side="top", fill="x", padx=8, pady=4)

        ttk.Label(ctrl_frame, text="Top Track [Row Min - Max]:").pack(side="left")
        self.var_t_min = tk.IntVar(value=self.core.roi_track_top[0])
        self.var_t_max = tk.IntVar(value=self.core.roi_track_top[1])
        ttk.Entry(ctrl_frame, textvariable=self.var_t_min, width=5).pack(side="left", padx=2)
        ttk.Entry(ctrl_frame, textvariable=self.var_t_max, width=5).pack(side="left", padx=2)

        ttk.Label(ctrl_frame, text="   Bottom Track [Row Min - Max]:").pack(side="left")
        self.var_b_min = tk.IntVar(value=self.core.roi_track_bottom[0])
        self.var_b_max = tk.IntVar(value=self.core.roi_track_bottom[1])
        ttk.Entry(ctrl_frame, textvariable=self.var_b_min, width=5).pack(side="left", padx=2)
        ttk.Entry(ctrl_frame, textvariable=self.var_b_max, width=5).pack(side="left", padx=2)

        ttk.Button(ctrl_frame, text="Apply ROIs", command=self.action_apply_rois).pack(side="left", padx=8)

        # Figures
        disp_frame = ttk.Frame(self.tab_roi)
        disp_frame.pack(fill="both", expand=True, padx=8, pady=4)

        self.fig_roi = Figure(figsize=(10, 6), dpi=100)
        self.ax_chip_roi = self.fig_roi.add_subplot(121)
        self.ax_v_prof = self.fig_roi.add_subplot(122)
        self.canvas_roi = FigureCanvasTkAgg(self.fig_roi, master=disp_frame)
        self.toolbar_roi = NavigationToolbar2Tk(self.canvas_roi, disp_frame)
        self.canvas_roi.get_tk_widget().pack(fill="both", expand=True)

    # -------------------------------------------------------------------------
    # TAB 3: CALIBRATION
    # -------------------------------------------------------------------------

    def build_tab_calib(self):
        panel = ttk.Frame(self.tab_calib, padding=10)
        panel.pack(fill="both", expand=True)

        desc = (
            "Select reference emission peaks from a spectral calibration lamp (e.g. Hg-Ar or Ne).\n"
            "Enter the pixel peak center and nominal wavelength (nm), then fit polynomial regression."
        )
        ttk.Label(panel, text=desc, justify="left").pack(anchor="w", pady=4)

        table_frame = ttk.LabelFrame(panel, text="Reference Peaks")
        table_frame.pack(fill="x", pady=6)

        self.calib_entries = []
        for i in range(4):
            row = ttk.Frame(table_frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=f"Peak {i+1} - Pixel:").pack(side="left", padx=4)
            v_pix = tk.StringVar()
            e_pix = ttk.Entry(row, textvariable=v_pix, width=10)
            e_pix.pack(side="left", padx=4)
            ttk.Label(row, text="Wavelength (nm):").pack(side="left", padx=4)
            v_wl = tk.StringVar()
            e_wl = ttk.Entry(row, textvariable=v_wl, width=10)
            e_wl.pack(side="left", padx=4)
            self.calib_entries.append((v_pix, v_wl))

        # Populate defaults
        for idx, pt in enumerate(self.core.calib_points[:4]):
            self.calib_entries[idx][0].set(str(pt["pixel"]))
            self.calib_entries[idx][1].set(str(pt["wavelength_nm"]))

        btn_row = ttk.Frame(panel)
        btn_row.pack(fill="x", pady=6)
        ttk.Button(btn_row, text="Fit Degree 2 Polynomial", command=lambda: self.action_fit_calibration(2)).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Fit Degree 3 Polynomial", command=lambda: self.action_fit_calibration(3)).pack(side="left", padx=4)

        self.lbl_calib_result = ttk.Label(panel, text="", font=("Courier", 10))
        self.lbl_calib_result.pack(anchor="w", pady=6)
        self.update_calib_label()

    # -------------------------------------------------------------------------
    # TAB 4: DIAGNOSTICS & ALIGNMENT
    # -------------------------------------------------------------------------

    def build_tab_diag(self):
        panel = ttk.Frame(self.tab_diag, padding=10)
        panel.pack(fill="both", expand=True)

        info_group = ttk.LabelFrame(panel, text="Optical Alignment Diagnostics")
        info_group.pack(fill="x", pady=6)

        self.lbl_rochon = ttk.Label(info_group, text="Rochon Beam Balance: N/A", font=("Courier", 10))
        self.lbl_rochon.pack(anchor="w", padx=6, pady=4)
        self.lbl_fourier = ttk.Label(info_group, text="Sharpness Score: 0.00", font=("Courier", 10))
        self.lbl_fourier.pack(anchor="w", padx=6, pady=4)

        fig_frame = ttk.Frame(panel)
        fig_frame.pack(fill="both", expand=True, pady=6)
        self.fig_diag = Figure(figsize=(8, 4), dpi=100)
        self.ax_fft = self.fig_diag.add_subplot(111)
        self.canvas_diag = FigureCanvasTkAgg(self.fig_diag, master=fig_frame)
        self.canvas_diag.get_tk_widget().pack(fill="both", expand=True)

    # -------------------------------------------------------------------------
    # Actions & Threaded Controllers
    # -------------------------------------------------------------------------

    def update_gui_from_core(self):
        if self.core.camera is not None:
            self.var_exposure.set(self.core.camera.get_exposure())
        self.var_method.set(self.core.auto_compensation_method)
        self.refresh_thumb()

    def action_update_exposure(self):
        val = self.var_exposure.get()
        if self.core.camera is not None:
            self.core.camera.set_exposure(val)

    def action_update_method(self):
        self.core.auto_compensation_method = self.var_method.get()
        if self.core.raw_frame_angle1 is not None and self.core.raw_frame_angle2 is not None:
            self.core.process_pair(self.core.raw_frame_angle1, self.core.raw_frame_angle2)
            self.refresh_cpl_plot()

    def action_snap_single(self):
        if self.core.camera is None:
            messagebox.showwarning("No Camera", "Camera is not connected.")
            return
        frame = self.core.snap_frame()
        self.refresh_thumb()
        self.refresh_roi_tab(frame)

    def action_acquire_cpl(self):
        def task():
            try:
                self.core.acquire_cpl_pair()
                self.root.after(0, self.refresh_all_views)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Acquisition Error", str(e)))

        threading.Thread(target=task, daemon=True).start()

    def action_start_accumulation(self):
        n_count = self.var_accum_count.get()
        self.progress_bar["maximum"] = n_count
        self.progress_bar["value"] = 0

        def callback(current, total):
            self.root.after(0, lambda: self.update_progress(current, total))

        def task():
            try:
                self.core.accumulate_cpl(n_accumulations=n_count, callback=callback)
                self.root.after(0, self.refresh_all_views)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Accumulation Error", str(e)))

        threading.Thread(target=task, daemon=True).start()

    def update_progress(self, current, total):
        self.progress_bar["value"] = current
        self.lbl_progress.config(text=f"Accumulation {current} / {total}")

    def action_toggle_video(self):
        if not self.video_active:
            self.video_active = True
            self.video_loop()
        else:
            self.video_active = False

    def video_loop(self):
        if self.video_active and self.core.camera is not None:
            self.core.snap_frame()
            self.refresh_thumb()
            delay_ms = max(50, int(self.core.camera.get_exposure()))
            self.root.after(delay_ms, self.video_loop)

    def action_auto_exposure(self):
        if self.core.camera is None:
            return
        new_exp = self.core.auto_exposure()
        self.var_exposure.set(round(new_exp, 2))
        self.refresh_thumb()

    def action_auto_roi(self):
        if self.core.camera is None or self.core.camera.current_image is None:
            return
        res = self.core.auto_roi_detection(self.core.camera.current_image)
        if res:
            self.var_t_min.set(res[0][0])
            self.var_t_max.set(res[0][1])
            self.var_b_min.set(res[1][0])
            self.var_b_max.set(res[1][1])
            self.action_apply_rois()

    def action_apply_rois(self):
        self.core.roi_track_top = [self.var_t_min.get(), self.var_t_max.get()]
        self.core.roi_track_bottom = [self.var_b_min.get(), self.var_b_max.get()]
        if self.core.camera is not None and self.core.camera.current_image is not None:
            self.refresh_roi_tab(self.core.camera.current_image)
            self.refresh_thumb()

    def action_fit_calibration(self, degree):
        pix_pts = []
        wl_pts = []
        for v_pix, v_wl in self.calib_entries:
            p_str, w_str = v_pix.get().strip(), v_wl.get().strip()
            if p_str and w_str:
                pix_pts.append(float(p_str))
                wl_pts.append(float(w_str))

        if len(pix_pts) < degree + 1:
            messagebox.showerror("Error", f"Need at least {degree + 1} points for degree {degree}.")
            return

        self.core.fit_wavelength_calibration(pix_pts, wl_pts, degree=degree)
        self.update_calib_label()
        self.refresh_cpl_plot()
        messagebox.showinfo("Calibration", "Wavelength calibration updated successfully.")

    def update_calib_label(self):
        c = self.core.calib_coeffs
        self.lbl_calib_result.config(text=f"Formula: lambda = {c[0]:.2e}*x^3 + {c[1]:.2e}*x^2 + {c[2]:.4f}*x + {c[3]:.2f}")

    # -------------------------------------------------------------------------
    # View Refreshes
    # -------------------------------------------------------------------------

    def refresh_all_views(self):
        self.refresh_thumb()
        self.refresh_cpl_plot()
        if self.core.camera is not None and self.core.camera.current_image is not None:
            self.refresh_roi_tab(self.core.camera.current_image)
            self.refresh_diag_tab(self.core.camera.current_image)

    def refresh_thumb(self):
        if self.core.camera is None or self.core.camera.current_image is None:
            return
        self.ax_thumb.clear()
        self.ax_thumb.imshow(self.core.camera.current_image, cmap="viridis", aspect="auto")

        # Draw ROIs
        t_min, t_max = self.core.roi_track_top
        b_min, b_max = self.core.roi_track_bottom
        w = self.core.camera.width

        rect_t = patches.Rectangle((0, t_min), w, t_max - t_min, fill=False, edgecolor="red", linewidth=1.2)
        rect_b = patches.Rectangle((0, b_min), w, b_max - b_min, fill=False, edgecolor="cyan", linewidth=1.2)
        self.ax_thumb.add_patch(rect_t)
        self.ax_thumb.add_patch(rect_b)

        self.ax_thumb.axis("off")
        self.fig_thumb.tight_layout(pad=0.2)
        self.canvas_thumb.draw_idle()

    def refresh_cpl_plot(self):
        self.ax_cpl.clear()
        self.ax_intensity.clear()

        wl = self.core.wavelengths

        # Right axis: raw intensities
        if self.var_disp_raw_polar.get():
            self.ax_intensity.plot(wl, self.core.i_left, color="magenta", alpha=0.35, label="I_left")
            self.ax_intensity.plot(wl, self.core.i_right, color="blue", alpha=0.35, label="I_right")
            self.ax_intensity.set_ylabel("Intensity (ADU)", color="gray", fontsize=11)
            self.ax_intensity.tick_params(axis="y", labelcolor="gray")

        # Left axis: glum
        if self.var_disp_glum.get():
            self.ax_cpl.plot(wl, self.core.glum, color="black", lw=1.2, label=f"glum ({self.core.auto_compensation_method})")
            if self.var_disp_error.get():
                self.ax_cpl.fill_between(
                    wl,
                    self.core.glum - self.core.glum_error,
                    self.core.glum + self.core.glum_error,
                    color="red",
                    alpha=0.2,
                    label="Poisson Shot Noise"
                )

        self.ax_cpl.axhline(0, color="gray", linestyle="--", lw=0.8)
        self.ax_cpl.set_xlabel("Wavelength (nm)", fontsize=11)
        self.ax_cpl.set_ylabel("Luminescence Dissymmetry Factor glum", fontsize=11)
        self.ax_cpl.set_ylim(-0.02, 0.02)
        self.ax_cpl.grid(True, linestyle=":", alpha=0.6)

        # Combined legend
        lines_1, labels_1 = self.ax_cpl.get_legend_handles_labels()
        lines_2, labels_2 = self.ax_intensity.get_legend_handles_labels()
        self.ax_cpl.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper right")

        self.fig_cpl.tight_layout()
        self.canvas_cpl.draw_idle()

    def refresh_roi_tab(self, frame):
        self.ax_chip_roi.clear()
        self.ax_v_prof.clear()

        self.ax_chip_roi.imshow(frame, cmap="viridis", aspect="auto")
        w = frame.shape[1]
        t_min, t_max = self.core.roi_track_top
        b_min, b_max = self.core.roi_track_bottom

        self.ax_chip_roi.add_patch(patches.Rectangle((0, t_min), w, t_max - t_min, fill=False, edgecolor="red", lw=1.5))
        self.ax_chip_roi.add_patch(patches.Rectangle((0, b_min), w, b_max - b_min, fill=False, edgecolor="cyan", lw=1.5))
        self.ax_chip_roi.set_title("Full Chip Image with Track ROIs")

        v_profile = np.sum(frame, axis=1)
        self.ax_v_prof.plot(v_profile, np.arange(len(v_profile)), color="teal")
        self.ax_v_prof.axhline(t_min, color="red", linestyle=":")
        self.ax_v_prof.axhline(t_max, color="red", linestyle=":")
        self.ax_v_prof.axhline(b_min, color="cyan", linestyle=":")
        self.ax_v_prof.axhline(b_max, color="cyan", linestyle=":")
        self.ax_v_prof.invert_yaxis()
        self.ax_v_prof.set_title("Vertical Spatial Profile")
        self.ax_v_prof.set_xlabel("Summed ADU")

        self.fig_roi.tight_layout()
        self.canvas_roi.draw_idle()

    def refresh_diag_tab(self, frame):
        diff, err = self.core.compute_rochon_balance(frame)
        self.lbl_rochon.config(
            text=f"Rochon Balance: Diff = {diff:.0f} ADU | Poisson Err = +/-{err:.0f} ADU "
                 f"(I1: {self.core.rochon_intensity1:.0f}, I2: {self.core.rochon_intensity2:.0f})"
        )

        sharp = self.core.compute_fourier_sharpness(frame)
        self.lbl_fourier.config(text=f"Image Sharpness Score: {sharp:.4f}")

        if self.core.magnitude_spectrum is not None:
            self.ax_fft.clear()
            self.ax_fft.imshow(np.log1p(self.core.magnitude_spectrum), cmap="inferno", aspect="auto")
            self.ax_fft.set_title("2D Fast Fourier Transform Magnitude Spectrum")
            self.fig_diag.tight_layout()
            self.canvas_diag.draw_idle()

    # -------------------------------------------------------------------------
    # Menu Handlers
    # -------------------------------------------------------------------------

    def menu_load_config(self):
        fp = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if fp:
            self.core.load_config(fp)
            self.update_gui_from_core()

    def menu_save_config(self):
        fp = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if fp:
            self.core.save_config(fp)

    def menu_export_csv(self):
        fp = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if fp:
            self.core.export_spectrum_csv(fp)

    def menu_export_chip(self):
        fp = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Matrix", "*.txt")])
        if fp:
            self.core.export_raw_chip(fp)

    def menu_import_chip(self):
        fp = filedialog.askopenfilename(filetypes=[("Text Matrix", "*.txt")])
        if fp:
            frame = self.core.import_raw_chip(fp)
            self.refresh_all_views()

    def on_close(self):
        self.video_active = False
        if self.core.camera is not None:
            self.core.camera.shutdown()
        if self.core.rotator is not None:
            self.core.rotator.close()
        self.root.destroy()
