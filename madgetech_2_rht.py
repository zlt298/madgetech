import madgetech_2 as mt2
import csv,os
import time
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

class rhtProcessor():
    """
    RHT sensor from a madgetech 2.0.x .csv file. 
    """
    
    def __init__(self):
        pass
		
    def envelope_plot(self,x, y, winsize, ax=None, fill='gray', color='blue'):
        if ax is None:
                ax = plt.gca()
        # Coarsely chunk the data, discarding the last window if it's not evenly
        # divisible. (Fast and memory-efficient)
        numwin = x.size // winsize
        ywin = y[:winsize * numwin].reshape(-1, winsize)
        xwin = x[:winsize * numwin].reshape(-1, winsize)
        # Find the min, max, and mean within each window 
        ymin = ywin.min(axis=1)
        ymax = ywin.max(axis=1)
        ymean = ywin.mean(axis=1)
        xmean = xwin.mean(axis=1)

        fill_artist = ax.fill_between(xmean, ymin, ymax, color=fill, 
                                                                  edgecolor='none', alpha=0.5)
        line, = ax.plot(xmean, ymean, color=color, linestyle='-')
        return fill_artist, line
	    
    def format_dat(self,rawdata,secondInterval,columns = True):
        temp = [[] for _ in range(len(rawdata[0]))]
        for ind,line in enumerate(rawdata):
            temp[0].append(ind*secondInterval/float(3600*24))
            for col in range(1,len(line)):
                temp[col].append(float(line[col]))
        if columns:
            return temp
        else:
            return zip(columns)

    def cut_bounds(self, data):
        def tellme(s):
            print s
            plt.title(s,fontsize=16)
            plt.draw()

        plt.clf()
        plt.plot(data)
        plt.setp(plt.gca(),autoscale_on=False)
        tellme('You will select start and end bounds. Click to continue')

        plt.waitforbuttonpress()

        happy = False
        while not happy:
            pts = []
            while len(pts) < 2:
                tellme('Select 2 bounding points with mouse')
                pts = plt.ginput(2,timeout=-1)
                if len(pts) < 2:
                    tellme('Too few points, starting over')
                    time.sleep(1) # Wait a second

            plt.fill_between(x, y1, y2, alpha=0.5, facecolor='grey', interpolate=True) 
            
            tellme('Happy? Key click for yes, mouse click for no')

            happy = plt.waitforbuttonpress()

        bounds = sorted([int(i[0]) for i in pts])
        plt.clf()
        print bounds
        return data[bounds[0] if bounds[0] > .02*len(data) else 0:bounds[1] if bounds[1] < len(data)-1 else len(data)-1],bounds

