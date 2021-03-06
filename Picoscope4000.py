# -*- coding: utf-8 -*-
"""
Created on Mon Sep  8 09:41:22 2014

@author: ckattmann
"""

import sys
import ctypes
import numpy as np
import time
import datetime
import os
import platform

libname_christoph = 'C:\Program Files\Pico Technology\PicoScope6\ps4000A.dll'
libname_micha = 'C:\Program Files (x86)\Pico Technology\PicoScope6\ps4000A.dll'
libname_pokini = '/opt/picoscope/lib/libps4000a.so'

# if 1, prints diagnostics to standard output
VERBOSE = 1
# If 1, generates profile.txtpicotec
PROFILING = 0 # Attention, may redirect standard print output, restart python kernel if output disappears

## Constants of PS2000.dll
# channel identifiers
PS4000_CHANNEL_A = 0
PS4000_CHANNEL_B = 1
PS4000_CHANNEL_C = 2
PS4000_CHANNEL_D = 3
PS4000_CHANNEL_E = 4
PS4000_CHANNEL_F = 5
PS4000_CHANNEL_G = 6
PS4000_CHANNEL_H = 7
PS4000_NONE = 5

# channel range values/codes
RANGE_10mV  = 0  # 20 mV
RANGE_20mV  = 1  # 20 mV
RANGE_50mV  = 2  # 50 mV
RANGE_100mV = 3  # 100 mV
RANGE_200mV = 4  # 200 mV
RANGE_500mV = 5  # 500 mV
RANGE_1V    = 6  # 1 V
RANGE_2V    = 7  # 2 V
RANGE_5V    = 8  # 5 V
RANGE_10V   = 9  # 10 V
RANGE_20V   = 10 # 20 V
RANGE_50V   = 11 # 50 V
RANGE_100V   = 12 # 100 V
RANGE_200V   = 13 # 200 V

# map the range the the scale factor
RANGE_SCALE_MAP = {
RANGE_20mV  : 0.02,
RANGE_50mV  : 0.05,
RANGE_100mV : 0.1,
RANGE_200mV : 0.2,
RANGE_500mV : 0.5,
RANGE_1V    : 1.0,
RANGE_2V    : 2.0,
RANGE_5V    : 5.0,
RANGE_10V   : 10.0,
RANGE_20V   : 20.0,
}

#analog offset inital valiue
ANALOG_OFFSET_0V = 0# 0V offset

# Y Resolution Limits
MAX_Y = 32768
MIN_Y = -32767

# Flank Definitions for Triggering
PS2000_RISING = 0
PS2000_FALLING = 1

# Time Units
FEMTOSECONDS = 0
PICOSECONDS = 1
NANOSECONDS = 2
MICROSECONDS = 3
MILLISECONDS = 4
SECONDS = 5

                

# Set the correct dll as  LIBNAME
if sys.platform == 'win32':
    LIBNAME = libname_micha
else:
    LIBNAME = libname_pokini
     
     
class Picoscope4000:
    def __init__(self):
        self.handle = None
        self.channels = [0,0]
        self.streaming_sample_interval = ctypes.c_uint(1000)
        self.streaming_sample_interval_unit = 3
        self.streaming_buffer_length = 100

        # load the library
        if platform.system() == 'Windows':
            self.lib = ctypes.windll.LoadLibrary(LIBNAME)
        elif platform.system() == 'Linux':
            self.lib = ctypes.cdll.LoadLibrary(LIBNAME)
        else:
            print('Unknown Platform')

        # open the picoscope
        self.handle = self.open_unit()
     
        
# Basic Open and Close operations
    def open_unit(self):
        '''open interface to unit'''
        if VERBOSE == 1:
            print('==== open_unit ====')
        self.handle = ctypes.c_int16()
        picoStatus = self.lib.ps4000aOpenUnit(ctypes.byref(self.handle),None)
        print(' PicoStatus: '+str(picoStatus))
        print(' Handle is '+str(self.handle.value))
        
        #change Power Source Setup if applied to USB 2.0 / 1.0 with doubled-headed cable
        if picoStatus == 286:
            res = self.lib.ps4000aChangePowerSource(self.handle, picoStatus)
            if VERBOSE:
                print(' Wrong Powersupply detected, try changing supply mode')
            if res > 0:
                self.close_unit()
                if VERBOSE:
                    print(' Failed to change USB Power Supply')
            else:
                if VERBOSE:
                    print(' OK: Supply mode changed')
                    
        if self.handle.value == -1:
            print(' Failed to open oscilloscope')
        elif self.handle.value == 0:
            print(' No oscilloscope found')
        return self.handle

    def close_unit(self):
        '''close the interface to the unit'''
        if VERBOSE == 1:
            print('==== close_unit ====')
        res = self.lib.ps4000aCloseUnit(self.handle.value)
        print(' '+str(res))
        self.handle = None
        return res
        
    def get_handle(self):
        '''returns oscilloscope handle'''
        return self.handle
        
        
# Setup Operations
    def set_channel(self, channel=PS4000_CHANNEL_A, enabled=True, dc=True, vertrange=RANGE_20V, analogOffset=ANALOG_OFFSET_0V):
        '''Default Values: channel: Channel A | channel enabled: true | ac/dc coupling mode: dc(=true) | vertical range: 2Vpp'''
        if VERBOSE:
            print('==== SetChannel ====')
        try:
            res = self.lib.ps4000aSetChannel(self.handle, channel, enabled, dc, vertrange, analogOffset)
            if channel == PS4000_CHANNEL_A:
                self.channels[0] = 1
            elif channel == PS4000_CHANNEL_B:
                self.channels[1] = 1
            if VERBOSE == 1:
                print(' Channel set to Channel '+str(channel))
                print(' Status of setChannel '+str(res)+' (0 = PICO_OK)')
        finally:
            pass
        
# Set Data Buffer for each channel of the PS4824 scope      
    def set_data_buffer(self, channel=PS4000_CHANNEL_A, segmentIndex=0, mode=0):
        print('==== SetDataBuffer ====')
        bufferlength = self.streaming_buffer_length
        try:
            if channel == PS4000_CHANNEL_A: #channel A is set
                self.channel_A_buffer=(ctypes.c_short * bufferlength)()
                #self.streaming_buffer_length = bufferlength
                res = self.lib.ps4000aSetDataBuffer(self.handle,channel,ctypes.byref(self.channel_A_buffer),self.streaming_buffer_length,segmentIndex,mode)
            if channel == PS4000_CHANNEL_B: #channel B is set
                self.channel_B_buffer=(ctypes.c_short * bufferlength)()
                #self.streaming_buffer_length = bufferlength
                res = self.lib.ps4000aSetDataBuffer(self.handle,channel,ctypes.byref(self.channel_B_buffer),self.streaming_buffer_length,segmentIndex,mode)
            if channel == PS4000_CHANNEL_C: #channel C is set
                self.channel_C_buffer=(ctypes.c_short * bufferlength)()
                #self.streaming_buffer_length = bufferlength
                res = self.lib.ps4000aSetDataBuffer(self.handle,channel,ctypes.byref(self.channel_C_buffer),self.streaming_buffer_length,segmentIndex,mode)
            if channel == PS4000_CHANNEL_D: #channel D is set
                self.channel_D_buffer=(ctypes.c_short * bufferlength)()
                #self.streaming_buffer_length = bufferlength
                res = self.lib.ps4000aSetDataBuffer(self.handle,channel,ctypes.byref(self.channel_D_buffer),self.streaming_buffer_length,segmentIndex,mode)
            if channel == PS4000_CHANNEL_E: #channel E is set
                self.channel_E_buffer=(ctypes.c_short * bufferlength)()
                #self.streaming_buffer_length = bufferlength
                res = self.lib.ps4000aSetDataBuffer(self.handle,channel,ctypes.byref(self.channel_E_buffer),self.streaming_buffer_length,segmentIndex,mode)
            if channel == PS4000_CHANNEL_F: #channel F is set
                self.channel_F_buffer=(ctypes.c_short * bufferlength)()
                #self.streaming_buffer_length = bufferlength
                res = self.lib.ps4000aSetDataBuffer(self.handle,channel,ctypes.byref(self.channel_F_buffer),self.streaming_buffer_length,segmentIndex,mode)
            if channel == PS4000_CHANNEL_G: #channel G is set
                self.channel_G_buffer=(ctypes.c_short * bufferlength)()
                #self.streaming_buffer_length = bufferlength
                res = self.lib.ps4000aSetDataBuffer(self.handle,channel,ctypes.byref(self.channel_G_buffer),self.streaming_buffer_length,segmentIndex,mode)
            if channel == PS4000_CHANNEL_H: #channel H is set
                self.channel_H_buffer=(ctypes.c_short * bufferlength)()
                #self.streaming_buffer_length = bufferlength
                res = self.lib.ps4000aSetDataBuffer(self.handle,channel,ctypes.byref(self.channel_H_buffer),self.streaming_buffer_length,segmentIndex,mode)

            if VERBOSE:
                print(' Result: '+str(res)+' (0 = PICO_OK)')
        finally:
            pass     

    def construct_buffer_callback(self):
        # Buffer callback C function template
        C_BUFFER_CALLBACK = ctypes.CFUNCTYPE(
                None,
                ctypes.c_int16,
                ctypes.c_int32,
                ctypes.c_uint32,
                ctypes.c_int16,
                ctypes.c_uint32,
                ctypes.c_int16,
                ctypes.c_int16,
                ctypes.c_void_p)
        
        # Callback function
        def get_buffer_callback(handle, noOfSamples, startIndex, overflow, triggerAt, triggered, autoStop, pParameter):
            
            if overflow:
                print(' Vertical Overflow')
            #create filename based on actual timestamp
            #filename = time.strftime("%Y%m%d_%H_%M_%S_%f.csv")
            filename=datetime.datetime.now()
            filename= filename.strftime("%Y%m%d_%H_%M_%S_%f")
            CH1='CH1_' + filename 
            #CH2='CH2_' + filename
            
            #cast 2d-pointer from c- callback into python pointer 
            #ob = ctypes.cast(overviewBuffers,ctypes.POINTER(ctypes.POINTER(ctypes.c_short)))
            if VERBOSE:
                print('------------------')
                print(' startIndex = '+str(startIndex))
                print(' Number of samples collected: '+str(noOfSamples))
                print(' Value of first sample: '+str(self.channel_A_buffer[startIndex]))
            
            #create array from pointer data ob[0]-> CH1 ob[1]-> CH2
            #streamed_data_CH1=np.fromiter(ob[0], dtype=np.short, count=nValues)
            #streamed_data_CH2=np.fromiter(ob[1], dtype=np.short, count=nValues)
                        
            #save array data into numpy fileformat
            path1 = os.path.normpath('C:\\Users\ckattmann\Documents\GitHub\pqpico\Data')+'/'+CH1
            #path2 = os.path.normpath('C:\\Users\ckattmann\Documents\GitHub\pqpico\Data')+'/'+CH2
                        
            #np.save(path1,streamed_data_CH1)
            #np.save(path2,streamed_data_CH2)
            #print('File saved:',CH1,CH2)
            
            return 0
            
        return C_BUFFER_CALLBACK(get_buffer_callback)

# Running and Retrieving Data NOTE: Bufferlength must be the same as set in set_data_buffer function
    def run_streaming(self, downSampleRatio=1, downSampleRatioMode=0):
        if VERBOSE:
            print('==== RunStreaming ====')
        sampleIntervalTimeUnit = self.streaming_sample_interval_unit
        try:
            autoStop=0
            maxPreTriggerSamples=None
            maxPostTriggerSamples=None
            res = self.lib.ps4000aRunStreaming(self.handle,
                    ctypes.byref(self.streaming_sample_interval),
                    sampleIntervalTimeUnit,
                    maxPreTriggerSamples,
                    maxPostTriggerSamples,
                    autoStop,
                    downSampleRatio,
                    downSampleRatioMode,
                    self.streaming_buffer_length)
            # DOC of ps4000aRunStreaming(handler, pointer to sampleInterval, sampleIntervalTimeUnit, maxPretriggerSamples=none, maxPosttriggerSamples=none,autostop=none,downsamplingrate=no, downsamlingratiomode=0,bufferlength= must be the same as in setbuffer)
            if VERBOSE:
                print(' Result: '+str(res)+' (0 = PICO_OK, 64 = PICO_INVALID_SAMPLERATIO)')
                print(' Streaming Sample Interval: '+str(self.streaming_sample_interval.value))
        finally:
            pass

    def get_Timebase(self, timebase=79,noSamples=1000,segmentIndex= 1):
        try:
            res=self.lib.ps4000aGetTimebase(self.handle, timebase, noSamples, ctypes.byref(self.timeIntervalNS),ctypes.byref(self.maxSamples),None)
            print('TimeInterval_Ns: '+ str(self.timeIntervalNS))
            print('maxSamples: '+str(self.maxSamples))
            print(res)
        finally:
            pass

#Actually retrieve the data on the pc
    def get_streaming_latest_values(self):
        buffer_callback = self.construct_buffer_callback()
        res = self.lib.ps4000aGetStreamingLatestValues(self.handle, buffer_callback)
        
        return res
    
    def stop_sampling(self):
        try:
            res=self.lib.ps4000aStop(self.handle)
            if VERBOSE:
                print('Stopping sampling of Scope')
                print('Result: '+str(res)+' (0= PICO_OK)')
        finally:
            pass
        return res    

# Checking Buffer Overflow
    def overview_buffer_status(self):
        streaming_buffer_overflow = ctypes.c_bool(1)
        res = self.lib.ps2000_overview_buffer_status(self.handle, ctypes.byref(streaming_buffer_overflow))
        print('Overflow Error: ',str(res))
        return streaming_buffer_overflow.value
    def getPicoStatusString(self, errorcode):
        pass



if __name__ == '__main__':

    pico = Picoscope4000()
    try:
        #Set up Picoscope for continuous streaming
        pico.set_channel()
        #pico.get_Timebase()
        pico.set_data_buffer()
        pico.run_streaming()
        time.sleep(0.5)
        for step in xrange(15):
            time.sleep(0.5)
            pico.get_streaming_latest_values()
        time.sleep(0.5)
        pico.stop_sampling()
    finally:      
        pico.close_unit()
