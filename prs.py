import matplotlib.pyplot as plt

from socket_server import *

if __name__ == '__main__':
    prs = PrsEnv(is_print=1)
    prs.npc_start(2)
    # npc number start
    ma = np.array(prs.server.maps.floor3)
    # print(ma.shape)(172, 228)

    prs.agent.goto_target_goal((2, 130, 120), position_mode=1)
    ma = prs.server.maps.floor3
    print(1111111111111111111111111111111111111111111111111)
    # plt.imshow(ma)
    # plt.show()

    # 导入，启动，世界坐标
    # 坐标转换，计算可行路径，导航，位置获取
    # 状态获取，房间/物品状态

    # 机器人感知
    # 机器人移动，动作，ik

    # 任务获取，任务进行
    # 任务打分，评测

    # 解压后
    # chmod 777 -R unity