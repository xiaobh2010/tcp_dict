#coding=utf-8
from socket import *
import re
import os
import signal
import time
import pymysql
import sys

#发送连接请求
def main():
    if len(sys.argv)!=3:
        print('argv is error')
        return 

    HOST=sys.argv[1]
    PORT=int(sys.argv[2])
    ADDR=(HOST,PORT)
    s=socket(AF_INET,SOCK_STREAM)
    s.connect(ADDR)

    while True:
        print('''
            ============Welcome============
            --   1:注册  2:登录  3:退出    --
            ===============================
            ''')
        try:
            cmd=int(input('输入选项>>'))
        except:
            print('输入有误')
            continue
        if cmd not in [1,2,3]:
            print('请输入正确命令')
            #清空输入缓冲区缓存防止前一次的输入信息和后一次的信息粘连在一起
            sys.stdin.flush()
            continue

        if cmd==1:
            if do_register(s)==0:
                print('注册成功！')
            else:
                print('注册失败！')

        elif cmd==2:
            name=do_login(s)
            if name==-1:
                print('登录失败')
            else:
                print('登录成功')
                login(s,name)

        elif cmd==3:
            s.send('E'.encode())
            s.close()
            sys.exit(0)

#发送注册请求
def do_register(s):
    while True:
        name=input('用户名:')
        passwd=input('密码:')
        passwd1=input('确认密码:')
        if passwd!=passwd1:
            print('密码不一致')
            continue
        msg='R %s %s'%(name,passwd)
        s.send(msg.encode())
        data=s.recv(128).decode()
        if data[:2]=='OK':
            return 0
        elif data[:6]=='EXISTS':
            print('用户名已经存在')
            return -1
        elif data[:]=='FAIL':
            # print('用户名添加失败')
            return -1
        else:
            return -1

#用户退出
def do_quit():
    pass

#----------------------第二界面----------------------#
def login(s,name):
    while True:
        print('''
            ============query command============
            --   1.查词　　　 2.历史记录　　 3.退出　　　　--
            =====================================
            ''')
        try:
            cmd=int(input('输入选项>>'))
        except:
            print('输入有误')
            continue
        if cmd not in [1,2,3]:
            print('请输入正确命令')
            #清空输入缓冲区缓存防止前一次的输入信息和后一次的信息粘连在一起
            sys.stdin.flush()
            continue
        if cmd==1:
            do_query(s,name)
        elif cmd==2:
            do_histoty(s,name)
        elif cmd==3:
            #退出二级界面就可以
            break

#登录请求
def do_login(s):
    name=input('用户名:')
    passwd=input('密码:')
    msg='L %s %s'%(name,passwd)
    s.send(msg.encode())
    data=s.recv(128).decode()
    if data[:2]=='OK':
        return name
    else:
        # print('登录失败')
        return -1

#发送查词请求
def do_query(s,name):
    while True:
        time.sleep(0.1)
        word=input('单词:')
        if word=='##':
            break
        msg='Q %s %s'%(name,word)
        s.send(msg.encode())
        data=s.recv(128).decode()
        if data[:2]=='OK':
            data=s.recv(1024).decode()
            if data[:9]=='not found':
                print('没有找到这个单词')
            else:
                print(data)
        else:
            print('查词失败')

#发送查看记录请求
def do_histoty(s,name):
    msg='H %s'%name
    s.send(msg.encode())
    time.sleep(0.1)
    data=s.recv(128).decode()
    if data[:2]=='OK':
        while True:
            time.sleep(0.1)
            data=s.recv(1024).decode()
            if data=='##':
                break
            print(data)
    else:
        print('获取历史记录失败')        

#用户注销
def do_quit1():
    pass

if __name__=='__main__':
    main()


