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
        print(SN)
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
# Evalustes delta between the curent time and log time. Then using
# time delta (900 sec) and serial number sends proper log (which are in time margin)
# to output folder, the other ones go to Trash.

def handleFailedLogs(sn, ltime, failedbrds, logpath, trash, outpath):
    curtime = datetime.now()
    logtime = datetime.strptime(ltime, "%Y%m%d%H%M%S")
    delta = (curtime - logtime).total_seconds()
    if delta > 900:
        if sn in failedbrds.keys() and not failedbrds[sn]:
            shutil.move(logpath, outpath)
            del failedbrds[sn]
            # print(failedbrds)
        elif sn in failedbrds.keys() and failedbrds[sn]:
            shutil.move(logpath, trash)
        else:
            failedbrds[sn] = True
            shutil.move(logpath, outpath)
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
        return True
    elif os.path.exists(outpath + '\\' + logname):
        os.remove(outpath + '\\' + logname)
        return True
    else:
        return False
#--------------------------------------------------------------------------
# Iterate through the buffer directory and move logs with the 'PASS' status
# to main directory
# def moveLogs(inpath, outpath, checkStatus):
#     curtime = datetime.now()
#     failed_boards = {}
#
#
#     with os.scandir(inpath) as templogs:
#         for entry in templogs:
#             if not entry.name.startswith('.') and entry.is_file():
#                 tempfnls = entry.name.split('_')
#                 # print(tempfnls)
#                 if 'PASS' in tempfnls[-1].split('.'):
#                     shutil.move(entry.path, outpath)
#                 elif 'FAIL' in tempfnls[-1].split('.'):
#                     status = checkStatus(entry.path)
#                     if not status:
#                         shutil.move(entry.path, outpath)
#                     elif status:
#                         handleFailedLogs(entry.path, tempfnls, curtime, failed_boards, trash)
#
#         for sn in failed_boards.keys():
#             status = selectMostRecent(sn, failed_boards)
#             if status:
#                 print(failed_boards[sn])
#---------------------------------------------------------------------------
