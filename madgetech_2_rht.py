import madgetech_2 as mt2
import csv,os
import matplotlib.pyplot as plt
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

    def cut_bounds(self, data , minmax):
        min_,max_ = min(data),max(data)
        while max_ > minmax[1] or min_ < minmax[0]:
            print 'Data truncated at out of bounds'
            mid = int(len(data)/2)
            ind = data.index(max_ if max_ > minmax[1] else min_)
            if ind > mid:
                data = data[:ind]
            else:
                data = data[ind + 1:]
            min_,max_ = min(data),max(data)
        return data
