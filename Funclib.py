import os
import shutil
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta


#----------------------------------------------------------------------
# Checks board status in MES system. If board has 'FAIL' and has a rework
# or doesn't have any status - answer is 'Board OK'. We can proceed with further
# analysis. IF board has 'PASS' or 'FAIL' without rework the answer is 'Board exist'
# and 'Board NOK' accordingly.

def boardStatusMES(SN):
    repair, send, answer = [False, False, '']
    try:
        url = "http://10.72.16.235/jrwebservices/mes.asmx/"
        url += "GetBoardHistory?CustomerName=Honeywell&pstrSerialNo=" + SN + "&pSep="
        # print(SN)
        with urllib.request.urlopen(url) as content:
            # print(content.read())
            root = ET.fromstring(content.read().decode('utf-8'))
            for child in root:
                # print(child)
                temp = child.text.split(';')
                # print(temp)
                if 'ICT FP_BTM_ACP' in temp and 'Pass' in temp:
                    answer = 'Board has PASS'
                    send = True
                    break
                elif 'Repair Repair' in temp and 'Pass' in temp:
                    repair = True
                elif 'ICT FP_BTM_ACP' in temp and 'Fail' in temp:
                    if repair:
                        answer = 'Board OK'
                        send = True
                    else:
                        answer = 'Board not OK'
                        send = True
            if not send:
                answer = 'Board OK'
            return answer

    except Exception as e:
        print(e)
        # return 'Board OK'

#----------------------------------------------------------------------
# Check the board status inside the log file
def checkLogStatus(logpath, output, trash, fbdict, sn):
    status = True
    with open(logpath, 'r') as logfile:
        for line in logfile:
            if line.startswith('*'):
                status = False if 'PASS' in line.split() else True
                break
    if not status and not fbdict.get(sn, False):
        shutil.move(logpath, output)
        fbdict[sn] = True
        return status
    elif not status and fbdict[sn]:
        shutil.move(logpath, trash)
        return status
    else:
        return status
#----------------------------------------------------------------------
# Analyze log name. Move passed logs to output folder
def checkLogName(namelist, logpath, output, trash, fbdict, sn):
    if 'PASS' in namelist[-1].split('.') and not fbdict.get(sn, False):
        shutil.move(logpath, output)
        fbdict[sn] = True
        return True
    elif 'PASS' in namelist[-1].split('.') and fbdict[sn]:
        shutil.move(logpath, trash)
        return True
    else:
        return False

#----------------------------------------------------------------------
# Evaluates time delta between the curent time and log time. Then using
# time delta (900 sec) and serial number sends proper log (which are in
# time margin) to output folder, the other ones go to Trash.

def handleFailedLogs(sn, ltime, failedbrds, logpath, trash, outpath):
    curtime = datetime.now()
    logtime = datetime.strptime(ltime, "%Y%m%d%H%M%S")
    delta = (curtime - logtime).total_seconds()
    dellog = False
    if delta > 900:
        if sn in failedbrds.keys() and failedbrds[sn]:
            shutil.move(logpath, trash)
        else:
            shutil.move(logpath, outpath)
            failedbrds[sn] = True

    elif delta <= 900:
        if sn not in failedbrds.keys():
            failedbrds[sn] = False
        elif sn in failedbrds.keys() and failedbrds[sn]:
            shutil.move(logpath, trash)

    # print(failedbrds)

#----------------------------------------------------------------------
# Clear folder if folder's size is more than 10 Mb
def clearDirectory(trash, logs):
    size = os.path.getsize(trash)
    if size >= 10485760:
        for log in logs:
            logpath = os.path.join(trash, log)
            try:
                if os.path.isfile(logpath):
                    os.unlink(logpath)
                elif os.path.isdir(logpath): shutil.rmtree(logpath)
            except Exception as e:
                print(e)
        return True

# -------------------------------------------------------------------------
# Check if log file is already exist in output or trash directory
def checkFileExist(logname, outpath, trash):
    if os.path.exists(trash + '\\' + logname):
        os.remove(trash + '\\' + logname)
        return True, 'File already exist and was deleted from Trash'
    elif os.path.exists(outpath + '\\' + logname):
        os.remove(outpath + '\\' + logname)
        return True, 'File already exist and was deleted from Output'
    else:
        return False, 'OK'


#--------------------------------------------------------------------------
# Remove unneccesary logs from dictionary
def removeLogs(fbdict):
    keys_to_remove = [key for key, value in fbdict.items() if value]
    for item in keys_to_remove:
        fbdict.pop(item, None)
        print(str(item) + ' was deleted from dictionary')

#---------------------------------------------------------------------------

