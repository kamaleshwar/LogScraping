#!/usr/bin/python

import csv
import datetime
import os
import re
import socket
import sys
import time

HOSTNAME=socket.gethostname().upper()
ENGINE_TIME_FORMAT='%Y-%m-%d %H:%M:%S.%f'
EMAIL_FROM=''
EMAIL_TO=''

EMAIL_BODY_DELAY='Delayed <font color="maroon"><b>Start of Day:</b></font> processes summary<br><h6><font color="maroon"><b>Please do not respond to this email message. It is automatically generated.</b></font></h6><br>'
EMAIL_BODY_SUMMARY='<font color="maroon"><b>Start of Day</b></font> summary<br><br><br><h6><font color="maroon"><b>Please do not respond to this email message. It is automatically generated.</b></font></h6>'
SUMMARY_TABLE=[]
TABLE_HEADER=['Component', 'WorkGroup', 'Type', 'BusinessDate', 'StartTime', 'EndTime', 'ByUser', 'Time(in sec)', 'Time(in hh:mm:ss:ms)', 'Status']

EMAIL_BODY_END='<br><br>'+'Additional Info:<br>'
EMAIL_BODY_END=EMAIL_BODY_END+'Host Name --> '+HOSTNAME+'<br>'
EMAIL_BODY_END=EMAIL_BODY_END+'Current Server Time --> '+time.strftime('%Y-%m-%d %H:%M:%S')+'<br>'


SOD_timings_key=[]
DELAYED_SOD=[]
SOD_timings=[[]]

try:
        tempEmail=str(sys.argv[3])
        if len(tempEmail) > 0 and "@" in tempEmail:
                EMAIL_TO=tempEmail		
except IndexError:
        print ''

# Function definition is here

def createhtmlmail (html, text, subject):
        """Create a mime-message that will render HTML in popular
           MUAs, text in better ones"""
        import MimeWriter
        import mimetools
        import cStringIO
        
        out = cStringIO.StringIO() # output buffer for our message 
        htmlin = cStringIO.StringIO(html)
        txtin = cStringIO.StringIO(text)
        
        writer = MimeWriter.MimeWriter(out)
        #
        # set up some basic headers... we put subject here
        # because smtplib.sendmail expects it to be in the
        # message body
        #
        writer.addheader("Subject", subject)
        writer.addheader("MIME-Version", "1.0")
        #
        # start the multipart section of the message
        # multipart/alternative seems to work better
        # on some MUAs than multipart/mixed
        #
        writer.startmultipartbody("alternative")
        writer.flushheaders()
        #
        # the plain text section
        #
        subpart = writer.nextpart()
        subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
        pout = subpart.startbody("text/plain", [("charset", 'us-ascii')])
        mimetools.encode(txtin, pout, 'quoted-printable')
        txtin.close()
        #
        # start the html subpart of the message
        #
        subpart = writer.nextpart()
        subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
        #
        # returns us a file-ish object we can write to
        #
        pout = subpart.startbody("text/html", [("charset", 'us-ascii')])
        mimetools.encode(htmlin, pout, 'quoted-printable')
        htmlin.close()
        #
        # Now that we're done, close our writer and
        # return the message body
        #
        writer.lastpart()
        msg = out.getvalue()
        out.close()
        return msg


def html_table(headers,array):
        tableData=''
        tableData=tableData+'<table class=\"gridtable\" style=\"border:1px solid black;border-collapse:collapse;font-family:sans-serif;\"><thread><tr>'
        for element in headers:
                tableData=tableData+"<th style=\"border:1px solid black;\">"+element+" </th>"
        tableData=tableData+'</tr></thead>'
        for sublist in array:
                tableData=tableData+'  <tr><td style=\"border:1px solid black;\">'
                tableData=tableData+'    </td><td style=\"border:1px solid black;\">'.join(sublist)
                tableData=tableData+'  </td></tr>'
        tableData=tableData+'</table>'
        return tableData
        
def sendmail(to, subject, html):
        styles="<style type=\"text/css\">"
        styles=styles+"table.gridtable {        font-family: verdana,arial,sans-serif;  font-size:11px; color:#333333;  border-width: 1px;      border-color: #666666;  border-collapse: collapse;}"
        styles=styles+"table.gridtable th {     border-width: 1px;      padding: 8px;   border-style: solid;    border-color: #666666;  background-color: #dedede;}"
        styles=styles+"table.gridtable td {     border-width: 1px;      padding: 8px;   border-style: solid;    border-color: #666666;  background-color: #ffffff;}"
        styles=styles+"</style>"
        html=styles+"<div style=\"font-family: verdana,arial,sans-serif; font-size:11px;\">"+html+"</div>"
        message = createhtmlmail(html, '', subject)
        import smtplib
        server = smtplib.SMTP("")
        server.sendmail(EMAIL_FROM,to, message)
        server.quit()
        return  

def timeDiff(time1,time2): #Times in ENGINE_TIME_FORMAT
        return int(time.mktime(time.strptime(time1, ENGINE_TIME_FORMAT)))-int(time.mktime(time.strptime(time2, ENGINE_TIME_FORMAT)))

def timeDiff_Milli_Seconds(time1,time2): #Times in ENGINE_TIME_FORMAT	
        return str((datetime.datetime.strptime(time1, ENGINE_TIME_FORMAT)-datetime.datetime.strptime(time2, ENGINE_TIME_FORMAT)))

def extractDataSODstarted( txt ):
        re1='.*?'	# Non-greedy match on filler
	re2='((?:2|1)\\d{3}(?:-|\\/)(?:(?:0[1-9])|(?:1[0-2]))(?:-|\\/)(?:(?:0[1-9])|(?:[1-2][0-9])|(?:3[0-1]))(?:T|\\s)(?:(?:[0-1][0-9])|(?:2[0-3])):(?:[0-5][0-9]):(?:[0-5][0-9]))'	# Time Stamp 1
	re3='([+-]?\\d*\\.\\d+)(?![-+0-9\\.])'	# Float 1
	re4='.*?'	# Non-greedy match on filler
	re5='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re6='.*?'	# Non-greedy match on filler
	re7='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re8='.*?'	# Non-greedy match on filler
	re9='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re10='.*?'	# Non-greedy match on filler
	re11='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re12='.*?'	# Non-greedy match on filler
	re13='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re14='.*?'	# Non-greedy match on filler
	re15='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re16='.*?'	# Non-greedy match on filler
	re17='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re18='.*?'	# Non-greedy match on filler
	re19='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re20='.*?'	# Non-greedy match on filler
	re21='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re22='.*?'	# Non-greedy match on filler
	re23='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re24='.*?'	# Non-greedy match on filler
	re25='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re26='.*?'	# Non-greedy match on filler
	re27='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re28='.*?'	# Non-greedy match on filler
	re29='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re30='.*?'	# Non-greedy match on filler
	re31='((?:[a-z][a-z0-9_]*))'	# Variable Name 1
	re32='.*?'	# Non-greedy match on filler
	re33='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re34='.*?'	# Non-greedy match on filler
	re35='((?:[a-z][a-z0-9_]*))'	# Variable Name 2
	re36='.*?'	# Non-greedy match on filler
	re37='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re38='.*?'	# Non-greedy match on filler
	re39='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re40='.*?'	# Non-greedy match on filler
	re41='((?:[a-z][a-z0-9_]*))'	# Variable Name 3
	re42='.*?'	# Non-greedy match on filler
	re43='((?:(?:[1]{1}\\d{1}\\d{1}\\d{1})|(?:[2]{1}\\d{3}))[-:\\/.](?:[0]?[1-9]|[1][012])[-:\\/.](?:(?:[0-2]?\\d{1})|(?:[3][01]{1})))(?![\\d])'	# YYYYMMDD 1
	re44='.*?'	# Non-greedy match on filler
	re45='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re46='.*?'	# Non-greedy match on filler
	re47='((?:[a-z][a-z0-9_]*))'	# Variable Name 4

	rg = re.compile(re1+re2+re3+re4+re5+re6+re7+re8+re9+re10+re11+re12+re13+re14+re15+re16+re17+re18+re19+re20+re21+re22+re23+re24+re25+re26+re27+re28+re29+re30+re31+re32+re33+re34+re35+re36+re37+re38+re39+re40+re41+re42+re43+re44+re45+re46+re47,re.IGNORECASE|re.DOTALL)
	m = rg.search(txt)
	if m:
		timestamp1=m.group(1)
		float1=m.group(2)
		var1=m.group(3)
		var2=m.group(4)
		var3=m.group(5)
		yyyymmdd1=m.group(6)
		var4=m.group(7)
                timestamp1=timestamp1+float1

                var2=var2.replace(' and context','')
                var2=var2.replace(' ','')
                
                key=var1+"_"+var2+"_"+var3+"_"+yyyymmdd1
                if key in SOD_timings_key:
                        keys = [item for item in range(len(SOD_timings_key)) if SOD_timings_key[item] == var1+"_"+var2+"_"+var3+"_"+yyyymmdd1]
                        keys[0]=keys[len(keys)-1]
                        if timeDiff(timestamp1,SOD_timings[keys[0]][4]) >= 0:
                                SOD_timings[keys[0]][4]=timestamp1
                                SOD_timings[keys[0]][6]=var4
                else:
                        SOD_timings_key.append(key)
                        if len(SOD_timings_key)>1:
                                SOD_timings.append([])
                        SOD_timings[len(SOD_timings)-1].append(var1)            #component
                        SOD_timings[len(SOD_timings)-1].append(var2)            #workGroup
                        SOD_timings[len(SOD_timings)-1].append(var3)            #type
                        SOD_timings[len(SOD_timings)-1].append(yyyymmdd1)       #businessDate
                        SOD_timings[len(SOD_timings)-1].append(timestamp1)      #startTime
                        SOD_timings[len(SOD_timings)-1].append(0)                       #endTime
                        SOD_timings[len(SOD_timings)-1].append(var4)            #user
        return

def extractDataSODfinished( txt , status ):
        re1='.*?'	# Non-greedy match on filler
	re2='((?:2|1)\\d{3}(?:-|\\/)(?:(?:0[1-9])|(?:1[0-2]))(?:-|\\/)(?:(?:0[1-9])|(?:[1-2][0-9])|(?:3[0-1]))(?:T|\\s)(?:(?:[0-1][0-9])|(?:2[0-3])):(?:[0-5][0-9]):(?:[0-5][0-9]))'	# Time Stamp 1
	re3='([+-]?\\d*\\.\\d+)(?![-+0-9\\.])'	# Float 1
	re4='.*?'	# Non-greedy match on filler
	re5='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re6='.*?'	# Non-greedy match on filler
	re7='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re8='.*?'	# Non-greedy match on filler
	re9='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re10='.*?'	# Non-greedy match on filler
	re11='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re12='.*?'	# Non-greedy match on filler
	re13='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re14='.*?'	# Non-greedy match on filler
	re15='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re16='.*?'	# Non-greedy match on filler
	re17='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re18='.*?'	# Non-greedy match on filler
	re19='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re20='.*?'	# Non-greedy match on filler
	re21='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re22='.*?'	# Non-greedy match on filler
	re23='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re24='.*?'	# Non-greedy match on filler
	re25='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re26='.*?'	# Non-greedy match on filler
	re27='((?:[a-z][a-z0-9_]*))'	# Variable Name 1
	re28='.*?'	# Non-greedy match on filler
	re29='.*?,'	# Uninteresting: csv
	re30='.*?'	# Non-greedy match on filler
	re31='(.*?),'	# Command Seperated Values 1
	re32='.*?'	# Non-greedy match on filler
	re33='(?:[a-z][a-z0-9_]*)'	# Uninteresting: var
	re34='.*?'	# Non-greedy match on filler
	re35='((?:[a-z][a-z0-9_]*))'	# Variable Name 2
	re36='.*?'	# Non-greedy match on filler
	re37='((?:(?:[1]{1}\\d{1}\\d{1}\\d{1})|(?:[2]{1}\\d{3}))[-:\\/.](?:[0]?[1-9]|[1][012])[-:\\/.](?:(?:[0-2]?\\d{1})|(?:[3][01]{1})))(?![\\d])'	# YYYYMMDD 1

	rg = re.compile(re1+re2+re3+re4+re5+re6+re7+re8+re9+re10+re11+re12+re13+re14+re15+re16+re17+re18+re19+re20+re21+re22+re23+re24+re25+re26+re27+re28+re29+re30+re31+re32+re33+re34+re35+re36+re37,re.IGNORECASE|re.DOTALL)
	m = rg.search(txt)
	if m:
		timestamp2=m.group(1)
		float2=m.group(2)
		var1=m.group(3)
		csv1=m.group(4)
		var2=m.group(5)
		yyyymmdd1=m.group(6)
		timestamp2=timestamp2+float2
                
                csv1=csv1.replace(' group ','')
                csv1=csv1.replace(' ','')
                
                keys = [item for item in range(len(SOD_timings_key)) if SOD_timings_key[item] == var1+"_"+csv1+"_"+var2+"_"+yyyymmdd1]
                if len(keys)==0:
                        keys = [item for item in range(len(SOD_timings_key)) if SOD_timings_key[item].startswith(var1+"_"+csv1+"_"+var2+"_")]
                        
                if len(keys) > 0:
                        keys[0]=keys[len(keys)-1]
                        if timeDiff(timestamp2,SOD_timings[keys[0]][4]) >= 0:
                                SOD_timings[keys[0]][5]=timestamp2
                                if len(SOD_timings[keys[0]]) < 8:
                                        SOD_timings[keys[0]].append(timeDiff(SOD_timings[keys[0]][5],SOD_timings[keys[0]][4]))
                                        SOD_timings[keys[0]].append((timeDiff_Milli_Seconds(SOD_timings[keys[0]][5],SOD_timings[keys[0]][4]))[:-3])				
                                        SOD_timings[keys[0]].append(status)
                                else:
                                        SOD_timings[keys[0]][7]=timeDiff(SOD_timings[keys[0]][5],SOD_timings[keys[0]][4])
                                        SOD_timings[keys[0]][8]=(timeDiff_Milli_Seconds(SOD_timings[keys[0]][5],SOD_timings[keys[0]][4]))[:-3]
                                        SOD_timings[keys[0]][9]=status
        return

processFile = open( str(sys.argv[1]), "r" )

for line in processFile:
        if "initiated" in line:
                extractDataSODstarted( line )
        elif "completed" in line:
                extractDataSODfinished( line , '<div style=\"background-color:rgb(7, 112, 63);color:rgb(255, 255, 255);\">COMPLETED</div>')
        elif "incomplete" in line:
                extractDataSODfinished( line , '<div style=\"background-color:rgb(128, 20, 28);color:rgb(255, 255, 255);\">INCOMPLETE</div>')

if len(SOD_timings[0])==0:
        sys.exit()

for workGroups in SOD_timings:
        if workGroups[5]==0:
                timeTaken=int(time.time())-int(time.mktime(time.strptime(workGroups[4], ENGINE_TIME_FORMAT)))		
                workGroups[5]=''
                if len(workGroups) < 8:
                        workGroups.append(timeTaken)
                        workGroups.append((timeDiff_Milli_Seconds(str((datetime.datetime.strptime(str(datetime.datetime.now()), ENGINE_TIME_FORMAT))),workGroups[4]))[:-3])
                        workGroups.append('<div style=\"background-color:rgb(250, 250, 17);color:rgb(0, 0, 0);\">IN_PROGRESS</div>')
                else:
                        workGroups[7]=int(timeTaken)
                        workGroups[8]=(timeDiff_Milli_Seconds(str((datetime.datetime.strptime(str(datetime.datetime.now()), ENGINE_TIME_FORMAT))),workGroups[4]))[:-3]
                        workGroups[9]='<div style=\"background-color:rgb(250, 250, 17);color:rgb(0, 0, 0);\">IN_PROGRESS</div>'

                if workGroups[7]>899 and workGroups[7]<10800 and workGroups[0]=='VAL':			
                        workGroups[7]=str(workGroups[7])
                        DELAYED_SOD.append(workGroups)
                        
                if workGroups[7]>1799 and workGroups[7]<10800 and workGroups[0]=='INT':			
                        workGroups[7]=str(workGroups[7])
                        DELAYED_SOD.append(workGroups)
        workGroups[7]=str(workGroups[7])
        SUMMARY_TABLE.append(workGroups)


if len(SOD_timings) > 0 :
        item_length = len(SOD_timings)
        with open('/logs/log/SOD_status_'+SOD_timings[0][0]+'.csv', 'wb') as test_file:
          file_writer = csv.writer(test_file)
          file_writer.writerow(TABLE_HEADER)
          for i in range(item_length):
                file_writer.writerow([x for x in SOD_timings[i]])
        if str(sys.argv[2])=='summary':
                if SOD_timings[0][0]=='VAL':
                        EMAIL_SUBJECT=HOSTNAME+': Margin SOD summary'
                        EMAIL_BODY_SUMMARY='Margin '+EMAIL_BODY_SUMMARY+html_table(TABLE_HEADER,SUMMARY_TABLE)
                if SOD_timings[0][0]=='INT':
                        EMAIL_SUBJECT=HOSTNAME+': Money SOD summary'
                        EMAIL_BODY_SUMMARY='Money '+EMAIL_BODY_SUMMARY+html_table(TABLE_HEADER,SUMMARY_TABLE)
                EMAIL_BODY=EMAIL_BODY_SUMMARY+EMAIL_BODY_END
                sendmail(EMAIL_TO,EMAIL_SUBJECT,EMAIL_BODY)

if len(DELAYED_SOD) > 0 and str(sys.argv[2])=='checkDelay':	
		if SOD_timings[0][0]=='VAL':
			EMAIL_SUBJECT=HOSTNAME+': Margin SOD Delayed'
		if SOD_timings[0][0]=='INT':
			EMAIL_SUBJECT=HOSTNAME+': Money SOD Delayed'
		EMAIL_BODY=EMAIL_BODY_DELAY+html_table(TABLE_HEADER,DELAYED_SOD)+EMAIL_BODY_END
		sendmail(EMAIL_TO,EMAIL_SUBJECT,EMAIL_BODY)
		
