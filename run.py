# -*- coding:utf-8 -*-

"""
    在pyctp2的父目录中, 执行
    python red.py pyctp2.sbin.md2 md_exec
"""

import logging
import threading

import asyncio
import json
from pydispatch import dispatcher
from autobahn.asyncio.websocket import WebSocketServerProtocol, WebSocketServerFactory

from pyctp2.common.base import INFO_PATH,DATA_PATH
from pyctp2.md import ctp_md as cm
from pyctp2.common import controller as ctl
from pyctp2.common.contract_type import CM_ALL
import ws_agent
from pyctp2.my.ports import ZSUsersC as my_ports


def make_users(mduser,contract_managers):
    controller = ctl.TController()
    mdagents = [ws_agent.WsAgent(cmng,DATA_PATH) for cmng in contract_managers]
    for mdagent in mdagents:
        controller.register_agent(mdagent)
    tt = ctl.Scheduler(160000,controller.day_finalize,24*60*60)
    users = []
    for port in mduser.ports:   #多路注册
        user = cm.MdApi.CreateMdApi('%s/%s' % (INFO_PATH,mduser.name))
        md_spi = cm.MdSpiDelegate(name=mduser.name,
                                 broker_id=mduser.broker,
                                 investor_id= mduser.investor,
                                 passwd= mduser.passwd,
                                 controller = controller,
                        )
        user.RegisterSpi(md_spi)
        controller.add_listener(md_spi)
        user.RegisterFront(port)
        #print('before init')
        user.Init()
        users.append(user)
    controller.reset()
    controller.start()
    return controller,users#,tt

def md_exec():
    '''
        当前使用版本
    '''
    logging.basicConfig(filename="%s/pyctp2_md.log" % (INFO_PATH,),level=logging.DEBUG,format='%(name)s:%(funcName)s:%(lineno)d:%(asctime)s %(levelname)s %(message)s')
    # return make_users(my_ports,[CM_ALL])
    return make_users(my_ports,[CM_ALL])

class MyServerProtocol(WebSocketServerProtocol):
    def onConnect(self, request):
        self.contract_sub =[]
        self.step=0
        print("Client connecting: {}".format(request.peer))

    def handle_event(self,tick,contract):
        """Simple event handler"""

        self.step += 1
        msg = {
            'contract':contract,
            'high':tick.bid_price,
            'low':tick.ask_price,
            'step':self.step
        }
        msg = json.dumps(msg)
        msg = msg.encode('utf8')
        if contract in self.contract_sub:
            self.sendMessage(msg)
            print (msg )
            print ("%s send" % contract)
            print (tick)
            print (tick.price)
            print (tick.bid_price)
            print (tick.ask_price)
            print (tick.bid_volume)
            print (tick.ask_volume)

    def onOpen(self):
        print("WebSocket connection open.")
        # asyncio.async(send_msg(self))
        dispatcher.connect( self.handle_event, sender=dispatcher.Any)

    def onClose(self, wasClean, code, reason):
        dispatcher.disconnect( self.handle_event, sender=dispatcher.Any)
        print("WebSocket connection closed: {}".format(reason))

    def onMessage(self, payload, isBinary):
        # self.sendMessage(payload, isBinary)
        data=str(payload.decode('utf8'))
        print (data)

        self.contract_sub.append(data)
        dispatcher.connect(self.handle_event, sender=dispatcher.Any)


def ws_exec():
    factory = WebSocketServerFactory()
    factory.protocol = MyServerProtocol

    t = threading.Thread(target=md_exec,args=())
    t.setDaemon(True)
    t.start()

    loop = asyncio.get_event_loop()
    coro = loop.create_server(factory, '127.0.0.1', 9002)
    server = loop.run_until_complete(coro)
    print("server created")

    try:
      loop.run_forever()
    except KeyboardInterrupt:
      pass
    finally:
      server.close()
      loop.close()

ws_exec()