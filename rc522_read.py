#!/usr/bin/python
# -*- coding: UTF-8 -*-
import threading

import time
from time import ctime,sleep

import sys
from mfrc522 import SimpleMFRC522

import sqlite3

import requests
import json
import urllib

from xml.dom.minidom import parseString
import xml.dom.minidom



SERVERNAME='http://192.168.0.211:18010'

def writedb_emp(rfid):
    try:
        updatedb_sql("writedb_emp","INSERT INTO emplyee_pid (PID) VALUES ({cpid})".format(cpid=rfid))
    except:
        print("writedb_att发生异常")
        info = sys.exc_info()  
        print( info[0], ":", info[1]) 

def writedb_att(RFID):
    #insert data
    cCARDDATE=time.strftime("%Y-%m-%d", time.localtime())
    cCARDTIME=time.strftime("%H:%M", time.localtime())
    cRFID=RFID
    try:
        updatedb_sql("writedb_att","INSERT INTO attdata (PID,CARDDATE,CARDTIME,ispublish) VALUES('{RFID}','{CARDDATE}','{CARDTIME}',0)".format(RFID=cRFID,CARDDATE=cCARDDATE,CARDTIME=cCARDTIME))
        return
    except :
        print("writedb_att发生异常")
        info = sys.exc_info()  
        print( info[0], ":", info[1]) 

def search_emp(rfid):# LOCAL FIND PID
    try:        
        conn = sqlite3.connect('test.db')
        datadb=conn.cursor()
        cursor=datadb.execute("SELECT id,PID,DT from emplyee_pid where pid={cpid}".format(cpid=rfid)) 
        for row in cursor:
            print ("DT = ", row[1])
            print ("\n")
            return row[1]
        datadb.close()
        conn.close()
    except:
        print("searchdb发生异常",Exception)  
        conn.rollback()
    finally:
        datadb.close()
        conn.close()
         
def updatedb_sql(funname,sql):
    try:
        if (funname=="writedb_att"):
            conn = sqlite3.connect('attdata.db')
        elif (funname=="writedb_emp"):
            conn = sqlite3.connect('emp.db')
        else:
            conn = sqlite3.connect('attleave.db')
        #print ("Opened database successfully")
        datadb=conn.cursor()
        done = False
        while not done:
            try:
                datadb.execute(sql)
                done = True
            except Exception as err:
                print("updatedb_sql Message:" , err)
                conn.rollback()
                time.sleep(0.1)

        done = False
        sk = 0
        while not done:
            try:
                conn.commit()
                done = True
            except Exception as err:
                sk = sk+1
                print("errconn_comit Message:" , sk)
                conn.rollback()
        
        
        #newdf=pd.read_sql(sql,con=conn)
        #conn_tosql(conn,datadb,sql) #newdf为需要保存的dataframe值
        #conn_comit(conn)
        datadb.close()
        conn.close()
        return
    except:
        print("updatedb_sql发生异常")
        info = sys.exc_info()  
        print( info[0], ":", info[1]) 
        conn.rollback()
    finally:
        conn.close()
        
def att_to_attleave():
    try:
        #conn = sqlite3.connect('test.db')
        #datadb=conn.cursor()
        #("SELECT id,PID, carddate,cardtime,ispublish from attcarddata where ispublish!=1",conn)
        #new_db = sqlite3.connect(':memory:') # create a memory database
        attleave_db = sqlite3.connect('attleave.db')
        cur=attleave_db.cursor()
        print(time.time())
        cur.execute("attach database 'attdata.db' as att")
        cur.execute("insert into attdata select * from att.attdata where id not in (select id from attdata) limit 100")
        attleave_db.commit()
        print(time.time())
        #print (cur.fetchall())
        #new_db.close()
    except:
        print("att_to_attleave发生异常")
        info = sys.exc_info()  
        print( info[0], ":", info[1]) 
        attleave_db.rollback()
    finally:
        attleave_db.close()
    
    
def Restful_post_att_leave():
    while True:
        sleep(5)
        print("Restful_post_att_leave")
        try:
            result=True
            conn = sqlite3.connect('attleave.db')
            for row in conn.execute("SELECT PID, carddate,cardtime,id from attdata where ispublish!=1"):
                empno=restful_post_per(row[0])
                YYMMDD=row[1]
                cardtime=row[2]
                CardTxt=str(row[3])
                ReMark=str(row[3])+'leave'
                print(row[3])
                result=restful_post_attdata("",empno,YYMMDD,cardtime,CardTxt,ReMark)#RFID not send flag leaveatt
                if result==False:
                    conn.close()
                    break
            if result==False:
                break
            print("updatedb_sql")
            updatedb_sql("Restful_post_att_leave","update attdata set ispublish=1 where ispublish!=1")    #update flag
            att_to_attleave()#read linddown 10 tiao
        except:
            print("Restful_post_att_leave发生异常")
            info = sys.exc_info()  
            print( info[0], ":", info[1]) 
            conn.rollback()
        finally:
            #print('ss')
            conn.close()
    
def restful_get_server():
    try:
        requrl = SERVERNAME+'/RestService/GetServerDateTime'
        headers = {'Content-type': 'application/raw'}
        response = requests.get(requrl,headers=headers)
        #print(response.content.decode('utf-8'))
        #print(response.text)
        s=response.text
        

        doc=xml.dom.minidom.parseString(s)
        colls=[]
        strings=doc.getElementsByTagName('string')
        for item in strings:
            return (item.childNodes[0].data)
    except:
        return ""
        pass


def restful_post_per(rfid):      
    try:
        test_data={}
        test_data["FunID"]="RS020101"
        test_data["Language"]=1
        test_data["SqlWhere"]="module.perfield102='{pid}' and incumbency=1".format(pid=rfid)
        test_data["CheckSql"]=0
        
        #print(json.dumps({"ids": ["00007190","00007191"]}))
        #str_word2 = 'hell0, word！{b}'.format(b=['eee', 'd'])
        #print(test_data)
        #print(json.dumps(test_data))
        json_test_data=json.dumps(test_data)
        #print(json_test_data)
        #requrl = 'http://192.168.0.211:18010/RestService/Search'
        requrl = SERVERNAME+'/RestService/Search'
        headers = {'Content-type': 'application/raw'}
        response = requests.post(requrl, data=json_test_data, headers=headers)
        str_data=json.loads(response.text)
        #print(str_data)
        #{"Data":"[{\"RowID\":1,\"ID\":190103130451000001,\"BillNo\
        #print(str_data['Success'])
        #if (str_data['Success']==True):

        if (str_data['Data']!="[]"):
            dict_data=json.loads(str_data['Data'][1:-1])
            return dict_data['EmpID']
        else:
            return ""
       
        #print(dict_data)
        #print(dict_data['EmpID'])
        #print(response.status_code)
        #print(response.text);
        #req = urllib.request.Request(url = requrl,data =json_test_data)
        #res_data = urllib.request.urlopen(req)
        #res = res_data.read()
        #print ("Search():" + res)
    #except print ("Search():" + res):
    except urllib.request.HTTPError:
        print ("there is an error")
        pass
    
def restful_post_attdata(rfid,empno,YYMMDD,cardtime,CardTxt,ReMark):      
    try:
        test_data={}
        test_data["FunID"]="KQ052001"
        test_data["Language"]=1
        
        if rfid!="":
            empno=restful_post_per(rfid)
            YYMMDD=time.strftime("%Y-%m-%d", time.localtime())
            cardtime=time.strftime("%H:%M", time.localtime())
            CardTxt=str(time.time())
            ReMark='Realtime'
        
        dict_data={}
        dict_data["EmpNo"]=empno
        dict_data["YYMMDD"]=YYMMDD
        dict_data["cardtime"]=cardtime
        dict_data["CardTxt"]=CardTxt
        dict_data["ReMark"]=ReMark    
       
        test_data["Data"]=dict_data
        json_test_data=json.dumps(test_data)

        requrl = SERVERNAME+'/RestService/SaveOrUpdate'
        headers = {'Content-type': 'application/raw'}
        response = requests.post(requrl, data=json_test_data, headers=headers)
        #print(response.content.decode('utf-8'))
        dict_data=json.loads(response.text)
        return (dict_data['Success'])
        
    except urllib.request.HTTPError:
        print ("there is an error")
        pass


def real_read_rfid():
    reader = SimpleMFRC522()
    try:
        while True:
            print("Hold a tag near the reader")
            id, text = reader.read()
            print("ID: %s\nText: %s" % (id,text))
            #readdb()
            if id!="":
                #gpio_out_led(3)
                writedb_att(id)
                if (restful_get_server()!=""):#server connect?     
                    if (restful_post_per(id)!=""):   #id exists
                        restful_post_attdata(id,"","","","","")       #POST ATTDATA
                        writedb_emp(id)              #local db write emp
                        #output signal OK
                    else:
                        #output signal NO
                        print("id %s no exits"%(id))
                else:
                    if (search_emp(id)!=""):
                        print("local db exists id")
                        #output signal OK
                    else:
                        print("local db not exists id")
                        #output signal NO
                sleep(0.5)
                id=""
    except KeyboardInterrupt:
        raise
        

threads=[]
t1=threading.Thread(target=Restful_post_att_leave,args=())
threads.append(t1)
t2=threading.Thread(target=real_read_rfid,args=())
threads.append(t2)

if __name__ =='__main__':
    
    #Restful_post_att_leave()
    for t in threads:
        t.setDaemon(True)
        t.start()
    print('over')






