# -*- coding: utf-8 -*-
"""
Created on Sun Jan  9 15:52:07 2022

@author: utilisateur
"""
import numpy as np
from hardware.camera_IDS import Camera_IDS

class CPLCore():
    def __init__(self, nb_pixel=1024, nb_image_for_average=20):
        self.camera = Camera_IDS()
        self.nb_pixel = nb_pixel
        
        self.nb_image_for_average = nb_image_for_average
        self.num_current_image = 0
        self.full_chip_image = None

        # FIXME
        self.Coeff = [0, 0, 0, 0]
        self.Coeffr = [0, 0, 0, 0]
        self.wl = np.arange(self.nb_pixel)

        self.CPL_right = np.zeros(self.nb_pixel)
        self.CPL_left = np.zeros(self.nb_pixel)
        self.CPL_gem = np.zeros(self.nb_pixel)
        
        self.ROI_CPL_Left = [None, None]
        self.ROI_CPL_Right = [None, None]


        self.threshold_spec = 50
        self.threshold_gem = 1
        
        self.CPL_calibration_left = np.ones(self.nb_pixel)
        self.CPL_calibration_right = np.ones(self.nb_pixel)
        
        """
        Il faut :
        - acquerir une image (ou plusieurs + moyenne/somme)
        - Extraire les spectres droit et gauche (ROI)
        - Appliquer les calibrations
        - Calculer la difference
        
        
        Autres fonctions :
            - Calibration en X<->Lambda
            - Calibration absolue en intensité -> une courbe de coeff
        
        """

    def changeROI(self, ROIs):
        self.ROI_CPL_Left = [ROIs[0], ROIs[1]]
        self.ROI_CPL_Right = [ROIs[2], ROIs[3]]
        
    def getSpectraFromFullChipImage(self, image):

        self.CPL_left = (image[ self.ROI_CPL_Left[0]:self.ROI_CPL_Left[1], :]).astype(np.float64)
        self.CPL_right = (image[self.ROI_CPL_Right[0]:self.ROI_CPL_Right[1], :]).astype(np.float64)

        self.CPL_left[self.CPL_left  < self.threshold_spec] = 0
        self.CPL_right[self.CPL_right < self.threshold_spec] = 0

        # self.CPL_left = np.average(self.CPL_left, axis=0)
        # self.CPL_right = np.average(self.CPL_right, axis=0)

        self.CPL_left = np.sum(self.CPL_left, axis=0)
        self.CPL_right = np.sum(self.CPL_right, axis=0)

        self.CPL_left  *= self.CPL_calibration_left
        self.CPL_right *= self.CPL_calibration_right
                        
        self.CPL_gem = 2 * (self.CPL_right - self.CPL_left) / (self.CPL_right + self.CPL_left)
        #FIXME 50
        # self.CPL_gem[self.CPL_left < 50] = 0

        self.CPL_gem[abs(self.CPL_gem) > self.threshold_gem] = 0


        self.photonright = self.CPL_right * self.camera.well / self.camera.codage
        self.photonleft = self.CPL_left * self.camera.well / self.camera.codage

        self.Incertitude = np.sqrt((np.sqrt(4 * self.photonright + 4 * self.photonleft) / (2 * self.photonright - 2 * self.photonleft)) ** 2 + (np.sqrt(self.photonright + self.photonleft) / (self.photonright + self.photonleft)) ** 2) * (2 * self.photonright - 2 * self.photonleft) / (self.photonright + self.photonleft)



    def changeCoeffCalib(self,A,B,C,D):
        self.Coeff = [A,B,C,D]
        self.wl = np.arange(self.nb_pixel)
        self.wl = self.Coeff[0]*self.wl**3 + self.Coeff[1]*self.wl**2 + self.Coeff[2]*self.wl + self.Coeff[3]
        print(self.wl)

    def changecalculcalib(self,X1,X2,X3,X4,Y1,Y2,Y3,Y4):
        self.M1 = np.array([[X1**3,X1**2,X1,1],[X2**3,X2**2,X2,1],[X3**3,X3**2,X3,1],[X4**3,X4**2,X4,1]])
        self.M2 = np.linalg.det(self.M1)
        self.tamponA1 = np.array([[Y1,X1**2,X1,1],[Y2,X2**2,X2,1],[Y3,X3**2,X3,1],[Y4,X4**2,X4,1]])
        self.tamponA2 = np.linalg.det(self.tamponA1)
        self.tamponB1 = np.array([[X1**3,Y1,X1,1],[X2**3,Y2,X2,1],[X3**3,Y3,X3,1],[X4**3,Y4,X4,1]])
        self.tamponB2 = np.linalg.det(self.tamponB1)
        self.tamponC1 = np.array([[X1**3,X1**2,Y1,1],[X2**3,X2**2,Y2,1],[X3**3,X3**2,Y3,1],[X4**3,X4**2,Y4,1]])
        self.tamponC2 = np.linalg.det(self.tamponC1)
        self.tamponD1 = np.array([[X1**3,X1**2,X1,Y1],[X2**3,X2**2,X2,Y2],[X3**3,X3**2,X3,Y3],[X4**3,X4**2,X4,Y4]])
        self.tamponD2 = np.linalg.det(self.tamponD1)
        self.Coeff[0] = self.tamponA2 / self.M2
        self.Coeff[1] = self.tamponB2 / self.M2
        self.Coeff[2] = self.tamponC2 / self.M2
        self.Coeff[3] = self.tamponD2 / self.M2
        self.wl = np.arange(self.nb_pixel)
        self.wl = self.Coeff[0] * self.wl ** 3 + self.Coeff[1] * self.wl ** 2 + self.Coeff[2] * self.wl + self.Coeff[3]
        self.Coeffr = self.rounder(self.Coeff)


    def rounder(self,Coeff):
        return np.round(Coeff,decimals=8)

    def exportData(self, filename):
        data = np.column_stack((self.wl, self.CPL_left,
                                self.CPL_right, self.CPL_gem, self.Incertitude))
        np.savetxt(filename, data)