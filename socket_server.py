import copy
import asyncio
import numpy as np
import os
import sys
import time
import subprocess
# import atexit

from socket import *
import threading
import json
import struct
from enum import Enum
from game_demo import *
import ast
import pickle
from map_process import RoomMap
from npc_control import Npc, Agent
import datetime
from multiprocessing import Process, Queue, Value, Lock



class EnvTime(object):
    def __init__(self, speed=120, year=2025, month=3, day=12, hour=6, minute=50, second=0, end=2050):
        # Define start date. At a rate of speed(120) times
        self.start_date = datetime.datetime(year, month, day, hour, minute, second)
        # Define time multiplier
        self.time_multiplier = speed
        self.running = 1
        self.end = end
        # Simulation time
        self.current_date = self.start_date
        self.start_time = self.start_date
        # self.current_date.isoweekday()
        self.week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    def time_simulation(self, stop_event):
        while True:
            # print(stop_event.is_set())
            if not self.running or stop_event.is_set():
                break
            # print("Current Date:", self.current_date)
            # 以 10 倍速度增加时间
            time_delta = datetime.timedelta(seconds=1)  # 增加一天
            self.current_date += time_delta * self.time_multiplier
            # 控制模拟速度
            time.sleep(1)  # 每秒钟增加一天，即10倍速度
            # 可添加终止条件，比如达到某个特定日期时停止模拟
            if self.current_date.year > self.end:
                break

    def time_difference(self):
        time_diff = self.current_date - self.start_time
        hours = time_diff.total_seconds() // 3600
        # print("时间差为 %d 小时" % hours)
        return time_diff.days

    def weekday_now(self):
        return self.week[self.current_date.weekday()]

    def simulation_start(self):
        self.start_time = self.current_date


# message define
class MsgCmd(Enum):
    # 0断开连接,1服务器发送行为指令,2服务器发送状态申请,3客户端回复行为回调,4客户端回复目标状态,5给robot的指令,6关于机器人client的请求/反馈
    EXIT = 0
    Instruction = 1
    Request = 2
    Result = 3
    State = 4
    Control = 5
    Information = 6
class Server(object):
    def __init__(self):
        self.state = 1
        self.clients = []
        self.messages = []
        self.information = ''
        # 1.创建套接字
        self.sock = socket(AF_INET, SOCK_STREAM)
        # 2.准备连接服务器，建立连接
        serve_ip = 'localhost'
        serve_port = 8000  # 端口，比如8000
        # tcp_socket.connect((serve_ip,serve_port))  # 连接服务器，建立连接,参数是元组形式
        tcp_address = ('localhost', 8000)
        # 给一个检查端口机制
        self.sock.bind(tcp_address)
        MAX_CONNECTION = 100
        # 开始监听连接
        self.sock.listen(MAX_CONNECTION)
        self.headerSize = 12
        self.count = 0
        # self.robot = PRS_IK()
        # robot ik algorithm
        self.maps = RoomMap()
        self.notes = {}
        # map process for floor 1 2 3
        # return True


    def wait_for_connection(self, stop_event):
        while True:
            try:
                now_client, addr = self.sock.accept()
                print('Connected by', now_client)
                self.state = 2
                print(self.state, self.state, self.state)
                now_client.settimeout(300)
                self.clients.append([addr, now_client])
                # self.handle_data(now_client)
                # data = json.loads(data)
            except:
                pass
            for index_client,n_client in enumerate(self.clients):
                # result = self.sock.connect_ex(n_client)
                try:
                    # rrr = n_client[1].recv(1024)
                    result = n_client[1].getsockname()
                    r = n_client[1].getpeername()
                    print('===========perfect connection============')
                    # print(result, r)
                # if result != 0:
                #     print(n_client, 'Connected closed')
                except Exception as e:
                    print(e, n_client[0], 'Connected closed')
                    try:
                        self.clients.remove(n_client)
                    except:
                        pass
            if not self.state or stop_event.is_set():
                print(self.state, 'No waiting for connection')
                self.sock.close()
                break
            if len(self.clients):
                time.sleep(1)
            else:
                time.sleep(0.01)

    def check_connection(self):
        pass
        # for i in range(2):
        #     for index_client, n_client in enumerate(self.clients):
        #         # result = self.sock.connect_ex(n_client)
        #         try:
        #             rrr = n_client[1].recv(1024)
        #             result = n_client[1].getsockname()
        #             r = n_client[1].getpeername()
        #             print('All right: ',result, r)
        #         # if result != 0:
        #         #     print(n_client, 'Connected closed')
        #         except Exception as e:
        #             print(e, n_client[0], 'Connected closed')
        #             del self.clients[index_client]

    def handle_data(self, n_client):
        # receive message from client -> information process
        data = n_client.recv(10240000)
        # 10240000000
        if not data:
            return 0
        else:
            self.messages.append(data)
        print('---------------------------------')
        # print(f'Received: msg')
        # content = data.decode()
        # ------------------parsing info from unity---------------------
        # self.messages.append(data.decode())
        # content_to_client = json.dumps({'result': 0})
        try:
            # self.unpack(data)
            pass
        except Exception as e:
            print(data)
            print(e)
        # self.send_back({'result': 1})
        return 1
        # except Exception as e:
        #     print(f"JSON解析出错: {e}")
        #     return 0

    def message_process(self, stop_event):
        while True:
            # print(self.state, 'received:')
            if not self.state or stop_event.is_set():
                print(self.state, 'no process')
                break
            if len(self.messages) > 0:
                # print('process')
                for msg_i, msg in enumerate(self.messages):
                    try:
                        self.unpack(msg)
                    except Exception as e:
                        print('.........parsing error............', e, type(msg))
                        self.state = 0
                        # json_data = json.dumps(msg)
                    finally:
                        del self.messages[msg_i]
            # else:
            #     if self.state != 1:
            #         try:
            #             # 进行一些socket操作
            #             data = self.sock.recv(1024)
            #             # 如果在这里发现socket已经关闭，则会引发异常
            #         except Exception as e:
            #             print("Socket closed", e)
            #             break

    def receive_data(self, stop_event):
        while True:
            self.check_connection()
            # print(1)
            for n_client in self.clients:
                try:
                    # print(2)
                    res = self.handle_data(n_client[1])
                    # if not res:
                    #     continue
                    # data = n_client[1].recv(1024)
                    # if not data:
                    #     break
                    # print('-----------------------')
                    # print(f'get: {data.decode()}')
                    # # content = data.decode()
                    # # ------------------parsing info from unity---------------------
                    # # self.messages.append(data.decode())
                    # self.send_back('okk!!!okk')
                # except Exception as e:

                except Exception as e:
                    print(e, n_client[0], 'Connected closed')
                    try:
                        self.clients.remove(n_client)
                    except:
                        pass

            if not self.state or stop_event.is_set():
                print(self.state, 'Connection closed')
                self.sock.close()
                break

    def send_data(self, cmd=1, data={"requestIndex":10,"npcId":0,"actionId":0,"actionPara":""}, recv=0):
        send_finish = 0
        while not send_finish:
            if len(self.clients)==0: break
            for n_client in self.clients:
                self.check_connection()
                try:
                    # n_client[1].send(instruction.encode("utf8"))
                    # print(data)
                    if cmd < 7:
                        data['requestIndex'] = self.count
                        self.count = self.count + 1
                    elif cmd == 0:
                        self.state = 0
                    msg, msg_data = self.pack(cmd, data, recv)
                    n_client[1].send(msg)
                    send_finish = 1
                    # print('********* Sent: ', msg_data)
                    return data['requestIndex']
                    break
                except Exception as e:
                    print(e, n_client[0])
                    try:
                        self.clients.remove(n_client)
                    except:
                        pass
        return False

    def send_back(self, response={'result': 0}):
        f = 0
        while not f:
            for n_client in self.clients:
                self.check_connection()
                try:
                    info = json.dumps(response)
                    n_client[1].send(info.encode("utf8"))
                    print('Sent: ', info.encode("utf8"))
                    f = 1
                    return 1
                except Exception as e:
                    print(e, n_client[0])
                    try:
                        self.clients.remove(n_client)
                    except:
                        pass

    def pack(self, cmd, _body, _recv=0):
        body = json.dumps(_body) # 将消息正文转换成Json格式，并转换成字节编码
        header = [body.__len__(), cmd, _recv] # 将消息头按顺序组成一个列表
        headPack= struct.pack("3I", *header) #  使用struct打包消息头,得到字节编码
        sendData = headPack+body.encode("utf8")  # 将消息头字节和消息正文字节组合在一起
        return sendData, body

    def handle_msg(self, headPack ,body):
        """分类处理接收到的消息字符串"""
        # 数据处理
        cmd= 'ad'
        try:
            cmd = MsgCmd(headPack[1]).name  # 获取Code的值\
        except Exception as e:
            print(headPack[1])
        # print('python get================cmd is', cmd)
        is_recv = headPack[2]
        # print("收到1个数据包->bodySize:{}, cmd:{}, recv:{}".format(headPack[0], cmd, is_recv))
        body = body.replace("false", "False")
        body = body.replace("true", "True")
        p = json.loads(body)  # 将字符串解码并且反序列化为json对象
        dict_data = ast.literal_eval(p)
        # print(dict_data)
        self.information += str(cmd) + str(body)
        # print(body)
        # 检查消息类型.
        # Instruction = 1
        # Request = 2
        # Result = 3
        # State = 4
        # Control = 5
        # Information = 6
        dict_d = copy.deepcopy(dict_data)
        del dict_d['requestIndex']
        self.notes[dict_data['requestIndex']] = dict_d
        if cmd == "EXIT":
            self.state = 0
            print('0、Env is over, exit!')
            return
        elif cmd == "Result":
            print('3、来自unity的执行结果', dict_data)
        elif cmd == "State":
            # 存储参数信息
            # self._log_path = p["logPath"]
            # self._brain_names = p["brainNames"]
            # print(self._log_path)
            # print(self._brain_names)
            # self._recv_init_msg = True
            # -----------map test------------
            print('4、得到的详细信息 id: {}'.format(dict_data['requestIndex']))
            # # dict_map = ast.literal_eval(dict_ma["points"])
            # print(3)
            # with open("map/map3.json", 'w') as file:
            #     json.dump(dict_ma, file)
        elif cmd == "Control":
            pass
        # IK is here
        elif cmd == "Information":
            print("6、这是机器人信息", dict_data['requestIndex'], ', length- ', len(dict_data),)
        else:
            print("\n未知的cmd:{0}".format(cmd))
        # 继续接收消息
        #self._recv_bytes()
        # print(self.notes)

    def unpack(self, data):
        headPack = struct.unpack('3I', bytearray(data[:self.headerSize]))
        bodySize = headPack[0]
        # print(headPack)
        body = data[self.headerSize:self.headerSize + bodySize]
        self.handle_msg(headPack, body.decode("utf8"))
        return 1

    def unpack_pro(self, data, msgHandler):
        dataBuffer = bytes()
        if data:
            self.dataBuffer += data
            while True:
                # 数据量不足消息头部时跳出函数继续接收数据
                if len(self.dataBuffer) < self.headerSize:
                    # print("数据包（%s Byte）小于消息头部长度，跳出小循环" % len(self.dataBuffer))
                    break
                # struct中:!代表Network order，3I代表3个unsigned int数据
                # msg_length = struct.unpack("I", bytearray(msg[:4]))[0]  # 获取信息长度
                headPack = struct.unpack('3I', bytearray(self.dataBuffer[:self.headerSize]))  # 解码出消息头部
                # 获取消息正文长度
                bodySize = headPack[0]
                # 分包情况处理，跳出函数继续接收数据
                if len(self.dataBuffer) < self.headerSize + bodySize:
                    # print("数据包（%s Byte）不完整（总共%s Byte），跳出小循环" % (len(self.dataBuffer), self.headerSize + bodySize))
                    break
                # 读取消息正文的内容
                body = self.dataBuffer[self.headerSize:self.headerSize + bodySize]
                self.handle_msg(headPack, body.decode("utf8"))
                # 粘包情况的处理，获取下一个数据包部分
                self.dataBuffer = self.dataBuffer[self.headerSize + bodySize:]
            if len(self.dataBuffer) != 0:
                return True  # 继续接收消息
            else:
                return False  # 不再接收消息
        else:
            return False  # 不再接收消息

    def env_finish(self, process, stop_event, npcs):
        process.terminate()
        server.send_data(0, {"requestIndex": 10, "actionId": 1}, 0)
        # movement demo
        print('00100')
        server.state = None
        for npc in npcs:
            npc.running = 0
        stop_event.set()
        self.sock.close()
        # process.terminate()
        # 等待进程结束（可选，但推荐）
        process.wait()
        print(server.state, type(server.state))
        print(threading.active_count(), ' ---11111111111111111111')
        time.sleep(10)
        print(threading.active_count(), ' ---11111111111111111111')
        time.sleep(10)
        print(threading.active_count(), ' ---11111111111111111111')




class Command(object):

    def __init__(self, ser, game, per, objects):
        self.id = 0
        self.web = game
        self.server = ser
        self.tar = [0, 1]
        self.near_items = None
        self.object_data = objects
        # 0断开连接,1服务器发送行为指令,2服务器发送状态申请,3客户端回复行为回调,4客户端回复目标状态,5给robot的指令,6关于机器人client的请求/反馈
        self.instruction = [
            [0, {'this is': 'an example for python command to unity API'}, 0],

            [1, {"requestIndex": 10, "npcId": 0, "actionId": 10, "actionPara": "{\"itemId\":177}"}, 1],
            # [1, {"requestIndex":10,"npcId":0,"actionId":0,"actionPara":""}, 1],
            #    python ins index,  npc,
            # [[0,npc_john,position],[]]
            # info -> items.json   id->name

            # 1  npc stand
            # [1, {"requestIndex":10,"npcId":0,"actionId":10,"actionPara":"{\"itemId\":177}"}, 1],
            #   npc sit
            [1, {"requestIndex":10,"npcId":0,"actionId":1,"actionPara":"{\"destination\":{\"x\":-14.56,\"y\":0.0,\"z\":-4.3}}"}, 1],
            # # 2  npc walk to (x,y,z)
            # [1, {"requestIndex":10,"npcId":0,"actionId":2,"actionPara":"{\"angle\":50}"}, 1],
            [1, {"requestIndex": 10, "npcId": 0, "actionId": 0, "actionPara": ""}, 1],
            # 3  npc turn n degrees
            [1, {"requestIndex":10,"npcId":0,"actionId":100,"actionPara": "{\"handType\":-1,\"itemId\":1}"}, 1],
            # 4  npc pick
            [1, {"requestIndex":10,"npcId":0,"actionId":101,"actionPara":"{\"handType\":-1,\"position\":{\"x\":5.0,\"y\":12.0,\"z\":5.0}}"}, 1],
            # 5  npc put
            [1, {"requestIndex":10,"npcId":0,"actionId":300,"actionPara":"{\"expressionType\":100}"}, 1],
            # 6  npc emoji
            [1, {"requestIndex":10,"npcId":0,"actionId":300,"actionPara":"{\"expressionType\":101}"}, 1],
            # 7  npc stand
            # [1, {"requestIndex":10,"npcId":0,"actionId":300,"actionPara":"{\"expressionType\":102}"}, 1],
            [1, {"requestIndex":10,"npcId":0,"actionId":102,"actionPara":"{\"handType\":-1}"},1],
            # 8  npc stand
            [2,  {"requestIndex":0,"targetType":0,"targetId":0}, 1],
            # [2, {"requestIndex": 0, "targetType": 1, "targetId": 2}, 1],
            # 9  npc information query
            # [2,  {"requestIndex":0,"targetType":1,"targetId":3}, 1],
            [2, {"requestIndex": 101, "targetType": 2, "targetId": 1}, 1],
            # 10 object information query
            [5, {"requestIndex": 0, "actionId": 0, "actionPara": "{\"distance\":1.0}"}, 1],
            # 11 robot move forward
            [5, {"requestIndex": 1, "actionId": 1, "actionPara": "{\"degree\":90}"}, 1],
            # 12 robot turn
            [5, {"requestIndex": 2, "actionId": 2, "actionPara": "{\"degree\":90}"}, 1],
            # 13 robot turn
            [5, {"requestIndex": 10, "requireId": 0}, 1],
            # 14 robot position
            [5, {"requestIndex": 11, "requireId": 1}, 1],
            # 15 robot joint

            [1, {"requestIndex": 10, "npcId": 0, "actionId": 400, "actionPara": "{\"showType\":100}"}, 1],
            # 16
            [1, {"requestIndex": 10, "npcId": 0, "actionId": 400, "actionPara": "{\"showType\":101}"}, 1],
            # 17
            [1, {"requestIndex": 10, "npcId": 0, "actionId": 400, "actionPara": "{\"showType\":102}"}, 1],
            # 18
            [1, {"requestIndex": 10, "npcId": 0, "actionId": 400, "actionPara": "{\"showType\":103}"}, 1],
            # 19
            [1, {"requestIndex": 10, "npcId": 0, "actionId": 400, "actionPara": "{\"showType\":104}"}, 1],
            # 20
            [1, {"requestIndex": 10, "npcId": 0, "actionId": 400, "actionPara": "{\"showType\":-1}"}, 1],
            # 21
            [1, {"requestIndex": 10, "npcId": 0, "actionId": 400, "actionPara": "{\"showType\":105}"}, 1],
            # 22
            [1, {"requestIndex": 10, "npcId": 0, "actionId": 400, "actionPara": "{\"showType\":106}"}, 1],
            # 23
            [1, {"requestIndex": 10, "npcId": 0, "actionId": 400, "actionPara": "{\"showType\":200}"}, 1],
            # 24
            # [1, {"requestIndex": 10, "npcId": 3, "actionId": 400, "actionPara": "{\"showType\":201}"}, 1],
            [1, {"requestIndex":0,"targetType":10,"targetId":0}, 1]
            # 25
        ]
        self.npc = per
    def chioce(self, index):
        print("click the Button ", index)
        # num_threads = threading.active_count()
        # print("当前运行的线程数：%d" % num_threadss)
        # 将字符串转换为字典
        data = self.instruction[index]
        if index == 2:
            # data = self.instruction[2]
            action_dict = json.loads(data[1]["actionPara"])

            # 设置 x 和 y 的随机值
            # action_dict["destination"]["x"] = round(np.random.uniform(-1, 1), 2)
            # action_dict["destination"]["z"] = round(np.random.uniform(-1, 1), 2)

            # 更新 actionPara 字符串
            data[1]["actionPara"] = json.dumps(action_dict)
            self.instruction[index] = data

        elif index == 3:
            # [1, {"requestIndex": 10, "npcId": 0, "actionId": 2, "actionPara": "{\"angle\":50}"}, 1],
            for ii in range(10):
                data[1]["npcId"] = ii
                self.send_to_client(data)
        elif index == 4:
            action_dict = json.loads(data[1]["actionPara"])
            action_dict["itemId"] = self.tar[1]
            data[1]["actionPara"] = json.dumps(action_dict)
            self.instruction[index] = data
        elif index == 1:
            action_dict = json.loads(data[1]["actionPara"])
            tar = self.object_data.object_parsing(self.near_items, ['Stool', 'Chair'])
            action_dict["itemId"] = tar
            data[1]["actionPara"] = json.dumps(action_dict)
            self.instruction[index] = data
        #  ---------instruction send----------
        ins_id = self.send_to_client(self.instruction[index])
        # print(ins_id, 'sended')
        if index == 9:
            ins = self.object_data.check_feedback(self.server, ins_id)
            self.near_items = ins
            self.tar[0] = self.object_data.object_parsing(ins, ['Stool'])
            self.tar[1] = self.object_data.object_parsing(ins, ['Apple'])
    #   get response of unity from server messages
        self.web.text = self.server.information

    def send_to_client(self, inf):
        res = self.server.send_data(inf[0], inf[1], inf[2])
#         def send_data(self, cmd=1, data={"requestIndex":10,"npcId":0,"actionId":0,"actionPara":""}, recv=0):
        return res


class ObjectsData(object):

    def __init__(self):
    # def objects_env():
        with open('unity/PRS_Data/StreamingAssets/itemInfo.json', 'r') as file:
            json_data = json.load(file)
        with open('unity/PRS_Data/StreamingAssets/roomInfo.json', 'r') as file:
            room_data = json.load(file)

        # 解析 JSON 数据
        env_objects = []
        for json_i in json_data['statusDetails']:
            data = json.loads(json_i)
            env_objects.append(data)
            # 获取字符串内容
            # string_content = data['statusDetails'][0]

            # 打印字符串内容
            # print(data)

        env_rooms = []
        for json_i in room_data['statusDetails']:
            data = json.loads(json_i)
            env_rooms.append(data)
        room_index = []
        for room_i, roo in enumerate(env_rooms):
            # print()
            xx, zz = [], []
            for point in roo['roomBoudaryPoints']:
                xx.append(point['x'])
                zz.append(point['z'])
            name = roo['roomName']
            # na = name.split('_')
            room_index.append({'name': name, 'x': [min(xx), max(xx)], 'y': roo['roomCenter']['y'], 'z': [min(zz), max(zz)]})
            # print('----------------')

        self.room_area = room_index

        self.objects = env_objects
        self.rooms = env_rooms
        # print(env_rooms)

    def point_determine(self, pos):
        point_P = {}
        try:
            point_P['x'], point_P['y'], point_P['z'] = pos['x'], pos['y'], pos['z']
        except:
            point_P['x'], point_P['y'], point_P['z'] = pos[0], pos[1], pos[2]
        res = None
        for room_i in self.room_area:
            if (room_i['x'][0] <= point_P['x'] <= room_i['x'][1]) and (
                    room_i['z'][0] <= point_P['z'] <= room_i['z'][1]):
                if abs(point_P['y']-room_i['y']) < 3:
                    res = room_i['name']
                    # print("点 P 在房间 F3_Bedroom 中")
        return  res

    def object_parsing(self, ins, target=['Chair','Stool']):
        print('near items: ', ins)
        datas = eval(ins['statusDetail'])
        obj_closed = datas['closeRangeItemIds']
        objec = None
        for i, obj in enumerate(obj_closed):
            name = self.objects[obj]['itemName']
            # print(name)
            for ttt in target:
                if ttt.lower() in name.lower():
            # if target in name:
                    print("The target: ", name, obj, self.objects[obj])
                    return obj
        print('There is no {}'.format(target))
        return objec
        # return None

    def object_query(self, target=['Chair', 'Stool']):
        tar = []
        for i, obj in enumerate(self.objects):
            obj_i = obj['itemId']
            obj_full_name = obj['itemName']
            obj_now = ''.join([char for char in obj_full_name if not char.isdigit()])
            # print(name)
            for name in target:
                if name.lower() == obj_now.lower():
                    tar.append(obj_i)
        return tar

    def check_feedback(self, server, id):
        # try:
        #     inf = server.notes[id]
        # except:
        #     time.sleep(0.5)
        time.sleep(0.1)
        info = None
        for i in range(30):
            try:
                info = server.notes[id]
                break
            except Exception as e:
                print(len(server.notes))
                time.sleep(0.1)
        return info

def cleanup_function(stop_event):
    stop_event.set()

def agent_plan(server, agent):
    agent.get_all_map()
    p, information = agent.pos_query()
    ob = agent.observation_camera_head()
    return 1
    flo, xx, yy, is_o = server.maps.get_point_info((20.9, 1, -44))
    print(flo, xx, yy, is_o)
    print(server.maps.maps_info[0]['x0'], server.maps.maps_info[0]['z0'])
    # server.maps.draw(19.2, 1, -44)
    des = agent.move_to(4)
    flo, xx, yy, is_o = server.maps.get_point_info(des)
    # agent.navigate(flo, (xx, yy))
    # 物理导航
    # agent.move_forward(0.3)
    # agent.pos_query()
    # 机器人位置请求

    # agent.goto_target_goal((18.0, 0.1, -2.99))
    agent.goto_target_goal((-13.9, 0.1, -7.5))
    flo, xx, yy, is_o = server.maps.get_point_info((-2.5, 0.1, -2.8))
    # adjustment
    flo, xx, yy, is_o = server.maps.get_point_info((-12.8, 0.1, 1.7))
    rotation_angle = agent.calculate_rotation_angle(xx, yy)
    # print(information)
    # print('-+++++++++++++++++++++++=', rotation_angle)
    # agent.joint_control(5, rotation_angle)
    # return
    # agent.rotate_right(rotation_angle)
    time.sleep(1)
    # agent.go_to_there((-2.0, 0.1, 0))
    # agent.go_to_there((12.5, 0.1, 0))
    # agent.goto_target_goal((27.0, 0.1, -2.99))
    agent.ik_control()
    time.sleep(2)
    agent.goto_target_goal((3.38, 0.1, 5.99))
    # 物品位置信息
#       {"requestIndex":10,"actionId":6,"result":1,"positionOffset":0.0,"directionOffset":0.0}

# def server_initialization(output_queue):
#     # 初始化类cla的实例
#     server = Server()
#     # 创建接收和发送线程
#     connection_thread = threading.Thread(target=server.wait_for_connection, args=())
#     receive_thread = threading.Thread(target=server.receive_data, args=())
#     parsing_thread = threading.Thread(target=server.message_process, args=())
#     # 启动线程
#     connection_thread.start()
#     receive_thread.start()
#     parsing_thread.start()
#
#     # 将类cla的实例放入队列中
#     output_queue.put(server)
#     print('server initialized', type(server), output_queue.empty())
#
#
# # 函数B，接收类cla的实例作为参数并进行操作
# def agent_initialization(input_queue):
#     # 从队列中获取类cla的实例
#     now_server = input_queue.get()
#     agent = Agent(now_server)
#     agent_thread = threading.Thread(target=agent_plan, args=(now_server, agent))
#     # 启动线程
#
#     agent_thread.start()
#     input_queue.put(now_server)
#     # 对类cla的实例进行操作
#     print("Agent thread start !!!")
# Redirect sys. stdout to an empty file object, thereby closing all print outputs
class DevNull:
    def write(self, msg):
        pass


class PrsEnv(object):
    def __init__(self, is_print=1, not_test_mode=0):
        self.server = Server()
        self.stop_event = threading.Event()
        self.npc_running, self.time_running, self.agent_running = 0, 0, 0
        connection_thread = threading.Thread(target=self.server.wait_for_connection, args=(self.stop_event,))
        receive_thread = threading.Thread(target=self.server.receive_data, args=(self.stop_event,))
        parsing_thread = threading.Thread(target=self.server.message_process, args=(self.stop_event,))
        connection_thread.start()
        receive_thread.start()
        parsing_thread.start()
        # ---------------server begin-------------------
        self.env_time = EnvTime()
        # ---------------time system ready-------------------
        executable_path = 'unity/start.sh'
        if not_test_mode:
            try:
                # 使用subprocess.Popen异步启动可执行文件,stdout 和 stderr 参数用于重定向输出，可以设置为 subprocess.PIPE, subprocess.STDOUT, 或一个文件对象
                self.process = subprocess.Popen([executable_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print("unity.exe 已经启动，现在执行后续代码...")
            except Exception as e:
                print(f"发生错误：{e}")
        # --- unity exe start ---
        while True:
            time.sleep(0.3)
            state = self.server.state
            if state == 2: break
        self.objs_data = ObjectsData()
        # --------------agent begin---------------
        self.agent = Agent(self.server, self.env_time, self.objs_data)
        agent_thread = threading.Thread(target=agent_plan, args=(self.server, self.agent))
        # 启动线程 机器人
        self.agent.get_all_map()
        # agent_thread.start()
        # ----------------------- npc coming----------------------
        npc_0 = Npc(0, self.server, self.env_time, self.objs_data)
        npc_1 = Npc(1, self.server, self.env_time, self.objs_data)
        npc_2 = Npc(2, self.server, self.env_time, self.objs_data)
        npc_3 = Npc(3, self.server, self.env_time, self.objs_data)
        npc_4 = Npc(4, self.server, self.env_time, self.objs_data)
        npc_5 = Npc(5, self.server, self.env_time, self.objs_data)
        npc_6 = Npc(6, self.server, self.env_time, self.objs_data)
        npc_7 = Npc(7, self.server, self.env_time, self.objs_data)
        npc_8 = Npc(8, self.server, self.env_time, self.objs_data)
        npc_9 = Npc(9, self.server, self.env_time, self.objs_data)

        print('start')

        self.npcs = [npc_0, npc_1, npc_2, npc_3, npc_4, npc_5, npc_6, npc_7, npc_8, npc_9]
        if not is_print:
            dev_null = DevNull()
            sys.stdout = dev_null
        time.sleep(1)


        # # --------------------------robot ----------------------

    def npc_start(self, number=1):
        if not self.time_running:
            time_thread = threading.Thread(target=self.env_time.time_simulation, args=(self.stop_event,))
            time_thread.start()
            self.time_running = 1
        if not self.npc_running:
            for npc_i, npc in enumerate(self.npcs):
                if npc_i == number:
                    break
                running_thread = threading.Thread(target=npc.continuous_simulation, args=(self.stop_event,))
                running_thread.start()
            self.npc_running = 1

    # def

if __name__ == '__main__':  # pragma nocover
    # res = input_pos(robot, 0.25, 0.0, 0.79)
    # objs_data = ObjectsData()
    # print(objs_data.point_determine([12,0,-35]))
    server = Server()
    # server.ik_process(0.25,0,0.75)
    # 创建接收和发送线程
    stop_event = threading.Event()
    print(threading.active_count(), ' ---11111111111111111111')
    # stop_event.set()  # 设置事件，表示停止
    connection_thread = threading.Thread(target=server.wait_for_connection, args=(stop_event,))
    receive_thread = threading.Thread(target=server.receive_data, args=(stop_event,))
    parsing_thread = threading.Thread(target=server.message_process, args=(stop_event,))
    # 启动线程
    connection_thread.start()
    receive_thread.start()
    parsing_thread.start()
    # ---------------server begin-------------------d

    env_time = EnvTime()
    time_thread = threading.Thread(target=env_time.time_simulation, args=(stop_event,))
    time_thread.start()
    print(threading.active_count(), ' ---11111111111111111111')
    # 定义可执行文件的路径
    executable_path = 'D:\\BaiduNetdiskDownload\\prs-test\\PRS\\VerticleSlice.exe'  # 如果a.exe在当前目录下，直接使用文件名即可

    # 使用subprocess启动可执行文件
    if 0:
        try:
            # subprocess.run([executable_path], check=True)
            # 使用subprocess.Popen异步启动可执行文件
            # stdout 和 stderr 参数用于重定向输出，可以设置为 subprocess.PIPE, subprocess.STDOUT, 或一个文件对象
            process = subprocess.Popen([executable_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # 现在你可以继续执行后续代码，而不需要等待 a.exe 结束
            print("unity.exe 已经启动，现在执行后续代码...")
        except subprocess.CalledProcessError as e:
            print(f"执行 {executable_path} 时出错，返回码为 {e.returncode}")
        except Exception as e:
            print(f"发生错误：{e}")
    print('wait wait wait')
    while True:
        time.sleep(1)
        state = server.state
        if state == 2:
            break

    objs_data = ObjectsData()
    npc_0 = Npc(0, server, env_time, objs_data)
    # running_thread0 = threading.Thread(target=npc_0.continuous_simulation, args=())
    # running_thread0 = threading.Thread(target=npc_0.walk_around(), args=())
    # # 执行一天的行为
    # running_thread0.start()
    # 启动线程

    # env_time.simulation_start()
    # ---------------npc & time begin-------------------
    # lock = threading.Lock()
    # with lock

    # serialized_obj = pickle.dumps(server)
    # # 反序列化
    # deserialized_obj = pickle.loads(serialized_obj)

    # npc_0.observation_surrounding()
    # 发送周围的图像
    print('start')
    # exit(1)
    env_time.simulation_start()
    # --------------agent begin---------------
    agent = Agent(server, env_time, objs_data)

    agent_thread = threading.Thread(target=agent_plan, args=(server, agent))
    # 启动线程 机器人
    agent.get_all_map()
    # server.maps.get_an_accessible_area(0.0,0,0)
    # exit(1)
    # agent.get_all_map()
    # np.savetxt('map\\floored_matrix.txt', server.maps.floor3, fmt='%d')
    # time.sleep(1)
    # # map process
    # queue1 = Queue()
    # process1 = Process(target=server.maps.plot_map, args=())
    # process1.start()
    # time.sleep(10)
    agent_thread.start()
    # # --------------------------robot ----------------------
    # exit(1)
    # demo start
    npc_list = [f'npc_{i}' for i in range(11)]
    # npc_0 = Npc(0, server)
    npc_1 = Npc(1, server, env_time, objs_data)
    npc_2 = Npc(2, server, env_time, objs_data)
    npc_3 = Npc(3, server, env_time, objs_data)
    npc_4 = Npc(4, server, env_time, objs_data)
    # npc_5 = Npc(5, server)
    # npc_6 = Npc(6, server)
    # npc_7 = Npc(7, server)
    # npc_8 = Npc(8, server)
    # npc_9 = Npc(9, server)
    # npc_10 = Npc(10, server)
    npcs = [npc_0, npc_1, npc_2, npc_3, npc_4]
    running_thread0 = threading.Thread(target=npc_0.continuous_simulation, args=(stop_event,))
    running_thread1 = threading.Thread(target=npc_1.walk_around, args=(stop_event,))
    running_thread2 = threading.Thread(target=npc_2.continuous_simulation, args=(stop_event,))
    running_thread3 = threading.Thread(target=npc_3.walk_around, args=(stop_event,))
    running_thread4 = threading.Thread(target=npc_4.walk_around, args=(stop_event,))
    # running_thread5 = threading.Thread(target=npc_5.walk_around, args=())
    # running_thread6 = threading.Thread(target=npc_6.walk_around, args=())
    # running_thread7 = threading.Thread(target=npc_7.walk_around, args=())
    # running_thread8 = threading.Thread(target=npc_8.walk_around, args=())
    # running_thread9 = threading.Thread(target=npc_9.walk_around, args=())
    # 启动线程
    # running_thread0.start()
    # 执行一天的行为
    running_thread0.start()
    time.sleep(1)
    running_thread1.start()
    # time.sleep(1)
    running_thread2.start()
    # time.sleep(1.0)
    running_thread3.start()
    # time.sleep(1.0)
    running_thread4.start()
    # time.sleep(1.0)
    # running_thread5.start()
    # time.sleep(1.0)
    # running_thread6.start()
    # time.sleep(1.0)
    # running_thread7.start()
    # time.sleep(1.0)
    # running_thread8.start()
    # time.sleep(1.0)
    # running_thread9.start()
    # -------------- pygame ---------------
    # game = WebDemo(server)
    # com = Command(server, game, npc_0, objs_data)
    # game.run(com, env_time)
    if 0:
        time.sleep(60)
        print('finish')
        # pygame.quit()
        server.env_finish(process, stop_event, npcs)
        atexit.register(cleanup_function, stop_event)
        print(threading.active_count(), ' ---11111111111111111111')
    exit(1)
    # game.run(com, env_time)

    while True:
    # while agent.agent_state and game.running :
        time.sleep(2)
    # time.sleep(50)
    server.send_data(0, {"requestIndex": 10, "actionId": 10}, 0)
    # movement demo
    print('001')
    server.state = None
    print(server.state, type(server.state))
    # for thread in threading.enumerate():
    #     if thread.is_alive():
    #         print(thread)
    #         thread.join()
    time.sleep(3)
    print(threading.active_count(),' ---11111111111111111111')
    exit(1)
    game = WebDemo(server)
    com = Command(server, game, npc)
    game.run(com)
    # --------game web--------

    # 测试发送数据到client(unity)
    # for i in range(6):
    #     time.sleep(6)
    #     server.send_data()
    # finish the python socket server
    # time.sleep(6)
    # print('finish')
    # server.state = 0
    # pygame.quit()



'''
-> Unity:  {"requestIndex":10,"npcId":0,"actionId":0,"actionPara":""}
-> Get : {"requestIndex":11, "result":1}


-> Unity:  {"requestIndex":10,"npcId":0,"actionId":0,"actionPara":""}
-> Get : {"result":1}
'''
