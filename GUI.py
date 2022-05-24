
import tkinter as tk
from tkinter import ttk
from core import CPLCore
from hardware.camera_IDS import Camera_IDS
# from hardware.cameraThorlabs import CameraThorlabs
from hardware.dummy_Camera import DummyCamera
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import matplotlib.patches as patches
from matplotlib.widgets import Cursor
from matplotlib.widgets import Cursor
import matplotlib.ticker as ticker
from tkinter import filedialog
import numpy as np




import threading
import time

class pyCPL():
    def __init__(self):
        self.root = tk.Tk()
        self.camera = Camera_IDS()
        # self.camera = CameraThorlabs()
        self.core = CPLCore(nb_pixel=self.camera.width.value)
        # self.camera = DummyCamera()
        self.graphe_profile_h_data = None




        self.create_gui()
        self.exposure_camera_sv.set("{:.2f}".format(self.camera.getExposure()))


        self.video_loop_duration_ms = min(100, self.camera.getExposure()*1.5)

        # TODO restore previous values
        self.changeROI()
        self.num_avg = 20
        self.A = 0
        self.B = 0
        self.C = 0
        self.D = 0

        self.splash_screen = None
        self.video_on = False
        self.root.protocol("WM_DELETE_WINDOW", self.onQuit)


    def run(self):
        self.root.title("pyCPL")
        self.root.deiconify()
        self.root.mainloop()


    # def create_midi_control(self):
    #     self.midiListener = midiControl.MidiListener(self)
    #     self.register_midi_callback()
    #     self.midiListener.createGUI()

    # def create_joystick_control(self):
    #     self.joystick_listener = joystick.JoystickListener(self)
    #     self.register_joy_callback()
    #     self.joystick_listener.createGUI()

    def create_gui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")
        
        s = ttk.Style()
        s.theme_create( "MyStyle", parent="alt", settings={
        "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0] } },
        "TNotebook.Tab": {"configure": {"padding": [100, 10],
                                        "font" : ('URW Gothic L', '11', 'bold')},}})
        s.theme_use("MyStyle")
        
        # ACQUISITION
        self.frame_acq = tk.Frame(self.notebook)
        self.frame_acq.pack(side="top", fill="both", expand=True)


        self.notebook.add(self.frame_acq, text='Acquisition')
       
        self.frame_left_part = tk.Frame(self.frame_acq)
        self.frame_left_part.pack(side="left", fill="both", expand=True)
        
        self.frame_cmd = tk.LabelFrame(self.frame_left_part, text="Cmd",
                     borderwidth=2)    
        self.frame_cmd.pack(side="top", fill="both", expand=True)
        
        tk.Button(self.frame_cmd, text="Snap", command=self.snap).grid(row=0, column=1)
        tk.Button(self.frame_cmd, text="Video", command=self.start_video).grid(row=0, column=2)
        tk.Button(self.frame_cmd, text="Stop", command=self.stop_video).grid(row=0, column=3)
        tk.Button(self.frame_cmd, text="Export", command=self.export).grid(row=1, column=0, columnspan=3)
        tk.Button(self.frame_cmd, text="Average", command=self.averageGEM).grid(row=2, column=0, columnspan=3)
        tk.Button(self.frame_cmd, text="Sum", command=self.sumGEM).grid(row=3, column=0, columnspan=3)
        tk.Button(self.frame_cmd, text="Auto ROI", command=self.autoROI).grid(row=4, column=0, columnspan=3)
        tk.Button(self.frame_cmd, text="Auto Exposure", command=self.autoExposure).grid(row=5, column=0, columnspan=3)





        self.frame_camera_main_ppty = tk.LabelFrame(self.frame_left_part, text="Main Param",
             borderwidth=2)        
        self.frame_camera_main_ppty.pack(side="top", fill="both", expand=True)

        tk.Label(self.frame_camera_main_ppty, text='Exposure (ms)').grid(row=0, column=0)
        self.exposure_camera_sv = tk.StringVar()
        e = tk.Entry(self.frame_camera_main_ppty, textvariable=self.exposure_camera_sv, justify=tk.CENTER, width=12)
        e.grid(row=0, column=1)
        e.bind('<Return>', lambda e: self.chage_exposure_from_main())
        self.exposure_camera_sv.set("100")

        self.sum_up_param_roi_left_sv = tk.StringVar()
        tk.Label(self.frame_camera_main_ppty, text='').grid(row=1, column=0)
        self.sum_up_param_roi_right_sv = tk.StringVar()
        tk.Label(self.frame_camera_main_ppty, text='').grid(row=2, column=0)


        tk.Label(self.frame_camera_main_ppty, text='Num frame to average').grid(row=3, column=0)
        self.num_frame_avg_sv = tk.StringVar()
        e = tk.Entry(self.frame_camera_main_ppty, textvariable=self.num_frame_avg_sv, justify=tk.CENTER, width=12)
        e.grid(row=3, column=1)
        e.bind('<Return>', lambda e: self.change_nb_frame_avg())
        self.exposure_camera_sv.set("100")

        tk.Label(self.frame_camera_main_ppty, text='Spectrum Threshold').grid(row=4, column=0)
        self.spectrum_threshold_sv = tk.StringVar()
        e = tk.Entry(self.frame_camera_main_ppty, textvariable=self.spectrum_threshold_sv, justify=tk.CENTER, width=12)
        e.grid(row=4, column=1)
        e.bind('<Return>', lambda e: self.change_threshold_spectrum())
        self.spectrum_threshold_sv.set("50")

        tk.Label(self.frame_camera_main_ppty, text='CPL Threshold').grid(row=5, column=0)
        self.cpl_threshold_sv = tk.StringVar()
        e = tk.Entry(self.frame_camera_main_ppty, textvariable=self.cpl_threshold_sv, justify=tk.CENTER, width=12)
        e.grid(row=5, column=1)
        e.bind('<Return>', lambda e: self.change_threshold_CPL())
        self.cpl_threshold_sv.set("1")


        
        # FULL CHIP
        self.frame_full_chip = tk.LabelFrame(self.frame_left_part, text="Full chip",
                     borderwidth=2)        
        self.frame_full_chip.pack(side="top", fill="both", expand=True)

        self.figure_full_chip_thumb = plt.Figure(figsize=(3*5/4, 3), dpi=100)
        self.ax_full_chip_thumb = self.figure_full_chip_thumb.add_subplot(111)

        plt.subplots_adjust(hspace=0)
        self.figure_full_chip_thumb.set_tight_layout(True)
        self.canvas_full_chip_thumb = FigureCanvasTkAgg(self.figure_full_chip_thumb, master=self.frame_full_chip)

        # self.toolbar = NavigationToolbar2Tk(self.canvas_full_chip_thumb, self.frame_full_chip)
        self.canvas_full_chip_thumb._tkcanvas.pack(side='top', fill='both', expand=1)


        
        self.frame_CPL_result = tk.LabelFrame(self.frame_acq, text="CPL Results",
                             borderwidth=2)
        self.frame_CPL_result.pack(side="left", fill="both", expand=True)
        
        


        # self.figure = plt.Figure(figsize=figsize, dpi=dpi)
        # self.ax = self.figure.add_subplot(111)
        #
        # self.canvas = FigureCanvasTkAgg(self.figure, master=self.frame)
        # self.canvas.get_tk_widget().pack(side='top', fill='both', expand=1)

        # self.figure, self.ax = plt.subplots(2, 1, figsize=(18, 8), dpi=50, sharex=True,
        #                        gridspec_kw={'height_ratios': [9, 1]})

        self.figure_CPL = plt.Figure(figsize=(14,6), dpi=100)
        self.ax_CPL = self.figure_CPL.add_subplot(111)
        self.ax2_CPL = self.ax_CPL.twinx()

        plt.subplots_adjust(hspace=0)
        self.figure_CPL.set_tight_layout(True)
        self.canvas_CPL = FigureCanvasTkAgg(self.figure_CPL, master=self.frame_CPL_result)
        # self.canvas.get_tk_widget().pack(side='top', fill='both', expand=1)

        self.toolbar = NavigationToolbar2Tk(self.canvas_CPL, self.frame_CPL_result)
        self.canvas_CPL._tkcanvas.pack(side='top', fill='both', expand=1)

        # CALIBRATION
        self.frame_calib = tk.Frame(self.notebook)
        self.frame_calib.pack(side="top", fill="both", expand=True)
        self.notebook.add(self.frame_calib, text='Calibration')

        self.frame_coeff = tk.LabelFrame(self.frame_calib, text="Premier choix - Coefficient de calibration sous la forme : Y(lg d'onde) = A*x^3+B*x^2+C*x+D",
                                    borderwidth=5)
        self.frame_coeff.pack(side="top", fill="x", expand=False)




        tk.Label(self.frame_coeff, text='A').grid(row=0, column=1)
        self.coeffA = tk.StringVar()
        e = tk.Entry(self.frame_coeff, textvariable=self.coeffA, justify=tk.CENTER, width=12)
        e.grid(row=2, column=1)
        e.bind('<Return>', lambda e: self.change_Calibration_A())



        tk.Label(self.frame_coeff, text='B').grid(row=0, column=2)
        self.coeffB = tk.StringVar()
        e = tk.Entry(self.frame_coeff, textvariable=self.coeffB, justify=tk.CENTER, width=12)
        e.grid(row=2, column=2)
        e.bind('<Return>', lambda e: self.change_Calibration_B())



        tk.Label(self.frame_coeff, text='C').grid(row=0, column=3)
        self.coeffC = tk.StringVar()
        e = tk.Entry(self.frame_coeff, textvariable=self.coeffC, justify=tk.CENTER, width=12)
        e.grid(row=2, column=3)
        e.bind('<Return>', lambda e: self.change_Calibration_C())



        tk.Label(self.frame_coeff, text='D').grid(row=0, column=4)
        self.coeffD = tk.StringVar()
        e = tk.Entry(self.frame_coeff, textvariable=self.coeffD, justify=tk.CENTER, width=12)
        e.grid(row=2, column=4)
        e.bind('<Return>', lambda e: self.change_Calibration_D())




        tk.Button(self.frame_coeff, text="Calibration", command=self.changeCalib).grid(row=2, column=6)

        self.frame_poly = tk.LabelFrame(self.frame_calib,text="Deuxième choix - Points du spectre de calibration (Demande obligatoirement 4 points de référence)",borderwidth=5)
        self.frame_poly.pack(side="top",fill ='x', expand=False)


        self.frame_point1 = tk.LabelFrame(self.frame_poly, text="Premier point", borderwidth=2)
        self.frame_point1.pack(side="left", fill='x', expand=False)

        tk.Label(self.frame_point1, text='Position en pixel').grid(row=0, column=4)
        self.x1 = tk.StringVar()
        e = tk.Entry(self.frame_point1, textvariable=self.x1, justify=tk.CENTER, width=12)
        e.grid(row=1, column=4)
        e.bind('<Return>', lambda e: self.change_Calibration_x1())

        tk.Label(self.frame_point1, text="Longeur d'onde (nm)").grid(row=0, column=6)
        self.y1 = tk.StringVar()
        e = tk.Entry(self.frame_point1, textvariable=self.y1, justify=tk.CENTER, width=12)
        e.grid(row=1, column=6)
        e.bind('<Return>', lambda e: self.change_Calibration_y1())


        self.frame_point2 = tk.LabelFrame(self.frame_poly, text="Deuxième point", borderwidth=2)
        self.frame_point2.pack(side="left", fill='x', expand=False)

        tk.Label(self.frame_point2, text='Position en pixel').grid(row=0, column=4)
        self.x2 = tk.StringVar()
        e = tk.Entry(self.frame_point2, textvariable=self.x2, justify=tk.CENTER, width=12)
        e.grid(row=1, column=4)
        e.bind('<Return>', lambda e: self.change_Calibration_x2())

        tk.Label(self.frame_point2, text="Longeur d'onde (nm)").grid(row=0, column=6)
        self.y2 = tk.StringVar()
        e = tk.Entry(self.frame_point2, textvariable=self.y2, justify=tk.CENTER, width=12)
        e.grid(row=1, column=6)
        e.bind('<Return>', lambda e: self.change_Calibration_y2())


        self.frame_point3 = tk.LabelFrame(self.frame_poly, text="Troisième point", borderwidth=2)
        self.frame_point3.pack(side="left", fill='x', expand=False)

        tk.Label(self.frame_point3, text='Position en pixel').grid(row=0, column=4)
        self.x3 = tk.StringVar()
        e = tk.Entry(self.frame_point3, textvariable=self.x3, justify=tk.CENTER, width=12)
        e.grid(row=1, column=4)
        e.bind('<Return>', lambda e: self.change_Calibration_x3())

        tk.Label(self.frame_point3, text="Longeur d'onde (nm)").grid(row=0, column=6)
        self.y3 = tk.StringVar()
        e = tk.Entry(self.frame_point3, textvariable=self.y3, justify=tk.CENTER, width=12)
        e.grid(row=1, column=6)
        e.bind('<Return>', lambda e: self.change_Calibration_y3())

        self.frame_point4 = tk.LabelFrame(self.frame_poly, text="Quatrième point", borderwidth=2)
        self.frame_point4.pack(side="left", fill='x', expand=False)

        tk.Label(self.frame_point4, text='Position en pixel').grid(row=0, column=4)
        self.x4 = tk.StringVar()
        e = tk.Entry(self.frame_point4, textvariable=self.x4, justify=tk.CENTER, width=12)
        e.grid(row=1, column=4)
        e.bind('<Return>', lambda e: self.change_Calibration_x4())

        tk.Label(self.frame_point4, text="Longeur d'onde (nm)").grid(row=0, column=6)
        self.y4 = tk.StringVar()
        e = tk.Entry(self.frame_point4, textvariable=self.y4, justify=tk.CENTER, width=12)
        e.grid(row=1, column=6)
        e.bind('<Return>', lambda e: self.change_Calibration_y4())

        tk.Button(self.frame_poly, text="Calibration", command=self.calculcalib).pack(side="left",fill='none',expand=False)
        tk.Button(self.frame_poly, text="Afficher le polynome", command=self.printer).pack(side="left", fill='none',expand=False)

        self.var = tk.StringVar()
        self.var.set(str(self.core.Coeffr[0]) + "*x^3 + " + str(self.core.Coeffr[1]) + "*x^2 + " + str(self.core.Coeffr[2]) + "*x + " + str(self.core.Coeffr[3]))
        t = tk.Label(self.frame_poly, textvariable=self.var)
        t.pack(side="left", fill="none", expand=False)


        # CAMERA
        self.frame_camera = tk.Frame(self.notebook)
        self.frame_camera.pack(side="top", fill="both", expand=True)
        self.notebook.add(self.frame_camera, text='Camera')


        # ROI
        self.frame_roi = tk.Frame(self.notebook)
        self.frame_roi.pack(side="top", fill="both", expand=True)
        self.notebook.add(self.frame_roi, text='ROI')


        self.frame_roi_cmd = tk.Frame(self.frame_roi)
        self.frame_roi_cmd.pack(side="left", fill="both", expand=True)

        self.frame_left_roi= tk.LabelFrame(self.frame_roi_cmd, text="ROI CPL left",
                                     borderwidth=2)

        self.frame_left_roi.pack(side="top", fill="both", expand=True)

        tk.Label(self.frame_left_roi, text='X_start').grid(row=0, column=0)
        self.x_start_left_sv = tk.StringVar()
        e = tk.Entry(self.frame_left_roi, textvariable=self.x_start_left_sv, justify=tk.CENTER, width=12)
        e.grid(row=0, column=1)
        e.bind('<Return>', lambda e: self.changeROI())
        self.x_start_left_sv.set("256")     
        
        tk.Label(self.frame_left_roi, text='X_end').grid(row=0, column=2)
        self.x_end_left_sv = tk.StringVar()
        e = tk.Entry(self.frame_left_roi, textvariable=self.x_end_left_sv, justify=tk.CENTER, width=12)
        e.grid(row=0, column=3)
        e.bind('<Return>', lambda e: self.changeROI())
        self.x_end_left_sv.set("300")      
        
        self.frame_right_roi = tk.LabelFrame(self.frame_roi_cmd, text="ROI CPL Right",
                                     borderwidth=2)

        self.frame_right_roi.pack(side="top", fill="both", expand=True)

        tk.Label(self.frame_right_roi, text='X_start').grid(row=0, column=0)
        self.x_start_rigth_sv = tk.StringVar()
        e = tk.Entry(self.frame_right_roi, textvariable=self.x_start_rigth_sv, justify=tk.CENTER, width=12)
        e.grid(row=0, column=1)
        e.bind('<Return>', lambda e: self.changeROI())
        self.x_start_rigth_sv.set("512")     
        
        tk.Label(self.frame_right_roi, text='X_end').grid(row=0, column=2)
        self.x_end_right_sv = tk.StringVar()
        e = tk.Entry(self.frame_right_roi, textvariable=self.x_end_right_sv, justify=tk.CENTER, width=12)
        e.grid(row=0, column=3)
        e.bind('<Return>', lambda e: self.changeROI())
        self.x_end_right_sv.set("600")

        self.frame_info_ROI = tk.LabelFrame(self.frame_roi, text="Informations complémentaires",
                                                 borderwidth=2)
        self.frame_info_ROI.pack(side="bottom", expand=False)

        tk.Label(self.frame_info_ROI, text='Pixel maximum =').grid(row=0, column=0)
        self.test = tk.IntVar()
        self.maximum = tk.Label(self.frame_info_ROI, textvariable=self.test).grid(row=0, column=1)



        self.frame_full_chip_ROI = tk.LabelFrame(self.frame_roi, text="Full chip Image",
                                     borderwidth=2)

        self.frame_full_chip_ROI.pack(side="left", fill="both", expand=True)

        self.frame_fig_chip = tk.Frame(self.frame_full_chip_ROI)
        self.frame_fig_chip.grid(row=0, column=0)
        self.frame_fig_h_profil = tk.Frame(self.frame_full_chip_ROI)
        self.frame_fig_h_profil.grid(row=1, column=0)
        self.frame_fig_v_profil = tk.Frame(self.frame_full_chip_ROI)
        self.frame_fig_v_profil.grid(row=0, column=1)

        self.figure_full_chip = plt.Figure(figsize=(8*5/4, 8), dpi=100)
        self.ax_full_chip = self.figure_full_chip.add_subplot(111)

        plt.subplots_adjust(hspace=0)
        self.figure_full_chip.set_tight_layout(True)
        self.canvas_full_chip = FigureCanvasTkAgg(self.figure_full_chip, master=self.frame_fig_chip)


        # self.figure_full_chip.canvas.mpl_connect('scroll_event', self.scrollEvent)
        self.figure_full_chip.canvas.mpl_connect('button_press_event', self.button_press_event)
        self.figure_full_chip.canvas.mpl_connect('button_release_event', self.button_release_event)
        self.figure_full_chip.canvas.mpl_connect('motion_notify_event', self.motion_notify_event)


        self.toolbar = NavigationToolbar2Tk(self.canvas_full_chip, self.frame_fig_chip)

        self.cursor_h = Cursor(self.ax_full_chip, useblit=True, color='red', horizOn=True, vertOn=True, linewidth=1)
        self.cursor_h.set_active(True)
        self.cursor_h.drawon = True






        self.canvas_full_chip._tkcanvas.pack(side='top', fill='both', expand=1)


        self.figure_h_profile = plt.Figure(figsize=(8*5/4, 1), dpi=100)
        self.ax_h_profile = self.figure_h_profile.add_subplot(111)


        plt.subplots_adjust(hspace=0)
        self.figure_h_profile.set_tight_layout("rect")
        self.canvas_h_profile = FigureCanvasTkAgg(self.figure_h_profile, master=self.frame_fig_h_profil)
        self.canvas_h_profile._tkcanvas.pack(side='top', fill='both', expand=1)



        self.figure_v_profile = plt.Figure(figsize=(1, 8), dpi=100)
        self.ax_v_profile = self.figure_v_profile.add_subplot(111)

        plt.subplots_adjust(hspace=0)
        self.figure_v_profile.set_tight_layout("rect")
        self.canvas_v_profile = FigureCanvasTkAgg(self.figure_v_profile, master=self.frame_fig_v_profil)
        self.canvas_v_profile._tkcanvas.pack(side='top', fill='both', expand=1)


        # self.canvas_full_chip._tkcanvas.grid(row=0, column=0)

    def change_nb_frame_avg(self):
        self.num_avg = int(self.num_frame_avg_sv.get())
    def printer(self):
        self.var.set(str(self.core.Coeffr[0]) + "*x^3 + " + str(self.core.Coeffr[1]) + "*x^2 + " + str(self.core.Coeffr[2]) + "*x + " + str(self.core.Coeffr[3]))

    def changeCalib(self):
        self.core.changeCoeffCalib(self.A, self.B, self.C, self.D)

    def calculcalib(self):
        self.core.changecalculcalib(self.X1,self.X2,self.X3,self.X4,self.Y1,self.Y2,self.Y3,self.Y4)


    def change_Calibration_x1(self):
        self.X1 = float(self.x1.get())

    def change_Calibration_x2(self):
        self.X2 = float(self.x2.get())

    def change_Calibration_x3(self):
        self.X3 = float(self.x3.get())

    def change_Calibration_x4(self):
        self.X4 = float(self.x4.get())

    def change_Calibration_y1(self):
        self.Y1 = float(self.y1.get())

    def change_Calibration_y2(self):
        self.Y2 = float(self.y2.get())

    def change_Calibration_y3(self):
        self.Y3 = float(self.y3.get())

    def change_Calibration_y4(self):
        self.Y4 = float(self.y4.get())

    def change_Calibration_A(self):
        self.A = float(self.coeffA.get())
        print(self.A)

    def change_Calibration_B(self):
        self.B = float(self.coeffB.get())
        print(self.B)

    def change_Calibration_C(self):
        self.C = float(self.coeffC.get())
        print(self.C)

    def change_Calibration_D(self):
        self.D = float(self.coeffD.get())
        print(self.D)

    def change_threshold_spectrum(self):
        self.core.threshold_spec = int(self.spectrum_threshold_sv.get())

    def change_threshold_CPL(self):
        self.core.threshold_gem = float(self.cpl_threshold_sv.get())

    def button_press_event(self, event):
        self.int_xdata = event.xdata.astype(int)
        self.int_ydata = event.ydata.astype(int)
        self.graphe_profile_v_data = self.camera.current_image[: , self.int_xdata]
        self.graphe_profile_h_data = self.camera.current_image[self.int_ydata, :  ]

        if self.graphe_profile_h_data is not None:
            self.ax_h_profile.clear()
            self.figure_h_profile.set_tight_layout("rect")
            self.ax_h_profile.plot(self.core.wl, self.graphe_profile_h_data)

            plt.tight_layout()
            # plt.yticks([])
            # self.ax_v_profile.xaxis.set_major_locator(ticker.NullLocator())

            self.figure_h_profile.canvas.draw()

        if self.graphe_profile_v_data is not None:
            self.ax_v_profile.clear()
            self.figure_v_profile.set_tight_layout("rect")
            self.ax_v_profile.plot(self.graphe_profile_v_data, np.arange(self.graphe_profile_v_data.size))

            # Remove y ticks
            # plt.yticks([])
            self.ax_v_profile.yaxis.set_major_locator(ticker.NullLocator())
            plt.tight_layout()
            self.figure_v_profile.canvas.draw()


    def button_release_event(self, event):

        if event.button == 1:
            pass
            # click gauche

    def motion_notify_event(self, event):
        pass






    def start_video(self):
        self.video_on = True
        self.root.after(int(self.video_loop_duration_ms), self.video_loop)

    def video_loop(self):
        if self.video_on:
            self.snap()
            self.root.after(int(self.video_loop_duration_ms), self.video_loop)

    def stop_video(self):
        self.video_on = False

    def changeROI(self):
        # TODO check with try if number
        x_start_left = int(self.x_start_left_sv.get())
        x_end_left = int(self.x_end_left_sv.get())
        x_start_right = int(self.x_start_rigth_sv.get())
        x_end_right = int(self.x_end_right_sv.get())

        if x_start_left > x_end_left:
            x_start_left, x_end_left = x_end_left, x_start_left
            self.x_start_left_sv.set(str(x_start_left))
            self.x_end_left_sv.set(str(x_end_left))

        if x_start_right > x_end_right:
            x_start_right, x_end_right = x_end_right, x_start_right
            self.x_start_rigth_sv.set(str(x_start_right))
            self.x_end_right_sv.set(str(x_end_right))

        self.sum_up_param_roi_left_sv.set("X_start left : " + str(x_start_left) + " X_end left : " + str(x_end_left))
        self.sum_up_param_roi_right_sv.set("X_start left : " + str(x_start_right) + " X_end left : " + str(x_end_right))

        self.core.changeROI((x_start_left, x_end_left, x_start_right, x_end_right))
        self.showThumbFullChip()
        self.showFullChip()


    def snap(self):
        errMsg = self.camera.snap()
        if (errMsg is not None):
            print("Error with camera : " + errMsg)
            return
        self.showThumbFullChip()
        self.showFullChip()
        self.core.getSpectraFromFullChipImage(self.camera.current_image)
        self.showCPL()
        self.test.set(np.amax(self.camera.current_image))



    def autoROI(self):
        self.snap()
        self.Recuperation = np.sum(self.camera.current_image, axis=1)
        i = 0
        while self.Recuperation[i] < np.mean(self.Recuperation):
            i = i + 1
            x_start_left = i-5

        while self.Recuperation[i] > np.mean(self.Recuperation):
            i = i + 1
            x_end_left = i+5

        while self.Recuperation[i] < np.mean(self.Recuperation):
            i = i + 1
            x_start_right = i-5

        while self.Recuperation[i] > np.mean(self.Recuperation):
            i = i + 1
            x_end_right = i+5
        self.core.changeROI((x_start_left, x_end_left, x_start_right, x_end_right))
        self.showThumbFullChip()
        self.showFullChip()
        self.snap()

    def autoExposure(self):
        exp = float(self.exposure_camera_sv.get())
        self.snap()
        self.max_value = np.amax(self.camera.current_image)

        # Sature ?
            # Tant que cela sature on divise, on ne peut pas savoir a priori de combien il faut diviser.
        while self.max_value > self.camera.max_auto_exposure:
            exp = exp / 1.1
            self.camera.setExposure(exp)
            self.exposure_camera_sv.set("{:.2f}".format(self.camera.getExposure()))
            self.snap()
            self.max_value = np.amax(self.camera.current_image)
            print("2 The Array is : ", self.max_value)

       # while self.max_value <= self.camera.min_auto_exposure:
        #    exp = exp * 1.1
        #   self.camera.setExposure(exp)
        #   self.exposure_camera_sv.set("{:.2f}".format(self.camera.getExposure()))
        #   self.snap()
        #   self.max_value = np.amax(self.camera.current_image)
        #   print("2 The Array is : ", self.max_value)

        # On ne sature plus ou pas
        #     self.snap()
        #     self.max_value = np.amax(self.camera.current_image)

            # print("3 The Array is: ", self.max_value)
            # print("exp is: ", exp)
            # exp *= self.camera.max_auto_exposure / self.max_value
            # self.camera.setExposure(exp)
            #
            #
            # print("exp is: ", exp)
            # print("exp is: ", self.camera.exposure_time_ms)
            #
            #
            # self.exposure_camera_sv.set("{:.2f}".format(self.camera.getExposure()))
            # self.snap()
            # self.max_value = np.amax(self.camera.current_image)
            # print("3 The Array is: ", self.max_value)
            # #ToDO fix le 3000 (et le 1.3 3000*1.3 < 4096)
            # while self.max_value < 3000:
            #     exp = exp * 1.3
            #     self.camera.setExposure(exp)
            #     self.exposure_camera_sv.set("{:.2f}".format(self.camera.getExposure()))
            #     self.snap()
            #     self.max_value = np.amax(self.camera.current_image)
            #     print("3 The Array is: ", self.max_value)




    def showThumbFullChip(self):
        if self.camera.current_image is None:
            return
        self.ax_full_chip_thumb.clear()
        self.figure_full_chip_thumb.set_tight_layout(True)
        self.ax_full_chip_thumb.imshow(self.camera.current_image)

        # ROI Left CPL
        roi_left = patches.Rectangle((0, self.core.ROI_CPL_Left[0]), self.core.nb_pixel, self.core.ROI_CPL_Left[1] - self.core.ROI_CPL_Left[0], linewidth=1, edgecolor='r', facecolor='none')
        self.ax_full_chip_thumb.add_patch(roi_left)

        # ROI Right CPL
        roi_right = patches.Rectangle((0, self.core.ROI_CPL_Right[0]), self.core.nb_pixel, self.core.ROI_CPL_Right[1] - self.core.ROI_CPL_Right[0], linewidth=1, edgecolor='b', facecolor='none')
        self.ax_full_chip_thumb.add_patch(roi_right)

        plt.tight_layout()
        self.figure_full_chip_thumb.canvas.draw()

    def showFullChip(self):
        if self.camera.current_image is None:
            return
        self.ax_full_chip.clear()
        self.figure_full_chip.set_tight_layout(True)
        self.ax_full_chip.imshow(self.camera.current_image)

        # ROI Left CPL
        roi_left = patches.Rectangle((0, self.core.ROI_CPL_Left[0]), self.core.nb_pixel, self.core.ROI_CPL_Left[1] - self.core.ROI_CPL_Left[0], linewidth=1, edgecolor='r', facecolor='none')
        self.ax_full_chip.add_patch(roi_left)

        # ROI Right CPL
        roi_right = patches.Rectangle((0, self.core.ROI_CPL_Right[0]), self.core.nb_pixel, self.core.ROI_CPL_Right[1] - self.core.ROI_CPL_Right[0], linewidth=1, edgecolor='b', facecolor='none')
        self.ax_full_chip.add_patch(roi_right)

        plt.tight_layout()
        self.figure_full_chip.canvas.draw()








    def showCPL(self):
        self.ax_CPL.clear()
        self.ax2_CPL.clear()
        self.ax_CPL.plot(self.core.wl, self.core.CPL_gem, label="glum")
        self.ax2_CPL.plot(self.core.wl, self.core.CPL_left, 'r', alpha=0.3, label="left")
        self.ax2_CPL.plot(self.core.wl, self.core.CPL_right, 'b', alpha=0.3, label="right")
        self.ax_CPL.set_xlabel("wl (nm)", fontsize=20)
        self.ax_CPL.set_ylabel("glum", fontsize=20)
        # plt.legend()
        self.figure_CPL.canvas.draw()


        
    def export(self):
        file_path = filedialog.asksaveasfile(title="Export file name ?") #initialdir=self.controller.view.saveDir
        if file_path == None or file_path == '':
            return None
        self.core.exportData(file_path.name)


    def averageGEM(self):
        cpl_left = []
        cpl_right = []
        gems = []
        for i in range(self.num_avg):
            self.snap()
            cpl_left.append(np.copy(self.core.CPL_left))
            cpl_right.append(np.copy(self.core.CPL_right))
            gems.append(np.copy(self.core.CPL_gem))

        stack = np.stack(cpl_left, axis=0)
        self.core.CPL_left = np.average(stack, axis=0)
        stack = np.stack(cpl_right, axis=0)
        self.core.CPL_right = np.average(stack, axis=0)
        stack = np.stack(gems, axis=0)
        self.core.CPL_gem = np.average(stack, axis=0)
        self.showCPL()

    def sumGEM(self):
            cpl_left = []
            cpl_right = []
            #gems = []
            for i in range(self.num_avg):
                self.snap()
                cpl_left.append(np.copy(self.core.CPL_left))
                cpl_right.append(np.copy(self.core.CPL_right))
                #gems.append(np.copy(self.core.CPL_gem))

            stack = np.stack(cpl_left, axis=0)
            self.core.CPL_left = np.sum(stack, axis=0)
            stack = np.stack(cpl_right, axis=0)
            self.core.CPL_right = np.sum(stack, axis=0)
            #stack = np.stack(gems, axis=0)
            self.core.CPL_gem = 2*(self.core.CPL_left - self.core.CPL_right) / (self.core.CPL_left + self.core.CPL_right)
            self.showCPL()


            self.core.photonright = self.core.CPL_right * self.camera.well / self.camera.codage
            self.core.photonleft = self.core.CPL_left * self.camera.well / self.camera.codage

            self.core.Incertitude = np.sqrt((np.sqrt(4 * self.core.photonright + 4 * self.core.photonleft) / (2 * self.core.photonright - 2 * self.core.photonleft)) ** 2 + (np.sqrt(self.core.photonright + self.core.photonleft) / (self.core.photonright + self.core.photonleft)) ** 2) * (2 * self.core.photonright - 2 * self.core.photonleft) / (self.core.photonright + self.core.photonleft)

    def chage_exposure_from_main(self):
        #TODO check if numeric
        exp = float(self.exposure_camera_sv.get())
        self.camera.setExposure(exp)
        self.exposure_camera_sv.set("{:.2f}".format(self.camera.getExposure()))
        self.video_loop_duration_ms = min(100, self.camera.getExposure() * 1.5)




    # def launch_ctrl(self):
    #     if self.joystick_listener is not None:
    #         self.joystick_listener.start_listening()

    # def register_midi_callback(self):
    #     self.midiListener.registerCallback(type="relative", name="MCL_X", midiCC=32, callBack=[self.dummy_XYStage.move_left, self.dummy_XYStage.move_right])
    #     self.midiListener.registerCallback(type="relative", name="MCL_Y", midiCC=33,
    #                                        callBack=[self.dummy_XYStage.move_down, self.dummy_XYStage.move_up])
    #
    #     self.midiListener.registerCallback(type="relative", name="MCL_StepX_small", midiCC=40, inc=1, tkVariable=self.dummy_XYStage.stepX_sv, callBack=[self.dummy_XYStage.get_GUI_params, self.dummy_XYStage.get_GUI_params])
    #     self.midiListener.registerCallback(type="relative", name="MCL_StepY_small", midiCC=41, inc=1,
    #                                        tkVariable=self.dummy_XYStage.stepY_sv, callBack=[self.dummy_XYStage.get_GUI_params, self.dummy_XYStage.get_GUI_params])
    #
    #     self.midiListener.registerCallback(type="relative", name="MCL_StepX_big", midiCC=48, inc=10, tkVariable=self.dummy_XYStage.stepX_sv, callBack=[self.dummy_XYStage.get_GUI_params, self.dummy_XYStage.get_GUI_params])
    #     self.midiListener.registerCallback(type="relative", name="MCL_StepY_big", midiCC=49, inc=10,
    #                                        tkVariable=self.dummy_XYStage.stepY_sv, callBack=[self.dummy_XYStage.get_GUI_params, self.dummy_XYStage.get_GUI_params])

    # def register_joy_callback(self):
    #
    #
    #     if self.madLibCity_XY is not None:
    #         self.joystick_listener.registerCallback(type="button", num=0, name="MCL_dblStep",
    #                                                 callBack=self.madLibCity_XY.double_step)
    #         self.joystick_listener.registerCallback(type="button", num=1, name="MCL_halfStep",
    #                                                 callBack=self.madLibCity_XY.halve_step)
    #
    #         self.joystick_listener.registerCallback(type="axis", num=1, name="MCL_up", callBack=self.madLibCity_XY.move_right)
    #         self.joystick_listener.registerCallback(type="axis", num=-1, name="MCL_down", callBack=self.madLibCity_XY.move_left)
    #         self.joystick_listener.registerCallback(type="axis", num=2, name="MCL_left", callBack=self.madLibCity_XY.move_down)
    #         self.joystick_listener.registerCallback(type="axis", num=-2, name="MCL_right", callBack=self.madLibCity_XY.move_up)



    def launchAquistion():
        """
        - Prendre une/(plusieurs + moyenne) image avec la camera (bloquant ou non ?) -> camera Snap
        - Calculer la gem avec le core
        - Afficher l'image full chip avec les ROI
        - Afficher la GEM

        pass
        """


    def writeParametersOnIniFile(self):
        f = open("parameters.ini", "w")
        f.write(str(self.core.ROI_CPL_Left[0]) + "\n")
        f.write(str(self.core.ROI_CPL_Left[1]) + "\n")
        f.write(str(self.core.ROI_CPL_Right[0]) + "\n")
        f.write(str(self.core.ROI_CPL_Right[1]) + "\n")


    def onQuit(self):
        # paramFile = open('param.ini', 'w')
        # paramFile.write(self.saveDir)
        self.root.destroy()
        self.root.quit()




