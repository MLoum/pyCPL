# -*- coding: utf-8 -*-
"""
Created on Sun Jan  9 20:14:46 2022

@author: utilisateur
"""

from hardware.camera import Camera
import numpy as np


class DummyCamera(Camera):
    def __init__(self):
        super().__init__()
        
        
    def snap(self):
        self.current_image = np.random.random((self.height, self.width, 1)) * 10
        