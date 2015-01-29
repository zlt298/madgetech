import madgetech_2 as mt2
import csv,os
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

class CorrosionSensorProcessor():
    """
    The corrosion sensor processor object takes a madgetech_2 mt2file object as its input 
    """
    def __init__(self,useDefaultInput = True):
        def setAnalysisParameters(resistance = 1000, #Ohms
                                  wetnessThreshold=0.00005, #V
                                  m=2.0935, #unit-less
                                  A=5.8035, #unit-less
                                  CIalarm=0): #Corrosion Index Units
            self.ANALYSIS_INPUT = (resistance,wetnessThreshold,m,A,CIalarm)
        self.ANALYSIS_INPUT_SET = useDefaultInput
        
        if self.ANALYSIS_INPUT_SET:
            setAnalysisParameters()
        else:
            self.ANALYSIS_INPUT = (None,None,None,None,None)
    
    def runAnalysis(self,data , secondinterval , resistance , wetnessThreshold , m , A , CIalarm):
        """
		This Function takes madgetech data as processed by the madgetech_2 module as well as 
		certain corrosion sensor parameters and returns a tuple of lists containing datasets
		for:
		days = daycount as a float
		wetString = Time wet as a contiguous string
		wetPeaks = Time Wet listed as peaks
		wetTime = A float of the time in days wet
		dryString = Time dry as a contiguous string
		dryPeaks = Time dry listed as peaks
		dryTime =  A float of the time in days dry
		cycleCount = Number of wet-dry cycles
		chlorideEquivalence = Calculated equivalent chloride level over time
		incrementalCorrosion = Corrosion index per unit time
		cumulativeCorrosion = Total Corrosion index up to time
		"""
	try:
            from math import log10
            dayInterval = (secondinterval/float(3600*24))
            wetString = [None]*len(data)
            dryString = [None]*len(data)
            wetPeaks = []
            dryPeaks = []
            cycleCount = 0.0
            chlorideEquivalence = [0]*len(data)
            incrementalCorrosion = [0]*len(data)
            cumulativeCorrosion = [0]
            alarmDay = 0
            
            for ind,value in enumerate(data):
                if ind == 0: #If first value of dataset
                    if value > wetnessThreshold:#If voltage crosses wetness threshold
                        wetString[0],dryString[0] = dayInterval,0
                    else: #If voltage does not cross wetness threshold
                        wetString[0],dryString[0] = 0,dayInterval
                    incrementalCorrosion[0] = 0
                else: #If not the first value of dataset
                    if value > wetnessThreshold: #If voltage crosses wetness threshold
                        wetString[ind],dryString[ind] = wetString[ind-1]+dayInterval,0
                        incrementalCorrosion[ind] = (data[ind-1]+data[ind])*secondinterval / float(2*resistance)  
                    else: #If voltage does not cross wetness threshold
                        wetString[ind],dryString[ind] = 0,dryString[ind-1]+dayInterval
                        incrementalCorrosion[ind] = 0
                    
                    cumulativeCorrosion.append(cumulativeCorrosion[-1]+incrementalCorrosion[ind])
                    
                    #When dry string or wet string ends
                    if dryString[ind]==dayInterval or wetString[ind]==dayInterval:
                        cycleCount += 0.5
                        if wetString[ind]: dryPeaks.append(dryString[ind-1])
                        else: wetPeaks.append(wetString[ind-1])
                    
                    #At the end of a wetstring, or at the end of the dataset if wetness threshold is crossed
                    #calculate chloride equivalence according to the curve fitted formula
                    if (wetString[ind]==0 and wetString[ind-1]!=0) or (ind==len(data)-1 and wetString[ind]!=0):
                        try:chlorideEquivalence[ind] = 10**(m*log10(max(data[ind-int(wetString[ind-1]/dayInterval):ind]))+A)
                        except ValueError:chlorideEquivalence[ind] = 10**(m*log10(value)+A)
                        if chlorideEquivalence[ind] < 0:chlorideEquivalence[ind] = 0
                
                #Check if Corrosion Index alarm threshold has been crossed. If true, record day
                if CIalarm > cumulativeCorrosion[-1]: alarmday = (ind+1)*dayInterval
            
            #Calculate total time wet and total time dry, and generate t axis.
            wetTime = sum(x>0 for x in wetString)*dayInterval
            dryTime = len(data)*dayInterval - wetTime
            days = [x*dayInterval for x in range(0,len(data))]
        
            return days,wetString,wetPeaks,wetTime,dryString,dryPeaks,dryTime,cycleCount,chlorideEquivalence,incrementalCorrosion,cumulativeCorrosion
        except Exception as e:
            print e
            print "Analysis of Corrosion sensor failed, check input data for proper formatting."
            return False
    
    def plotAnalysis(self,site , data , days , wetString , dryString , chlorideEquivalence , incrementalCorrosion , cumulativeCorrosion):
        yy = [data, wetString , dryString , chlorideEquivalence , incrementalCorrosion , cumulativeCorrosion]
        titles = ['Raw Sensor Data','Wet String','Dry String','Chloride Equivalent Levels',
                  'Incremental Corrosion Index','Cumulative Corrosion Index']
        yaxis = ['Voltage [V]','Duration Wet [D]','Duration Dry [D]','Chloride Equivalent [ppm]',
                 'Incremental Corrosion Index','Cumulative Corrosion Index']
                 
        fig, axes = plt.subplots(nrows=6, ncols=1,figsize=(16,24),dpi = 100)
        for i, ax in enumerate(axes.flat, start=1):
            ax.tick_params(labelsize=14)
            ax.set_title(titles[i-1],fontsize = 20)
            ax.set_xlabel('Exposure Time [D]',fontsize = 16)
            ax.set_ylabel(yaxis[i-1],fontsize = 16)
            ax.set_xlim([0,days[-1]])
            ax.plot(days,yy[i-1])
            ax.yaxis.set_major_locator(MaxNLocator(5))
            if i==1:
                ax.plot([0,days[-1]],[self.ANALYSIS_INPUT[1],self.ANALYSIS_INPUT[1]],color='r',label='Wetness Threshold')
                ax.legend()
        fig.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=1.4)
        fig.suptitle(site+' CS',fontsize = 16,horizontalalignment='right',
                     verticalalignment='top',x = 1,y = 1)
        fig.tight_layout()

        #check for alternative sensors:
        fname = site+' CS Graphs.png'
        fname_counter = 2
        while os.path.isfile(fname):
            fname = site+' CS'+str(fname_counter)+' Graphs.png'
            fname_counter += 1
        
        fig.savefig(fname)
        fig.clf()
        plt.close()

        
    def csvAnalysis(self,site,days,wetString,wetPeaks,wetTime,dryString,dryPeaks,dryTime,cycleCount,chlorideEquivalence,incrementalCorrosion,cumulativeCorrosion):
        #Define functions for standard deviation and median
        from math import sqrt
        def stdev(yj):
            ymean = sum(yj)/float(len(yj))
            return sqrt(sum([(x-ymean)**2 for x in yj])/float(len(yj)))
        def median(lst):
            even = (0 if len(lst) % 2 else 1) + 1
            half = (len(lst) - 1) / 2
            return sum(sorted(lst)[half:half + even]) / float(even)
        tt,wet,wetP,wetT,dry,dryP,dryT,cyc,chl,ic,cci = days,wetString,wetPeaks,wetTime,dryString,dryPeaks,dryTime,cycleCount,chlorideEquivalence,incrementalCorrosion,cumulativeCorrosion

        #check for alternative sensors:
        fname = site+' CS analysis.csv'
        fname_counter = 2
        while os.path.isfile(fname):
            fname = site+' CS'+str(fname_counter)+' analysis.csv'
            fname_counter += 1
        
        with open(fname,'w+b') as csvfile:
            cw = csv.writer(csvfile, delimiter=',',quoting=csv.QUOTE_NONE)
            try:alarmThreshDay = str(tt[ic.index(next(i for i in ic if i >self.ANALYSIS_INPUT[4]))])
            except:alarmThreshDay = str('N/A')
            contents = [[site+' CS'],
                        ['TOW','','CORROSIVITY','','CORROSION INDEX'],
                        ['Inputs','','Inputs','','Inputs'],
                        ['Wetness Threshold (recommended: 0.00005)',str(self.ANALYSIS_INPUT[1]),'Chloride Calibration Slope (m)',str(self.ANALYSIS_INPUT[2]),'Sensor R (Ohm)',str(self.ANALYSIS_INPUT[0])],
                        ['Data Interval (min)',str(int((tt[1]-tt[0])*24*60)),'Chloride Calibration Offset (A)',str(self.ANALYSIS_INPUT[3]),'Corrosion Index Alarm Threshold',str(self.ANALYSIS_INPUT[4])],
                        [],[],['Outputs','','Outputs','','Outputs'],
                        ['','','','','Corrosion Index',str(cci[-1])],
                        ['Total Exposure Time (D)',str(tt[-1])],
                        ['','','Chloride Equivalent [ppm]','','Day Alarm Threshold Exceeded',alarmThreshDay],
                        ['Total Wetness Time (D)',str(wetT),'Min',min(chl)],
                        ['','','Average',str(sum(chl)/float(len(chl)))],
                        ['Total Dry Time (D)',str(dryT),'Max',max(chl)],
                        [],['Percent Time Wet (%)',str(wetT/float(tt[-1])*100),'SD',stdev(chl)],
                        [],['Number of Wet-Dry Cycles',str(cyc)]]
            
            if len(wetP) > 0:
                contents.extend([[],['Wet Cycle'],
                                 ['Min (D)',str(min(wetP))],
                                 ['Average (D)',str(sum(wetP)/float(len(wetP)))],
                                 ['Max (D)',str(max(wetP))],
                                 ['Median (D)',str(median(wetP))],
                                 ['SD (D)',str(stdev(wetP))],
                                 [],['Dry Cycle'],
                                 ['Min (D)',str(min(dryP))],
                                 ['Average (D)',str(sum(dryP)/float(len(dryP)))],
                                 ['Max (D)',str(max(dryP))],
                                 ['Median (D)',str(median(dryP))],
                                 ['SD (D)',str(stdev(dryP))]])
                        
            for i in contents:
                cw.writerow(i)
