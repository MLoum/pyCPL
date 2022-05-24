# -*- coding: utf-8 -*-
"""
Created on Sun Jan  9 14:14:39 2022

@author: utilisateur
"""

from pyueye import ueye
import numpy as np
import ctypes
from hardware.camera import Camera


# TODO :
# Tps de pose / Gain, etc...
# Binning

"""
def is_SetGainBoost(hCam, mode):

    :param hCam: c_uint (aka c-type: HIDS)
    :param mode: c_int (aka c-type: INT)
    :returns: success, or no success, that is the answer
    :raises NotImplementedError: if function could not be loaded

def is_SetBinning(hCam, mode):
    
    :param hCam: c_uint (aka c-type: HIDS)
    :param mode: c_int (aka c-type: INT)
    :returns: success, or no success, that is the answer
    :raises NotImplementedError: if function could not be loaded
    


def is_SetHardwareGain(hCam, nMaster, nRed, nGreen, nBlue):
   
    :param hCam: c_uint (aka c-type: HIDS)
    :param nMaster: c_int (aka c-type: INT)
    :param nRed: c_int (aka c-type: INT)
    :param nGreen: c_int (aka c-type: INT)
    :param nBlue: c_int (aka c-type: INT)
    :returns: success, or no success, that is the answer
    :raises NotImplementedError: if function could not be loaded
    
    if _is_SetHardwareGain is None:
        raise NotImplementedError()

    _hCam = _value_cast(hCam, ctypes.c_uint)
    _nMaster = _value_cast(nMaster, ctypes.c_int)
    _nRed = _value_cast(nRed, ctypes.c_int)
    _nGreen = _value_cast(nGreen, ctypes.c_int)
    _nBlue = _value_cast(nBlue, ctypes.c_int)

    ret = _is_SetHardwareGain(_hCam, _nMaster, _nRed, _nGreen, _nBlue)

    return ret



def is_SetFrameRate(hCam, FPS, newFPS):
    
    :param hCam: c_uint (aka c-type: HIDS)
    :param FPS: c_double (aka c-type: double)
    :param newFPS: c_double (aka c-type: double \*)
    :returns: success, or no success, that is the answer
    :raises NotImplementedError: if function could not be loaded
    
    if _is_SetFrameRate is None:
        raise NotImplementedError()

    _hCam = _value_cast(hCam, ctypes.c_uint)
    _FPS = _value_cast(FPS, ctypes.c_double)

    ret = _is_SetFrameRate(_hCam, _FPS, ctypes.byref(newFPS))

    return ret


_is_GetFramesPerSecond = _bind("is_GetFramesPerSecond", [ctypes.c_uint, ctypes.POINTER(ctypes.c_double)], ctypes.c_int)


def is_GetFramesPerSecond(hCam, dblFPS):
    
    :param hCam: c_uint (aka c-type: HIDS)
    :param dblFPS: c_double (aka c-type: double \*)
    :returns: success, or no success, that is the answer
    :raises NotImplementedError: if function could not be loaded
    
    if _is_GetFramesPerSecond is None:
        raise NotImplementedError()

    _hCam = _value_cast(hCam, ctypes.c_uint)

    ret = _is_GetFramesPerSecond(_hCam, ctypes.byref(dblFPS))

    return ret





"""


#TODO Virtual class etc
class Camera_IDS(Camera):
    def __init__(self):
        super().__init__(width=1280, height=1024)
        self.hCam = ueye.HIDS(0)             #0: first available camera;  1-254: The camera with the specified camera ID
        self.sInfo = ueye.SENSORINFO()
        self.cInfo = ueye.CAMINFO()
        self.pcImageMemory = ueye.c_mem_p()
        self.MemID = ueye.int()
        self.rectAOI = ueye.IS_RECT()
        self.pitch = ueye.INT()
        self.channels = 1                    #3: channels for color mode(RGB); take 1 channel for monochrome
        self.exposure_time_ms = ueye.DOUBLE()
        self.max_auto_exposure = 4096*0.95
        self.min_auto_exposure = 4096 * 0.75
        self.well = 2**12
        self.codage = 2**12

        # We use the model : UI324xML-NIR
        #self.m_nColorMode = ueye.IS_CM_MONO12
        self.m_nColorMode = ueye.IS_CM_SENSOR_RAW12

        self.nBitsPerPixel = ueye.INT(16)
        self.bytes_per_pixel = int(self.nBitsPerPixel / 8)

        self.initHardware()
        self.resetToDefault()
        self.getCameraInfo()
        self.getSensorInfo()
        self.setDisplayMode()
        self.setColorMode()
        self.getAOI()   #should be the default one (i.e "full chip")        
        self.allocateImageMemory()
        self.printInfo()





    def initHardware(self):
        # Starts the driver and establishes the connection to the camera
        nRet = ueye.is_InitCamera(self.hCam, None)
        if nRet != ueye.IS_SUCCESS:
            return "is_InitCamera ERROR"
        else:
            return 0


    def exitHardware(self):
        nRet = ueye.is_ExitCamera(self.hCam)
        if nRet != ueye.IS_SUCCESS:
            return "is_ExitCamera ERROR" + nRet

        nRet =  ueye.is_FreeImageMem(self.hCam, self.pcImageMemory, self.MemID)
        if nRet != ueye.IS_SUCCESS:
            return "is_FreeImageMem ERROR" + nRet

        return None

    def stop(self):
        pass

    def getCameraInfo(self):
        # Reads out the data hard-coded in the non-volatile camera memory and writes it to the data structure that cInfo points to
        nRet = ueye.is_GetCameraInfo(self.hCam, self.cInfo)
        if nRet != ueye.IS_SUCCESS:
            return "is_GetCameraInfo ERROR"
        else:
            return nRet

    def getSensorInfo(self):
        # You can query additional information about the sensor type used in the camera
        nRet = ueye.is_GetSensorInfo(self.hCam, self.sInfo)
        if nRet != ueye.IS_SUCCESS:
            return "is_GetSensorInfo ERROR"
        else:
            return 0

    def setDisplayMode(self):
        # Set display mode to bitmap (DIB) display mode (other alternative : direct3D or openGL)
        nRet = ueye.is_SetDisplayMode(self.hCam, ueye.IS_SET_DM_DIB)
        if nRet != ueye.IS_SUCCESS:
            return "is_setDisplayMode ERROR" + str(nRet)
        else:
            return None

    def setColorMode(self):
        nRet = ueye.is_SetColorMode(self.hCam, self.m_nColorMode)
        if nRet != ueye.IS_SUCCESS:
            return "is_setColorMode" + str(nRet)
        else:
            return None


    def getExposure(self):

        # nRet = ueye.is_Exposure(self.hCam, ueye.IS_EXPOSURE_CMD_GET_EXPOSURE, ctypes.POINTER(self.exposure_time_ms), 8)
        nRet = ueye.is_Exposure(self.hCam, ueye.IS_EXPOSURE_CMD_GET_EXPOSURE, self.exposure_time_ms, 8)
        if nRet != ueye.IS_SUCCESS:
            return "is_Exposure" + nRet
        else:
            return self.exposure_time_ms.value

    def setExposure(self, exposure_ms):
        """
        
        Note on dependencies on other settings

        The use of the following functions will affect the exposure time:        
        •is_PixelClock()        
        •is_SetOptimalCameraTiming()        
        •is_SetFrameRate()        
        •is_AOI() (if the image size is changed)        
        •is_SetSubSampling()        
        •is_SetBinning()
        
        Changes made to the image size, the frame rate or the pixel clock frequency also affect the exposure time. For this reason, you need to call is_Exposure() again after such changes.
        
        In general, the pixel clock is set once when opening the camera and will not be changed. Note that, if you change the pixel clock, the setting ranges for frame rate and exposure time also changes. If you change a parameter, the following order is recommended:        
        1.Change pixel clock.
        2.Query frame rate range and, if applicable, set new value.        
        3.Query exposure time range and, if applicable, set new value.
        If one parameter is changed, the following parameters have to be adjusted due to the dependencies.


        Accuracy of the exposure time setting
        -------------------------------------
        
        The increments for setting the exposure time (IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_INC) depend on the sensor's current timing settings (pixel clock, frame rate). The smallest increment usually corresponds to the duration of one pixel row, which is the time it takes the sensor to read out one pixel row.        
        You can query the actual exposure time setting with the IS_EXPOSURE_CMD_GET_EXPOSURE parameter.        
        Some sensors allow setting the exposure time in smaller increments. Using the IS_EXPOSURE_CMD_GET_CAPS parameter, you can check whether your sensor supports this function.        
        For minimum and maximum exposure times as well as other sensor-based dependencies, please refer to the Camera and sensor data chapter.

        Parameters
        ----------
        exposure_ms : TYPE
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """

        #pParam: Pointer to variable of type double that passes the value to be set. After setting the exposure time this value contains the actually set exposure time. Depending on the sensor the set exposure time may vary slightly from the desired exposure time.        
        self.exposure_time_ms = ueye.c_double(exposure_ms)
        # nRet = ueye.is_Exposure(self.hCam, ueye.IS_EXPOSURE_CMD_SET_EXPOSURE, ctypes.POINTER(self.exposure_time_ms), 8)
        nRet = ueye.is_Exposure(self.hCam, ueye.IS_EXPOSURE_CMD_SET_EXPOSURE, self.exposure_time_ms, 8)
        if nRet != ueye.IS_SUCCESS:
            return "is_Exposure" + nRet
        else:
            return None


    def getExposureInfo(self):
        """
        IS_EXPOSURE_CMD_GET_EXPOSURE
	
        Returns the currently set exposure time (in ms).
        
        •pParam: Pointer to variable of type double returning the current value.
        
        •nSizeOfParam: 8
        
        IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_MIN
        	
        
        Returns the minimum exposure time.
        
        •pParam: Pointer to variable of type double returning the minimum value.
        
        •nSizeOfParam: 8
        
        IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_MAX
        	
        
        Returns the maximum exposure time.
        
        •pParam: Pointer to variable of type double returning the maximum value.
        
        •nSizeOfParam: 8
        
        IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_INC
        	
        
        Returns the exposure time increment.
        
        •pParam: Pointer to variable of type double returning the increment.
        
        •nSizeOfParam: 8
        
        IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE
        	
        
        Returns the exposure time range.
        
        •pParam: Pointer to array of type double returning the minimum and maximum values and the increment (in exactly this order).
        
        •nSizeOfParam: 24

        Returns
        -------
        None.

        """
        #TODO
        pass

    def setBinning(self):
        #TODO
        pass


    def resetToDefault(self):
        nRet = ueye.is_ResetToDefault(self.hCam)
        if nRet != ueye.IS_SUCCESS:
            return "is_ResetToDefault ERROR" + str(nRet)
        else:
            return None

    def getAOI(self):
        # Can be used to set the size and position of an "area of interest"(AOI) within an image
        nRet = ueye.is_AOI(self.hCam, ueye.IS_AOI_IMAGE_GET_AOI, self.rectAOI, ueye.sizeof(self.rectAOI))
        if nRet != ueye.IS_SUCCESS:
            return "is_AOI ERROR" + str(nRet)
        else:
            #FIXME I need to swap width and height <-> error in the python wraper ?
            self.width = self.rectAOI.s32Width
            self.height = self.rectAOI.s32Height
            # self.width = self.rectAOI.s32Height
            # self.height = self.rectAOI.s32Width
            return None

    def printInfo(self):
        # Prints out some information about the camera and the sensor
        print("Camera model:\t\t", self.sInfo.strSensorName.decode('utf-8'))
        print("Camera serial no.:\t", self.cInfo.SerNo.decode('utf-8'))
        print("Maximum image width:\t", self.width)
        print("Maximum image height:\t", self.height)
        print()

    def allocateImageMemory(self):
        # Allocates an image memory for an image having its dimensions defined by width and height and its color depth defined by nBitsPerPixel
        nRet = ueye.is_AllocImageMem(self.hCam, self.width, self.height, self.nBitsPerPixel, self.pcImageMemory, self.MemID)
        if nRet != ueye.IS_SUCCESS:
            return "is_AllocImageMem ERROR" + str(nRet)

        # Makes the specified image memory the active memory
        nRet = ueye.is_SetImageMem(self.hCam, self.pcImageMemory, self.MemID)
        if nRet != ueye.IS_SUCCESS:
            return "is_SetImageMem ERROR" + str(nRet)


        # is_InquireImageMem() reads out the properties of an allocated image memory.
        """
        hCam Camera handle        
        pMem Pointer to the starting address of the image memory as allocated by is_AllocImageMem()        
        nMemId ID of the image memory as allocated by is_AllocImageMem()        
        pnX Returns the width used to define the image memory. You can also pass NULL instead.        
        pnY Returns the height used to define the image memory. You can also pass NULL instead.        
        pnBits Returns the bit width used to define the image memory. You can also pass NULL instead.        
        pnPitch Returns the line increment of the image memory. You can also pass NULL instead.
        """
        nRet = ueye.is_InquireImageMem(self.hCam, self.pcImageMemory, self.MemID, self.width, self.height, self.nBitsPerPixel, self.pitch)
        if nRet != ueye.IS_SUCCESS:
            return "is_InquireImageMem ERROR" + nRet
        else:
            return None




    def snap(self):
        """
        is_FreezeVideo() acquires a single image from the camera. 
        In DIB mode, the image is stored in the active image memory. 
        If ring buffering is used in DIB mode, the captured image is transferred to the next available image memory of the sequence. 
        Once the last available sequence memory has been filled, 
        the sequence event or message will be triggered.
        """
        nRet = ueye.is_FreezeVideo(self.hCam, Wait=ueye.IS_DONT_WAIT)
        if nRet != ueye.IS_SUCCESS:
            return "is_FreezeVideo ERROR" + self.errorNumberToMessage(nRet)
        else:
            # NB : get_data does not belong to the ueye API
            # array = ueye.get_data(self.pcImageMemory, self.width, self.height, self.nBitsPerPixel, self.pitch, copy=False)


            # Create a numpy array from a ctypes array or POINTER.
            # The numpy array shares the memory with the ctypes object.
            data = np.ctypeslib.as_array(ctypes.cast(self.pcImageMemory, ctypes.POINTER(ctypes.c_ushort)), (self.height.value, self.width.value))
            # bytes_per_pixel = int(nBitsPerPixel / 8)

            # ...reshape it in an numpy array...
            self.current_image = np.reshape(data, (self.height.value, self.width.value))

            #TODO multiple images

            return None

    def errorNumberToMessage(self, nRet):
        return "TODO : translate nRet to text"

    '''
    if nRet == 1:
        return "IS_INVALID_CAMERA_HANDLE"
        
    IS_INVALID_CAMERA_HANDLE = 1
    IS_INVALID_HANDLE = 1
    IS_IO_REQUEST_FAILED = 2
    IS_CANT_OPEN_DEVICE = 3
    IS_CANT_CLOSE_DEVICE = 4
    IS_CANT_SETUP_MEMORY = 5
    IS_NO_HWND_FOR_ERROR_REPORT = 6
    IS_ERROR_MESSAGE_NOT_CREATED = 7
    IS_ERROR_STRING_NOT_FOUND = 8
    IS_HOOK_NOT_CREATED = 9
    IS_TIMER_NOT_CREATED = 10
    IS_CANT_OPEN_REGISTRY = 11
    IS_CANT_READ_REGISTRY = 12
    IS_CANT_VALIDATE_BOARD = 13
    IS_CANT_GIVE_BOARD_ACCESS = 14
    IS_NO_IMAGE_MEM_ALLOCATED = 15
    IS_CANT_CLEANUP_MEMORY = 16
    IS_CANT_COMMUNICATE_WITH_DRIVER = 17
    IS_FUNCTION_NOT_SUPPORTED_YET = 18
    IS_OPERATING_SYSTEM_NOT_SUPPORTED = 19
    IS_INVALID_VIDEO_IN = 20
    IS_INVALID_IMG_SIZE = 21
    IS_INVALID_ADDRESS = 22
    IS_INVALID_VIDEO_MODE = 23
    IS_INVALID_AGC_MODE = 24
    IS_INVALID_GAMMA_MODE = 25
    IS_INVALID_SYNC_LEVEL = 26
    IS_INVALID_CBARS_MODE = 27
    IS_INVALID_COLOR_MODE = 28
    IS_INVALID_SCALE_FACTOR = 29
    IS_INVALID_IMAGE_SIZE = 30
    IS_INVALID_IMAGE_POS = 31
    IS_INVALID_CAPTURE_MODE = 32
    IS_INVALID_RISC_PROGRAM = 33
    IS_INVALID_BRIGHTNESS = 34
    IS_INVALID_CONTRAST = 35
    IS_INVALID_SATURATION_U = 36
    IS_INVALID_SATURATION_V = 37
    IS_INVALID_HUE = 38
    IS_INVALID_HOR_FILTER_STEP = 39
    IS_INVALID_VERT_FILTER_STEP = 40
    IS_INVALID_EEPROM_READ_ADDRESS = 41
    IS_INVALID_EEPROM_WRITE_ADDRESS = 42
    IS_INVALID_EEPROM_READ_LENGTH = 43
    IS_INVALID_EEPROM_WRITE_LENGTH = 44
    IS_INVALID_BOARD_INFO_POINTER = 45
    IS_INVALID_DISPLAY_MODE = 46
    IS_INVALID_ERR_REP_MODE = 47
    IS_INVALID_BITS_PIXEL = 48
    IS_INVALID_MEMORY_POINTER = 49
    IS_FILE_WRITE_OPEN_ERROR = 50
    IS_FILE_READ_OPEN_ERROR = 51
    IS_FILE_READ_INVALID_BMP_ID = 52
    IS_FILE_READ_INVALID_BMP_SIZE = 53
    IS_FILE_READ_INVALID_BIT_COUNT = 54
    IS_WRONG_KERNEL_VERSION = 55
    IS_RISC_INVALID_XLENGTH = 60
    IS_RISC_INVALID_YLENGTH = 61
    IS_RISC_EXCEED_IMG_SIZE = 62
    IS_DD_MAIN_FAILED = 70
    IS_DD_PRIMSURFACE_FAILED = 71
    IS_DD_SCRN_SIZE_NOT_SUPPORTED = 72
    IS_DD_CLIPPER_FAILED = 73
    IS_DD_CLIPPER_HWND_FAILED = 74
    IS_DD_CLIPPER_CONNECT_FAILED = 75
    IS_DD_BACKSURFACE_FAILED = 76
    IS_DD_BACKSURFACE_IN_SYSMEM = 77
    IS_DD_MDL_MALLOC_ERR = 78
    IS_DD_MDL_SIZE_ERR = 79
    IS_DD_CLIP_NO_CHANGE = 80
    IS_DD_PRIMMEM_NULL = 81
    IS_DD_BACKMEM_NULL = 82
    IS_DD_BACKOVLMEM_NULL = 83
    IS_DD_OVERLAYSURFACE_FAILED = 84
    IS_DD_OVERLAYSURFACE_IN_SYSMEM = 85
    IS_DD_OVERLAY_NOT_ALLOWED = 86
    IS_DD_OVERLAY_COLKEY_ERR = 87
    IS_DD_OVERLAY_NOT_ENABLED = 88
    IS_DD_GET_DC_ERROR = 89
    IS_DD_DDRAW_DLL_NOT_LOADED = 90
    IS_DD_THREAD_NOT_CREATED = 91
    IS_DD_CANT_GET_CAPS = 92
    IS_DD_NO_OVERLAYSURFACE = 93
    IS_DD_NO_OVERLAYSTRETCH = 94
    IS_DD_CANT_CREATE_OVERLAYSURFACE = 95
    IS_DD_CANT_UPDATE_OVERLAYSURFACE = 96
    IS_DD_INVALID_STRETCH = 97
    IS_EV_INVALID_EVENT_NUMBER = 100
    IS_INVALID_MODE = 101
    IS_CANT_FIND_FALCHOOK = 102
    IS_CANT_FIND_HOOK = 102
    IS_CANT_GET_HOOK_PROC_ADDR = 103
    IS_CANT_CHAIN_HOOK_PROC = 104
    IS_CANT_SETUP_WND_PROC = 105
    IS_HWND_NULL = 106
    IS_INVALID_UPDATE_MODE = 107
    IS_NO_ACTIVE_IMG_MEM = 108
    IS_CANT_INIT_EVENT = 109
    IS_FUNC_NOT_AVAIL_IN_OS = 110
    IS_CAMERA_NOT_CONNECTED = 111
    IS_SEQUENCE_LIST_EMPTY = 112
    IS_CANT_ADD_TO_SEQUENCE = 113
    IS_LOW_OF_SEQUENCE_RISC_MEM = 114
    IS_IMGMEM2FREE_USED_IN_SEQ = 115
    IS_IMGMEM_NOT_IN_SEQUENCE_LIST = 116
    IS_SEQUENCE_BUF_ALREADY_LOCKED = 117
    IS_INVALID_DEVICE_ID = 118
    IS_INVALID_BOARD_ID = 119
    IS_ALL_DEVICES_BUSY = 120
    IS_HOOK_BUSY = 121
    IS_TIMED_OUT = 122
    IS_NULL_POINTER = 123
    IS_WRONG_HOOK_VERSION = 124
    IS_INVALID_PARAMETER = 125
    IS_NOT_ALLOWED = 126
    IS_OUT_OF_MEMORY = 127
    IS_INVALID_WHILE_LIVE = 128
    IS_ACCESS_VIOLATION = 129
    IS_UNKNOWN_ROP_EFFECT = 130
    IS_INVALID_RENDER_MODE = 131
    IS_INVALID_THREAD_CONTEXT = 132
    IS_NO_HARDWARE_INSTALLED = 133
    IS_INVALID_WATCHDOG_TIME = 134
    IS_INVALID_WATCHDOG_MODE = 135
    IS_INVALID_PASSTHROUGH_IN = 136
    IS_ERROR_SETTING_PASSTHROUGH_IN = 137
    IS_FAILURE_ON_SETTING_WATCHDOG = 138
    IS_NO_USB20 = 139
    IS_CAPTURE_RUNNING = 140
    IS_MEMORY_BOARD_ACTIVATED = 141
    IS_MEMORY_BOARD_DEACTIVATED = 142
    IS_NO_MEMORY_BOARD_CONNECTED = 143
    IS_TOO_LESS_MEMORY = 144
    IS_IMAGE_NOT_PRESENT = 145
    IS_MEMORY_MODE_RUNNING = 146
    IS_MEMORYBOARD_DISABLED = 147
    IS_TRIGGER_ACTIVATED = 148
    IS_WRONG_KEY = 150
    IS_CRC_ERROR = 151
    IS_NOT_YET_RELEASED = 152
    IS_NOT_CALIBRATED = 153
    IS_WAITING_FOR_KERNEL = 154
    IS_NOT_SUPPORTED = 155
    IS_TRIGGER_NOT_ACTIVATED = 156
    IS_OPERATION_ABORTED = 157
    IS_BAD_STRUCTURE_SIZE = 158
    IS_INVALID_BUFFER_SIZE = 159
    IS_INVALID_PIXEL_CLOCK = 160
    IS_INVALID_EXPOSURE_TIME = 161
    IS_AUTO_EXPOSURE_RUNNING = 162
    IS_CANNOT_CREATE_BB_SURF = 163
    IS_CANNOT_CREATE_BB_MIX = 164
    IS_BB_OVLMEM_NULL = 165
    IS_CANNOT_CREATE_BB_OVL = 166
    IS_NOT_SUPP_IN_OVL_SURF_MODE = 167
    IS_INVALID_SURFACE = 168
    IS_SURFACE_LOST = 169
    IS_RELEASE_BB_OVL_DC = 170
    IS_BB_TIMER_NOT_CREATED = 171
    IS_BB_OVL_NOT_EN = 172
    IS_ONLY_IN_BB_MODE = 173
    IS_INVALID_COLOR_FORMAT = 174
    IS_INVALID_WB_BINNING_MODE = 175
    IS_INVALID_I2C_DEVICE_ADDRESS = 176
    IS_COULD_NOT_CONVERT = 177
    IS_TRANSFER_ERROR = 178
    IS_PARAMETER_SET_NOT_PRESENT = 179
    IS_INVALID_CAMERA_TYPE = 180
    IS_INVALID_HOST_IP_HIBYTE = 181
    IS_CM_NOT_SUPP_IN_CURR_DISPLAYMODE = 182
    IS_NO_IR_FILTER = 183
    IS_STARTER_FW_UPLOAD_NEEDED = 184
    IS_DR_LIBRARY_NOT_FOUND = 185
    IS_DR_DEVICE_OUT_OF_MEMORY = 186
    IS_DR_CANNOT_CREATE_SURFACE = 187
    IS_DR_CANNOT_CREATE_VERTEX_BUFFER = 188
    IS_DR_CANNOT_CREATE_TEXTURE = 189
    IS_DR_CANNOT_LOCK_OVERLAY_SURFACE = 190
    IS_DR_CANNOT_UNLOCK_OVERLAY_SURFACE = 191
    IS_DR_CANNOT_GET_OVERLAY_DC = 192
    IS_DR_CANNOT_RELEASE_OVERLAY_DC = 193
    IS_DR_DEVICE_CAPS_INSUFFICIENT = 194
    IS_INCOMPATIBLE_SETTING = 195
    IS_DR_NOT_ALLOWED_WHILE_DC_IS_ACTIVE = 196
    IS_DEVICE_ALREADY_PAIRED = 197
    IS_SUBNETMASK_MISMATCH = 198
    IS_SUBNET_MISMATCH = 199
    IS_INVALID_IP_CONFIGURATION = 200
    IS_DEVICE_NOT_COMPATIBLE = 201
    IS_NETWORK_FRAME_SIZE_INCOMPATIBLE = 202
    IS_NETWORK_CONFIGURATION_INVALID = 203
    IS_ERROR_CPU_IDLE_STATES_CONFIGURATION = 204
    IS_DEVICE_BUSY = 205
    IS_SENSOR_INITIALIZATION_FAILED = 206
    IS_IMAGE_BUFFER_NOT_DWORD_ALIGNED = 207
    IS_SEQ_BUFFER_IS_LOCKED = 208
    IS_FILE_PATH_DOES_NOT_EXIST = 209
    IS_INVALID_WINDOW_HANDLE = 210
    IS_INVALID_IMAGE_PARAMETER = 211
    IS_NO_SUCH_DEVICE = 212
    IS_DEVICE_IN_USE = 213
    '''