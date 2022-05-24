# -*- coding: utf-8 -*-
"""
Created on Sun Jan  9 14:14:39 2022

@author: utilisateur
"""
import numpy as np


class Camera():
    def __init__(self, width=1024, height=1280):
        self.width = width
        self.height = height
        self.video_images = []
        self.current_image = np.zeros((self.height, self.width))
        self.video_on = False
        self.max_auto_exposure = None
        self.min_auto_exposure = None
        self.well = None
        self.codage = None
        
    def snap(self):
        pass
        
    def setExposure(self, exposure_ms):
        pass

    def getExposure(self):
        pass
    
    def setBinning(self, bin_factor):
        pass
    

    # def start_acq(self):
    #     self.thread_video = threading.Thread(name='video snap', target=self.video_loop)
    #     self.video_on = True
    #     self.thread_video.start()
    #
    # def stop_acq(self):
    #     self.video_on = False
    #     self.camera.stop()
    #     if self.thread_video.is_alive():
    #         self.thread_video.join(timeout=0.5)
    #
    # def video_loop(self):
    #     while self.video_on:
    #         self.snap()
    #         time.sleep(0.1)


    def stop(self):
        pass

