import madgetech_2 as mt2
import csv,os
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

class TOWprocessor():
    """
    The TOW sensor processor object takes a madgetech_2 mt2file object as its input 
    """
    def __init__(self):
        pass        
    
    def createBuckets(self,min_,max_,bucketCount):
        """divides the FSR (max-min) into bucketCount buckets. Values in returned list are upper bounds of the buckets"""
        try:
            R = max_-min_
            buckets = [min_+(R*x)/float(bucketCount) for x in range(1,bucketCount+1)]
            return buckets
        except Exception as e:
            print e
            print 'The values entered do not yield a valid set of buckets.'
            return False

    def checkBucket(self,value,buckets):
        """returns index of the bucket which 'value' falls into. If value is out of range, returns False"""
        for ind,uBound in enumerate(buckets):
            if value < uBound: return ind
        return False

    def runAnalysis(self, data , secondinterval, bucketCount):
        """
        Takes TOW data that has been cropped to the date interval of interest, secondinterval in float and bucketCount as an integer.

        Returns final data count
        """
        try:
            dayInterval = (secondinterval/float(3600*24))
            min_,max_ = min(data),max(data)

            #Truncate data if threshold of 27.5mV or -2.5mV is crossed
            while max_ > 27.5 or min_ < -2.5:
                print 'Data truncated at out of bounds'
                mid = int(len(data)/2)
                ind = data.index(max_ if max_ > 27.5 else min_)
                if ind > mid:
                    data = data[:ind]
                else:
                    data = data[ind + 1:]
                min_,max_ = min(data),max(data)
                
                
            count = len(data)
            bucketBounds = self.createBuckets(min_,max_,bucketCount)
            buckets = [0 for _ in xrange(bucketCount)]
            

            #Bucket Quartiles are divided such that the first and last bucket both have round(bucketCount / 4) buckets. eg:
            #For 11 buckets : Q1 = [0,1,2], Q23 = [3,4,5,6,7], Q4 = [8,9,10]
            #For 12 buckets : Q1 = [0,1,2], Q23 = [3,4,5,6,7,8], Q4 = [9,10,11]
            #For 13 buckets : Q1 = [0,1,2], Q23 = [3,4,5,6,7,8,9], Q4 = [10,11,12]
            #For 14 buckets : Q1 = [0,1,2,3], Q23 = [4,5,6,7,8,9], Q4 = [10,11,12,13]
            Q1Ind = range(int(round(bucketCount / 4.0)))
            Q4Ind = range(bucketCount-int(round(bucketCount / 4.0)),bucketCount)
            Q23Ind = range(Q1Ind[-1]+1,Q4Ind[0])

            Q = dict([('Q1',0),('Q23',0),('Q4',0)])

            Q4increment = [0 for _ in data]
            Q4time = [0 for _ in data]

            avg = 0
            for ind,value in enumerate(data):
                avg += value
                bucket = self.checkBucket(value,bucketBounds)
                buckets[bucket] += 1
                Q4 = 0
                if bucket in Q1Ind:
                    Q['Q1'] += 1
                elif bucket in Q23Ind:
                    Q['Q23'] += 1
                elif bucket in Q4Ind:
                    Q['Q4'] += 1
                    Q4 = dayInterval
                Q4increment[ind] = Q['Q4']/float(ind+1)
                Q4time[ind] = Q4time[ind-1]+Q4 if ind != 0 else Q4

            avg = avg/float(count)
            days = [x*dayInterval for x in range(0,len(data))]
            for key in Q.keys():Q[key] = Q[key]/float(count)
            for ind in range(len(buckets)):buckets[ind] = buckets[ind]/float(count)
            return days,count,buckets,Q,Q4increment,Q4time,min_,max_,avg
        
        except Exception as e:
            print e
            print "Analysis of TOW sensor failed, check inputs for proper formatting."
            return False

    def plotRaw(self,site , data , days):
        yy = [data]
        titles = ['Raw Sensor Data']
        yaxis = ['Voltage [mV]']
                 
        fig, axes = plt.subplots(nrows=1, ncols=1,figsize=(16,4),dpi = 100)
        for i in range(len(yy)):
            axes.tick_params(labelsize=14)
            axes.set_title(titles[i],fontsize = 20)
            axes.set_xlabel('Exposure Time [D]',fontsize = 16)
            axes.set_ylabel(yaxis[i],fontsize = 16)
            axes.set_xlim([0,days[-1]])
            axes.plot(days,yy[i])
            axes.yaxis.set_major_locator(MaxNLocator(5))

        fig.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=1.4)
        fig.suptitle(site+' TOW',fontsize = 16,horizontalalignment='right',
                     verticalalignment='top',x = 1,y = 1)
        fig.tight_layout()

        #check for alternative sensors:
        fname = site+' TOW Raw.png'
        fname_counter = 2
        while os.path.isfile(fname):
            fname = site+' TOW'+str(fname_counter)+' Raw.png'
            fname_counter += 1
        
        fig.savefig(fname)
        fig.clf()
        plt.close()
