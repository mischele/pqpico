# -*- coding: utf-8 -*-
"""
Created on Tue Oct 21 18:18:18 2014

@author: ckattmann
"""

PROFILING = 0

import Picoscope
import time, sys

                           
if __name__ == '__main__':
    
    if PROFILING:
        import cProfile
        pr=cProfile.Profile()
        pr.enable()
            
    try:
        print('Initializing Fast Streaming')
        
        pico = Picoscope.Picoscope()
        pico.set_channel()
        pico.set_trigger()
        buffer_callback = pico.construct_buffer_callback()
        
        pico.run_streaming_ns(sample_interval=2, time_units=3)
        time.sleep(0.5)
        
        starttime = time.time()
        
        while time.time()-starttime < 600:
            time.sleep(0.5)
            oflow = pico.overview_buffer_status()
            pico.get_streaming_last_values(buffer_callback)
            print('Buffer Overflow : '+str(oflow))
    finally:
        pico.close_unit()
        
    if PROFILING:
        pr.disable()
        sys.stdout = open('profile.txt','w')
        pr.print_stats(sort='cumtime')