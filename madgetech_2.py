import os,sys,csv,datetime
#This code is for manipulation of Madgetech 2.0.x files and file-folders

def timeserial2datetime(serial):
    """
    Converts a dateserial in the excel and madgetech format to a python datetime.datetime object
    """
    days = int(serial)
    frac = serial - days
    seconds = int(round(frac * 86400.0))
    assert 0 <= seconds <= 86400
    if seconds == 86400:
        seconds = 0
        days += 1
    if days == 0:
        # second = seconds % 60; minutes = seconds // 60
        minutes, second = divmod(seconds, 60)
        # minute = minutes % 60; hour    = minutes // 60
        hour, minute = divmod(minutes, 60)
        return datetime.time(hour, minute, second)
        
    if days < 61 and datemode == 0:
        raise serialAmbiguous(serial)

    return (
        datetime.datetime.fromordinal(days + 693594)
        + datetime.timedelta(seconds=seconds)
        )

class mt2file:
    """
    The mt2Dat object is for easy manipulation of madgetech 2.0.x data files in the
    '.csv' format. 
    filePath is the string of the file path to the desired madgetech .csv file
    if loadData is set to True, the mt2Dat object will hold the data in memory under 'data'
    otherwise, only metadata will be loaded.
    
    If the reading interval is in Hertz, the date serial is unable to capture the interval properly
    The data will still load but an error will be raised.
    """
    def __init__(self,filePath,loadData = False):
        self.valid = True
        self.filePath = filePath
        self.fileName = None
        
        #madgetech metadata
        self.serial = None
        self.device = None
        self.startdate = None
        self.enddate = None
        self.timeinterval = None
        self.readings = None
        self.timezonedelta = None
        self.channelcount = None
        self.channels = []
        self.channelunits = []
        
        #data and related variables,data is not a dictionary because channel names are not unique
        self.data = []
        self.missingdata = []
        

        #attempt to load the file from filePath, rough check to see if it is a madgetech data file
        #save all meta data into a dictionary for later use, stop collecting at the [Display] section
        try:
            if os.path.isfile(filePath):
                self.fileName = filePath.split('\\')[-1]
                with open(filePath,'rb') as file_:
                    csvread = csv.reader(file_,delimiter = ',')
                    firstLine,collectMeta = True,True
                    metaDict = {}
                    for line in csvread:
                        if firstLine:
                            if not '%DATA MadgeTech Data File' in line[0]:
                                raise Exception('Input file is not a Madgetech data File')
                            firstLine = False
                        elif collectMeta:
                            if len(line)==2 and collectMeta:
                                metaDict[line[0]] = line[1]
                            elif '[Display]' in line:
                                collectMeta = False
            else:
                raise Exception('Input file path is invalid')
        except Exception as e:
            self.valid = False
            print e
            print filePath + ' Does not lead to a valid madgetech 2.0.x data file.'

        #Convert metaDict into object variables
        if self.valid:
            try:
                self.serial = metaDict['SerialNumber']
                self.device = metaDict['DeviceName']
                
                self.startdate = timeserial2datetime(float(metaDict['StartDate']))
                self.enddate = timeserial2datetime(float(metaDict['EndDate']))
                
                #Madgetech uses a custom string for the reading rate in the form 'RxY' where x is an integer and
                #Y can be H,M,S,Z representing Hours, Minutes, Seconds and Hertz, respectively.
                secondMultiplier = {'H':lambda x:3600*x,'M':lambda x:60*x,'S':lambda x:x,'Z':lambda x:1/float(x)}[metaDict['ReadingRate'][-1]]
                self.timeinterval = datetime.timedelta(seconds = secondMultiplier(int(metaDict['ReadingRate'][1:-1])))
                
                self.readings = int(metaDict['Readings'])
                
                #Time zones are formatted as 'TZUTC-100000|STANDARD|HST'
                timezonestring = metaDict['TimeZone'].split('|')[0].split('UTC')[1]
                timezonesign = 1 if timezonestring[0] == '+' else -1
                self.timezonedelta = datetime.timedelta(
                    hours = timezonesign*int(timezonestring[1:3]),
                    minutes = timezonesign*int(timezonestring[3:5]),
                    seconds = timezonesign*int(timezonestring[5:]))
                
                self.channelcount = int(metaDict['Channels'])
                for channel in ['('+str(i)+')' for i in range(self.channelcount)]:
                    self.channels.append(metaDict['UnitType'+channel])
                    self.channelunits.append(metaDict['Unit'+channel])
            except Exception as e:
                print e
                self.valid = False
                print 'Error while parsing metadata. Check file for corrupted data header.'
            
        #Try and load data if the loadData flag is up. While parsing data, double check metadata
        if self.valid and loadData:
            self.loaddata()
	
    def loaddata(self):
        """
            If the data has not already been loaded,running this code will load the data
        
            This allows for easy sorting and ordering with only the metadata loaded, then
            processing with the full data to save on memory.
        """
        if self.valid:
            channelindex = [2]#data sets always start with ID,datetime,channel0,...
            for _ in self.channels:
                self.data.append([])
            
            checkstartdate = False
            checkenddate = None
            checktimeinterval = False
            checkreadings = 0
            
            try:
                with open(self.filePath,'rb') as file_:
                    csvread = csv.reader(file_,delimiter = ',')
                    started,firstLine = False,True
                    for line in csvread:
                        if '[End Reading]' in line: break
                        if started:
                            if firstLine:
                                #find the remaining channel indexes
                                firstLine = False
                                while len(channelindex) != self.channelcount:
                                    #To understand this line, perform the ritual sacrifice for summoning Haarthrax The All-knowing
                                    channelindex.append(min([line[channelindex[-1]+1:].index(cell)+channelindex[-1]+1 for cell in line[channelindex[-1]+1:] 
                                        if not ('Status' in cell or 'Annotation' in cell)]))
                            else: #Parse actual data
                                dt = timeserial2datetime(float(line[1]))
                                if not checkstartdate:
                                    checkstartdate = dt
                                else:
                                    if not checktimeinterval:
                                        checktimeinterval = dt - checkenddate
                                    else:
                                        #check if time interval between readings is correct, if not commit segment to self.missingdata
                                        if dt != checkenddate + checktimeinterval:
                                            self.missingdata.append((checkenddate,dt))
                                for ind,val in enumerate(channelindex):
                                    self.data[ind].append(line[val])
                                checkenddate = dt
                                checkreadings += 1
                        else:
                            if '[Reading]' in line:
                                started = True
                #check values against metadata
                if checkstartdate != self.startdate: raise Exception('Discrepency between start date in data and in metadata')
                if checkenddate != self.enddate: raise Exception('Discrepency between end date in data and in metadata')
                if checktimeinterval != self.timeinterval and self.readings > 1: raise Exception('Discrepency between time interval in data and in metadata')
                if checkreadings != self.readings: raise Exception('Discrepency between readings in data and in metadata')
                
            except Exception as e:
                self.valid = False
                print e
                print 'Error while loading data'
                
    def printVals(self):
        print self.valid
        print self.filePath
        print self.fileName
        print self.serial
        print self.device
        print self.startdate
        print self.enddate
        print self.timeinterval
        print self.readings
        print self.timezonedelta
        print self.channelcount
        print self.channels
        print self.channelunits
    
    def getData(self,useLocalTime = False):
        """
        returns a list of tuples containing the datestring and each channel in the order listed in self.channels
        
        if the useLocalTime flag is true, the timezonedelta will be applied to the resulting datestrings
        Datestrings are in the format 'YYYY/MM/DD hh:mm:ss'
        """
        result = []
        dt = self.startdate + useLocalTime*self.timezonedelta
        for ind in range(self.readings):
            row = [dt.strftime('%Y/%m/%d %H:%M:%S')]
            for channel in range(self.channelcount):
                row.append(self.data[channel][ind])
            result.append(tuple(row))
            dt = dt + self.timeinterval
        return result
    
        
def mt2folder(folderPath,loadData = False):
    """
        Returns a list of mt2Dat objects from all valid .csv sorted by startdate
    """
    results = []
    namelist = []
    for root, dirs, files in os.walk(folderPath):
        namelist.extend([folderPath+r'\\'+file_ for file_ in files if file_.split('.')[1] == 'csv'])
    for name in namelist:
        mt = mt2file(name,loadData)
        if mt.valid:
            results.append(mt)
        else:
            print mt.fileName + '\n'
    return sorted(results,key = lambda x: x.startdate)
