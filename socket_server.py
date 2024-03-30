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
            # Accelerate at 120 times the speed
            time_delta = datetime.timedelta(seconds=1)  # Add one more day
            self.current_date += time_delta * self.time_multiplier
            # Control simulation speed
            time.sleep(1)  # Update every second
            # Termination conditions can be added, such as stopping simulation when a specific date is reached
            if self.current_date.year > self.end:
                break

    def time_difference(self):
        time_diff = self.current_date - self.start_time
        hours = time_diff.total_seconds() // 3600
        # print("The time difference is% d hours" % hours)
        return time_diff.days

    def weekday_now(self):
        return self.week[self.current_date.weekday()]

    def simulation_start(self):
        self.start_time = self.current_date


# message define
class MsgCmd(Enum):
    # 0 disconnects, 1 server sends behavior instructions, 2 servers send status requests, 3 clients reply with behavior callbacks,
    # 4 clients reply with target status, 5 instructions to robots, 6 requests/feedback about robot clients
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
        # 1.Create a socket
        self.sock = socket(AF_INET, SOCK_STREAM)
        # 2. Prepare to connect to the server and establish a connection
        serve_ip = 'localhost'
        serve_port = 8000  # 端口，比如8000
        # tcp_socket.connect((serve_ip,serve_port))
        # Connect to the server, establish a connection, with parameters in tuple form
        tcp_address = ('localhost', 8000)
        # Provide a mechanism for checking ports
        self.sock.bind(tcp_address)
        MAX_CONNECTION = 100
        # Start listening for connections
        self.sock.listen(MAX_CONNECTION)
        self.headerSize = 12
        self.count = 0
        # self.robot = PRS_IK()
        # robot ik algorithm
        self.maps = RoomMap()
        self.notes = {}


    def wait_for_connection(self, stop_event):
        while True:
            try:
                now_client, addr = self.sock.accept()
                print('Connected by', now_client)
                self.state = 2
                print(self.state, self.state, self.state)
                now_client.settimeout(300)
                self.clients.append([addr, now_client])
            except:
                pass
            for index_client,n_client in enumerate(self.clients):
                # result = self.sock.connect_ex(n_client)
                try:
                    result = n_client[1].getsockname()
                    r = n_client[1].getpeername()
                    print('===========perfect connection============')
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


    def handle_data(self, n_client):
        # receive message from client -> information process
        data = n_client.recv(10240000)
        if not data:
            return 0
        else:
            self.messages.append(data)
        print('---------------------------------')
        # print(f'Received: msg')
        # ------------------parsing info from unity---------------------
        # self.messages.append(data.decode())
        try:
            # self.unpack(data)
            pass
        except Exception as e:
            print(data)
            print(e)
        # self.send_back({'result': 1})
        return 1

    def message_process(self, stop_event):
        while True:
            if not self.state or stop_event.is_set():
                print(self.state, 'no process')
                break
            if len(self.messages) > 0:
                for msg_i, msg in enumerate(self.messages):
                    try:
                        self.unpack(msg)
                    except Exception as e:
                        print('.........parsing error............', e, type(msg))
                        self.state = 0
                    finally:
                        del self.messages[msg_i]

    def receive_data(self, stop_event):
        while True:
            self.check_connection()
            # print(1)
            for n_client in self.clients:
                try:
                    # Processing received message
                    res = self.handle_data(n_client[1])
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
                    if cmd < 7:
                        data['requestIndex'] = self.count
                        self.count = self.count + 1
                    elif cmd == 0:
                        self.state = 0
                    msg, msg_data = self.pack(cmd, data, recv)
                    n_client[1].send(msg)
                    send_finish = 1
                    return data['requestIndex']
                    break
                except Exception as e:
                    print(e, n_client[0])
                    try:
                        self.clients.remove(n_client)
                    except: pass
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
                    except: pass

    def pack(self, cmd, _body, _recv=0):
        body = json.dumps(_body)
        # Convert the message body to Json format and convert it to byte encoding
        header = [body.__len__(), cmd, _recv]
        # Form a list of message headers in order
        headPack= struct.pack("3I", *header)
        #  Use struct to package message headers and obtain byte encoding
        sendData = headPack+body.encode("utf8")
        # Combine message header bytes and message body bytes together
        return sendData, body

    def handle_msg(self, headPack ,body):
        """Classify and process received message strings"""
        # data processing
        cmd= 'ad'
        try:
            cmd = MsgCmd(headPack[1]).name  # Get the value of Code\
        except Exception as e:
            print(headPack[1])
        # print('python get================cmd is', cmd)
        is_recv = headPack[2]
        # print("Received 1 packet->bodySize:{}, cmd:{}, recv:{}".format(headPack[0], cmd, is_recv))
        body = body.replace("false", "False")
        body = body.replace("true", "True")
        p = json.loads(body)  # Decode and deserialize strings into JSON objects
        dict_data = ast.literal_eval(p)
        # print(dict_data)
        self.information += str(cmd) + str(body)
        # print(body)
        # Check the message type
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
            print('3、Execution results from Unity', dict_data)
        elif cmd == "State":
            # Storing parameter information
            print('4、Detailed information obtained id: {}'.format(dict_data['requestIndex']))
            # # dict_map = ast.literal_eval(dict_ma["points"])
        elif cmd == "Control":
            pass
        # IK is here
        elif cmd == "Information":
            print("6、This is robot information", dict_data['requestIndex'], ', length- ', len(dict_data),)
        else:
            print("\nUnknown cmd:{0}".format(cmd))
        # Continue receiving messages
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
                # Jump out of the function to continue receiving data when there is insufficient data in the message header
                if len(self.dataBuffer) < self.headerSize:
                    # print("Packet (% s Byte) is smaller than the length of the message header, causing a small loop to break out" % len(self.dataBuffer))
                    break
                # struct中:!代表Network order，3I represents 3个unsigned int
                # msg_length = struct.unpack("I", bytearray(msg[:4]))[0]
                # Obtain information length
                headPack = struct.unpack('3I', bytearray(self.dataBuffer[:self.headerSize]))
                # Decode the message header
                # Get message body length
                bodySize = headPack[0]
                # Handling subcontracting situations, jumping out of the function to continue receiving data
                if len(self.dataBuffer) < self.headerSize + bodySize:
                    # print("Packet (% s Byte) incomplete (total of% s Bytes), skipping small loop“ % (len(self.dataBuffer), self.headerSize + bodySize))
                    break
                # Read the content of the message body
                body = self.dataBuffer[self.headerSize:self.headerSize + bodySize]
                self.handle_msg(headPack, body.decode("utf8"))
                # Handling of packet sticking and obtaining the next part of the data packet
                self.dataBuffer = self.dataBuffer[self.headerSize + bodySize:]
            if len(self.dataBuffer) != 0:
                return True  # Continue receiving messages
            else:
                return False  # No longer receiving messages
        else:
            return False  # No longer receiving messages

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
        # Waiting for the process to end (optional, but recommended)
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
        # 0 disconnects, 1 server sends behavior instructions, 2 servers send status requests, 3 clients reply with behavior callbacks, 4 clients reply with target status, 5 instructions to robots, 6 requests/feedback about robot clients
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
        # Convert strings to dictionaries
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
        with open('unity/PRS_Data/StreamingAssets/itemInfo.json', 'r') as file:
            json_data = json.load(file)
        with open('unity/PRS_Data/StreamingAssets/roomInfo.json', 'r') as file:
            room_data = json.load(file)

        # 解析 JSON 数据
        env_objects = []
        for json_i in json_data['statusDetails']:
            data = json.loads(json_i)
            env_objects.append(data)

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
                    # print ("Point P is in room F3_Bedroom")
        return  res

    def object_parsing(self, ins, target=['Chair','Stool']):
        print('near items: ', ins)
        datas = eval(ins['statusDetail'])
        obj_closed = datas['closeRangeItemIds']
        objec = None
        for i, obj in enumerate(obj_closed):
            name = self.objects[obj]['itemName']
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
    # stop the loop


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
    # Physical navigation
    # agent.move_forward(0.3)
    # agent.pos_query()
    # Robot position request

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
    # Item location information
#       {"requestIndex":10,"actionId":6,"result":1,"positionOffset":0.0,"directionOffset":0.0}

# def server_initialization(output_queue):

class DevNull:
    def write(self, msg):
        pass


class PrsEnv(object):
    def __init__(self, is_print=1, not_test_mode=0):
        print("PRS environment beta is starting without interaction")
        print('Please open the Unity program (start.sh)')
        print('PRS challenge task and benchmark come soon!')
        if not is_print:
            dev_null = DevNull()
            sys.stdout = dev_null
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
        executable_path = 'start.sh'
        try:
            if not_test_mode:
                # Start the Shell script using subprocess.Popen and capture stdout and stderr
                process = subprocess.Popen([executable_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print("Starting Unity process...")
                # If needed, you can add more processing logic here, such as waiting for the process to finish, etc.
        except Exception as e:
            # Catch any exceptions that occur during startup and print the error message
            print(f"An error occurred: {e}")
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
                # running_thread = threading.Thread(target=npc.continuous_simulation, args=(self.stop_event,))
                running_thread = threading.Thread(target=npc.walk_around, args=(self.stop_event,))
                running_thread.start()
            self.npc_running = 1


if __name__ == '__main__':  # pragma nocover
    server = Server()



'''
-> Unity:  {"requestIndex":10,"npcId":0,"actionId":0,"actionPara":""}
-> Get : {"requestIndex":11, "result":1}


-> Unity:  {"requestIndex":10,"npcId":0,"actionId":0,"actionPara":""}
-> Get : {"result":1}
'''
