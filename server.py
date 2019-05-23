#!/usr/bin/python3
#coding=utf-8

from socket import *
import re
import os
import signal
import time
import pymysql
import sys

DICT_TEXT='dict.txt'
HOST='127.0.0.1'
PORT=8000
ADDR=(HOST,PORT)

#并发接受链接
def main():
    #生成数据库对象
    db=pymysql.connect('127.0.0.1','root','123456','dict')
    s=socket(AF_INET,SOCK_STREAM)
    #套接字被关闭后，端口可以重用
    s.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
    s.bind(ADDR)
    s.listen(5)
    #防止僵尸进程，父进程不用等待处理子进程后再退出
    signal.signal(signal.SIGCHLD,signal.SIG_IGN)
    
    while True:
        try:
            c,addr=s.accept()
            print('Connect from ',addr)
        except KeyboardInterrupt:
            # raise
            #键盘断开连接
            os._exit(0)
        except:
            continue

        pid=os.fork()
        if pid<0:
            print('pid create error')
            c.close()
        elif pid==0:
            #关闭子进程的s套接字
            s.close()
            #mysql具有原子性,相互之间的操作不受影响
            #操作连接套接字实现的通信
            do_child(c,db)
        else:
            #主进程关闭连接套接字，就不接收连接请求
            c.close()
            continue

    db.close()
    s.close()
    os._exit(0)

#执行子进程具体任务
def do_child(c,db):
    while True:
        data=c.recv(128).decode()
        print('Request:',data)
        if data[0]=='R':
            do_register(c,db,data)
            continue
        elif data[0]=='E':
            #这边考虑的是一主一从，客户端退出，子进程也结束了
            c.close()
            sys.exit(0)
            #这里只是退出了当前子进程，退出后继续执行主进程的循环，等待客户端的连接
        elif data[0]=='L':
            do_login(c,db,data)
        elif data[0]=='Q':
            do_query(c,db,data)
        elif data[0]=='H':
            do_history(c,db,data)

#用户注册
def do_register(c,db,data):
    print('执行用户注册')
    l=data.split(' ')
    name=l[1]
    passwd=l[2]
    cur=db.cursor()
    sql="select * from user where name ='%s'"%name
    cur.execute(sql)
    r=cur.fetchone() #获取查找到的一条记录
    if r!=None:
        print('用户存在')
        c.send('EXISTS'.encode())
        return
    sql="insert into user values('%s','%s')"%(name,passwd)
    try:
        cur.execute(sql)
        db.commit()
        c.send('OK'.encode())
    except:
        c.send('FAIL'.encode())
        #回滚，将数据返回到sql语句执行前的状态
        db.rollback()
        return
    else:
        print('注册成功')

#断开链接结束子进程
def do_quit():
    pass

#用户登录
def do_login(c,db,data):
    print('登录操作')
    cur=db.cursor()
    l=data.split(' ')
    name=l[1]
    passwd=l[2]
    sql="select * from user where name='%s' and passwd='%s'"%(name,passwd)
    try:
        cur.execute(sql)
        db.commit()
        r=cur.fetchone()
    except:
        pass
    if r!=None:
        c.send('OK'.encode())
    else:
        c.send('FAIL'.encode())
    return

#查词
def do_query(c,db,data):
    print('查询操作')
    l=data.split(' ')
    print(l)
    name=l[1]
    word=l[2]
    try:
        f=open(DICT_TEXT,'rb')
        c.send('OK'.encode())
    except:
        c.send('FAIL'.encode())
        return
    for line in f:
        #line=f.readline().decode()
        #w=line.split(' ')[0]
        w=line.decode().split(' ')[0]
        # print(w)
        if word==w:
            print(line)
            #读取出来已经是字节串了
            #字典中每个单词是一行，这个结果本来就不需要词义分离
            c.send(line)
            time.sleep(0.1)
            #查词成功插入到历史记录
            insert_history(db,name,word)
            time.sleep(0.1)
            break        
    else:
        c.send('not found'.encode())
    f.close()        
    return

def insert_history(db,name,word):
    print('插入历史记录')
    cur=db.cursor()
    #获取当前时间
    ti=time.ctime()
    sql="insert into hist values('%s','%s','%s')"%(name,ti,word)
    try:
        cur.execute(sql)
        db.commit()
    except:
        #插入不成功进行回滚
        db.rollback()
        return
    print('插入成功')
    cur.close()
    db.close()

#查看历史记录
def do_history(c,db,data):
    print('查看历史记录')
    l=data.split(' ')
    name=l[1]
    cur=db.cursor()
    sql="select * from hist where name='%s'"%name
    try:
        cur.execute(sql)
        global r
        r=cur.fetchall()
        if r!=None:
            c.send('OK'.encode())  
        else:
            c.send('FAIL'.encode())
            return
    except:
        pass
    for i in r:
        #防止粘包的话可以添加一些延时
        time.sleep(0.1)
        msg='%s %s %s'%(i[0],i[1],i[2])
        c.send(msg.encode())
    time.sleep(0.1)
    c.send('##'.encode())  


if __name__=='__main__':
    main()
