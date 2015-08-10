#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    MoyTalker: A XMPP client written using python.
        By: Moycat
    Thanks to SleekXMPP, a great open source library.
"""
"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file LICENSE for copying permission.
"""

import sys
import logging
import getpass
import time
import re
import threading
from optparse import OptionParser

import sleekxmpp

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input

newMsgCount = 0
newMsg = []
connected = 0

def listen():
    global newMsgCount
    global newMsg
    global connected
    while not connected:
        time.sleep(1)
    print('\nYou have logged in successfully.')
    while 1:
        print("=================")
        print("Now you have", newMsgCount, "received massages.")
        print("1:Refresh\n2:Show all messages\n3.Show the latest message\n4.Reply a message\n5.Reply the latest message\n6.Send a message\n7.Log out")
        op = input("Please type a number above:")
        if op:
            op = int(op)
        print("=================")
        if op == 2:
            if newMsgCount == 0:
                print("No received message!")
            else:
                count = 0
                for nowMsg in newMsg:
                    print("\n[Message No.%s]\nFrom: %s\nBody:\n%s" % (count, nowMsg['from'], nowMsg['body']))
                    count += 1
        elif op == 3:
            if newMsgCount == 0:
                print("No received message!")
            else:
                tmpMsg = newMsg[newMsgCount - 1]
                print("\n[Message No.%s]\nFrom: %s\nBody:\n%s" % (newMsgCount - 1, tmpMsg['from'], tmpMsg['body']))
        elif op == 4:
            if newMsgCount == 0:
                print("No received message!")
            else:
                toNum = int(input("Which message do you want to reply? Type the number of it: "))
                if toNum < 0 or toNum >= newMsgCount:
                    print("Wrong number!")
                else:
                    tmpMsg = newMsg[toNum]
                    print("[Message No.%s]\nFrom: %s\nBody:\n%s\n" % (toNum, tmpMsg['from'], tmpMsg['body']))
                    fom = str(tmpMsg['from'])
                    to = fom.split('/', 1)[0]
                    content = input("Your reply: ")
                    if content:
                        xmpp.send_message(mto=to, mbody=content, mtype='chat')
                        print("Seccessful!")
                    else:
                        print("No input!")
        elif op == 5:
            if newMsgCount == 0:
                print("No received message!")
            else:
                toNum = newMsgCount - 1
                tmpMsg = newMsg[toNum]
                print("[Message No.%s]\nFrom: %s\nBody:\n%s\n" % (toNum, tmpMsg['from'], tmpMsg['body']))
                fom = str(tmpMsg['from'])
                to = fom.split('/', 1)[0]
                content = input("Your reply: ")
                if content:
                    xmpp.send_message(mto=to, mbody=content, mtype='chat')
                    print("Seccessful!")
                else:
                    print("No input!")
        elif op == 6:
            to = input("Who do you want to send to? Type the address: ")
            if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", to) == None:
                print("Wrong address!")
            else:
                content = input("Your message: ")
                if content:
                    xmpp.send_message(mto=to, mbody=content, mtype='chat')
                    print("Seccessful!")
                else:
                    print("No input!")
        elif op == 7:
            connected = 0
            xmpp.disconnect(wait=True)
            break
        else:
            continue
        tmp = input("\n<Press enter to continue...>")

def guard():
    global connected
    while not connected:
        time.sleep(1)
    while 1:
        if not connected:
            break
        try:
            rtt = xmpp['xep_0199'].ping(xmpp.pingjid, timeout=10)
        except IqError as e:
            logging.info("Error pinging %s: %s",
                    xmpp.pingjid,
                    e.iq['error']['condition'])
        except IqTimeout:
            logging.info("No response from %s", xmpp.pingjid)
        time.sleep(3)

class XMPPClient(sleekxmpp.ClientXMPP):

    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        pingjid = self.boundjid.bare
        self.pingjid = pingjid
        
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        
        demon = threading.Thread(target=guard, name='guard')
        demon.start()
        menu = threading.Thread(target=listen, name='listen')
        menu.start()

    def start(self, event):
        self.send_presence()
        self.get_roster()
        global connected
        connected = 1

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            global newMsgCount
            global newMsg
            newMsgCount += 1
            newMsg.append(msg)
            fom = str(msg['from'])
            print('\n{New message got! From %s}' % fom.split('/', 1)[0])


if __name__ == '__main__':
    optp = OptionParser()
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)

    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")

    opts, args = optp.parse_args()

    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        opts.jid = raw_input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")

    xmpp = XMPPClient(opts.jid, opts.password)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0004') # Data Forms
    xmpp.register_plugin('xep_0060') # PubSub
    xmpp.register_plugin('xep_0199') # XMPP Ping

    if xmpp.connect():
        xmpp.process(block=True)
        print("The End")
    else:
        print("Unable to connect.")