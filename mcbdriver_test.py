from ctypes import *
import numpy as np
from time import time

class MCBDriver:
    error_codes = {
         0: 'No error (maybe an MCB warning)',
         1: 'Det handle or other parameter is invalid',
         2: 'MCB reported error (see nMacro_err & nMicro_err)',
         3: 'Disk, Network or MCB I/O error (see nMacro_err)',
        -1: 'Detector Comm Broken, Call MIOCloseDetector()',
        -2: 'Detector communication timeout -- Try Again',
        -3: 'Detector communication error -- Try Again',
        -4: 'Too Many open detectors -- close detector then try again',
        -5: 'Disk, OS or any other error',
         4: 'Memory allocation error',
         5: 'Authorization or Password failure ',
         8: 'MCBCIO call before MIOStartup() or after MIOCleanup()',
         9: 'Connection not open, Used only by UMCBI.OCX',
        10: 'Unexpected internal error, Used only by UMCBI.OCX',
        11: 'Requested operation is not supported by MCB <6.00>'
    }

    macro_codes = {
          0: 'Success',
          1: 'Power-up just occurred',
          2: 'Battery-backed data lost',
        129: 'Command syntax error',
        131: 'Command execution error',
        132: 'Invalid Command'
    }

    macro_error_codes = {
          1: 'Invalid Verb',
          2: 'Invalid Noun',
          4: 'Invalid Modifier',
        128: 'Invalid first parameter',
        129: 'Invalid second parameter',
        130: 'Invalid third parameter',
        131: 'Invalid fourth parameter',
        132: 'Invalid number of parameters',
        133: 'Invalid command',
        134: 'Response buffer too small',
        135: 'Not applicable while active',
        136: 'Invalid command in this mode',
        137: 'Hardware error',
        138: 'Requested data not found'
    }

    micro_codes = {
          0: 'Success',
          1: 'Input already started/stopped',
          2: 'Preset already exceeded',
          4: 'Input not stared/stopped',
         64: 'Parameter was rounded (for decimal numbers)',
        128: 'No sample data available'
    }

    def __init__(self):
        self.active = False
        self.buffer = np.zeros(2048)
        self.true = 0
        self.live = 0
        self.true_preset = 0
        self.live_preset = 0
        self.gate = 'OFF'
        self.lld = 0
        self.uld = 2047
        self.start_time = int(time())
        
    def __del__(self):
        pass
        
    def get_det_length(self, hdet):
        return 2048

    def get_last_error(self):
        return '', '', ''
        
    def open_detector(self, ndet):
        return 0
        
    def close_detector(self, hdet):
        pass
        
    def comm(self, hdet, cmd):
        resp = ''
        if cmd == 'START':
            self.active = True
            self.buffer = np.arange(2048)
            self.start_time = int(time())
        if cmd == 'STOP':
            self.active = False
        if cmd == 'CLEAR':
            self.buffer = np.zeros(2048)
            self.true = 0
            self.live = 0
        if cmd == 'SHOW_TRUE':
            resp = '$C' + str(self.true) + 'cccn'
        if cmd == 'SHOW_LIVE':
            resp = '$C' + str(self.live) + 'cccn'
        if cmd == 'SHOW_TRUE_PRESET':
            resp = '$C' + str(self.true_preset) + 'cccn'
        if cmd == 'SHOW_LIVE_PRESET':
            resp = '$C' + str(self.live_preset) + 'cccn'
        if cmd == 'SHOW_GATE':
            resp = '$F0' + self.gate + 'n'
        if cmd == 'SHOW_LLD':
            resp = '$C' + str(self.lld) + 'cccn'
        if cmd == 'SHOW_ULD':
            resp = '$C' + str(self.uld) + 'cccn'
        if cmd[:9] == 'SET_TRUE ':
            self.true = int(cmd[9:])
        if cmd[:9] == 'SET_LIVE ':
            self.live = int(cmd[9:])
        if cmd[:9] == 'SET_TRUE_':
            self.true_preset = int(cmd[16:])
        if cmd[:9] == 'SET_LIVE_':
            self.live_preset = int(cmd[16:])
        if cmd[:8] == 'SET_GATE':
            self.gate = cmd[9:]
        if cmd[:7] == 'SET_LLD':
            self.lld = int(cmd[8:])
        if cmd[:7] == 'SET_ULD':
            self.uld = int(cmd[8:])
        return resp
        
    def get_config_max(self):
        return 1
        
    def get_config_name(self, ndet):
        return 'test', 1
        
    def get_data(self, hdet, start_chan=0, num_chans=2048):
        return self.buffer

    def get_start_time(self, hdet):
        return self.star_time
            
    def is_active(self, hdet):
        return self.active