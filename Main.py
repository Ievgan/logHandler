import os
import time
import shutil
import configparser
from Funclib import boardStatusMES, checkLogName, checkLogStatus, handleFailedLogs

# Initialize variables. Read values from 'settings.cfg'
config = configparser.ConfigParser()
config.read('settings.cfg')
inpath = config['Paths']['Input path']
outpath = config['Paths']['Output path']
trash = config['Paths']['Trash path']
wait = int(config['Main']['Working delay'])
ftype = config['Main']['File type']
failedbrds = {}
# print(inpath, outpath, trash, wait, ftype, sep='\n')
# -----------------------------------------------------------------------------


while True:
    # Check if logs are present in folder. If not, sleep 30 sec
    if not os.listdir(inpath):
        print('Input directory is empty')
        time.sleep(wait)
    else:
        # If yes, iterate through the list of files
        with os.scandir(inpath) as logs:
            for entry in logs:
                # Check if the file has a proper type
                if entry.name.endswith(ftype) and entry.is_file():
                    # Retrieve serial number and test time from log's name
                    tempfnls = entry.name.split('_')
                    sn = tempfnls[-2]
                    logtime = tempfnls[2] + tempfnls[3]
                    # Check board history in MES system
                    result = boardStatusMES(sn)
                    print(result)
                    # If board has a proper status in MES then analyze log's name
                    if result == 'Board OK':
                        lognameok = checkLogName(tempfnls, entry.path, outpath, trash, failedbrds, sn)
                        # If log's name has FAIL then check board status inside log
                        if not lognameok:
                            logstatus = checkLogStatus(entry.path, outpath, trash, failedbrds, sn)
                            # If status is FAIL then invoke handler for failed boards
                            if logstatus:
                                handleFailedLogs(sn, logtime, failedbrds, entry.path, trash, outpath)
                    else:
                        shutil.move(entry.path, trash)
        time.sleep(wait)
