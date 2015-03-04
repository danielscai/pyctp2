# -*- coding:utf-8 -*-

"""
    在pyctp2的父目录中, 执行
    python red.py pyctp2.sbin.md2 md_exec
"""


import logging

from ..common.base import INFO_PATH,DATA_PATH
from ..md import ctp_md as cm
from ..common import controller as ctl
from ..common.contract_type import CM_ALL, CM_ZJ
from ..md import save_agent as save_agent

from ..my.ports import ZSUsersC as my_ports

def make_users(mduser,contract_managers):
    controller = ctl.TController()
    mdagents = [save_agent.SaveAgent(cmng,DATA_PATH) for cmng in contract_managers]
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
    return make_users(my_ports,[CM_ZJ])

@asyncio.coroutine
def hello(websocket, path):
    while True:
        name = yield from websocket.recv()
        if name != "IF1509":
            print("< {}".format(name))
            greeting = "Hello {}!".format(name)
            # yield from producer(websocket,name)
            # t = threading.Thread(target=producer,args=(websocket,name))
            # t.run()
            yield from self.producer(websocket,name)
            yield from websocket.send(greeting)
            # producer(websocket,name)
            print("> {}".format(greeting))

@asyncio.coroutine
def producer(websocket,args):
    for i in range(1,10):
        greeting = "Hello {}!".format(args)
        print (i)
        yield from websocket.send(str(i))
        time.sleep(1)


start_server = websockets.serve(hello, 'localhost', 8766)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()