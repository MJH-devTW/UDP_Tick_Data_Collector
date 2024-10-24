import numpy as np
import time
import matplotlib.pyplot as plt
import socket
import threading
import re
import matplotlib.ticker as ticker  # 引入 ticker 用於設定數字格式

#本區段註解不得省略__區域開始
#兩台電腦都要掛載 tickclient 並且非本電腦的那台IP 要設定成此py執行電腦的IP
#本區段註解不得省略__區域結束
# 儲存接收的數據（時間戳, 數據）
data_A = []
data_B = []  # 第二組數據儲存
last_received_price_A = None  # 儲存最後一次接收的數據 A
last_received_price_B = None  # 儲存最後一次接收的數據 B
symbol_A = "Price A"  # 預設 symbol A
symbol_B = "Price B"  # 預設 symbol B
areatimesec = 20  # 顯示最近的 10 秒數據

# 設置 UDP 伺服器
UDP_IP = "0.0.0.0"
UDP_PORT_A = 8082  # 第一個端口
UDP_PORT_B = 8092  # 第二個端口


# 日誌緩衝區
log_buffer = []  # 暫存數據的緩衝區
log_write_interval = 60  # 每隔 60 秒寫入一次文件
last_log_write_time = time.time()
# 文件寫入函數，格式為 time, symbol_A, price_A, symbol_B, price_B
def write_log_to_file():
    global log_buffer
    if log_buffer:
        with open("data_log.txt", "a") as log_file:
            log_file.write("\n".join(log_buffer) + "\n")
        log_buffer.clear()  # 清空緩衝區
        print("Log data written to file.")

# 初始化 Socket
sock_A = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_B = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    # 綁定 IP 和連接埠 A
    sock_A.bind((UDP_IP, UDP_PORT_A))
    print(f"UDP server A is running on port {UDP_PORT_A}")
except OSError as e:
    print(f"Failed to bind port {UDP_PORT_A}: {e}")
    exit(1)

try:
    # 綁定 IP 和連接埠 B
    sock_B.bind((UDP_IP, UDP_PORT_B))
    print(f"UDP server B is running on port {UDP_PORT_B}")
except OSError as e:
    print(f"Failed to bind port {UDP_PORT_B}: {e}")
    exit(1)

# 接收 UDP 數據的執行緒函數 A
def receive_udp_data_A():
    global data_A, last_received_price_A, symbol_A
    while True:
        data, addr = sock_A.recvfrom(1024)  # 接收數據
        timestamp = time.time()  # 獲取當前時間戳
        message = data.decode('utf-8')
        message = re.sub(r'[^\x20-\x7E]', '', message)  # 移除不可見字符

        # 根據空格拆分數據
        parts = message.split()
        if len(parts) == 2:
            symbol_A = parts[0]  # 動態更新 symbol A
            price = parts[1]
            price = float(price)

        try:
            data_A.append((timestamp, price))  # 保存數據到 data_A
            last_received_price_A = price  # 更新最後一次接收的價格
            print(f"Received message A: {message} from {addr}")
        except ValueError:
            print(f"Invalid data received: {message}")

# 接收 UDP 數據的執行緒函數 B
def receive_udp_data_B():
    global data_B, last_received_price_B, symbol_B
    while True:
        data, addr = sock_B.recvfrom(1024)  # 接收數據
        timestamp = time.time()  # 獲取當前時間戳
        message = data.decode('utf-8')
        message = re.sub(r'[^\x20-\x7E]', '', message)  # 移除不可見字符

        # 根據空格拆分數據
        parts = message.split()
        if len(parts) == 2:
            symbol_B = parts[0]  # 動態更新 symbol B
            price = parts[1]
            price = float(price)

        try:
            data_B.append((timestamp, price))  # 保存數據到 data_B
            last_received_price_B = price  # 更新最後一次接收的價格
            print(f"Received message B: {message} from {addr}")
        except ValueError:
            print(f"Invalid data received: {message}")

# 啟動接收數據的執行緒 A
udp_thread_A = threading.Thread(target=receive_udp_data_A)
udp_thread_A.daemon = True  # 設定為 daemon 執行緒，程式結束時自動退出
udp_thread_A.start()

# 啟動接收數據的執行緒 B
udp_thread_B = threading.Thread(target=receive_udp_data_B)
udp_thread_B.daemon = True  # 設定為 daemon 執行緒，程式結束時自動退出
udp_thread_B.start()

def run(niter=200000, doblit=True):
    """
    Display the simulation using matplotlib, with time on the x-axis
    and two sets of network data on the y-axis.
    """

    global last_received_price_A, last_received_price_B, symbol_A, symbol_B, last_log_write_time

    fig, ax = plt.subplots(1, 1)
    ax.set_xlim(0, 10)  # 初始設定顯示最近 10 秒的範圍
    ax.set_ylim(0, 10)  # 初始 y 軸範圍設置為 0 到 10
    # 禁用科學記號
    ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useOffset=False))
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter(useOffset=False))
    times_A = []
    values_A = []
    times_B = []
    values_B = []

    # 設置兩條線，A 為藍色，B 為紅色，初始化時的 label
    points_A, = ax.plot([], [], 'o-', label=f'{symbol_A} {UDP_PORT_A} ', markersize=4)
    points_B, = ax.plot([], [], 'o-', color='red', label=f'{symbol_B} {UDP_PORT_B}', markersize=4)
    # 設置圖例在右上角
    ax.legend(loc='upper right')

    plt.draw()

    if doblit:
        # cache the background
        background = fig.canvas.copy_from_bbox(ax.bbox)

    start_time = time.time()

    for ii in range(niter):
        current_time = time.time() - start_time  # 相對時間


        # 更新 A 的數據
        if last_received_price_A is not None:
            value_A = last_received_price_A
        else:
            value_A = 0

        # 更新 B 的數據
        if last_received_price_B is not None:
            value_B = last_received_price_B
        else:
            value_B = 0

        times_A.append(current_time)
        values_A.append(value_A)

        times_B.append(current_time)
        values_B.append(value_B)

        # 只顯示最近 10 秒的數據
        if current_time > areatimesec:
            ax.set_xlim(current_time - areatimesec, current_time)

        # 只根據最近 10 秒的數據動態調整 y 軸範圍
        if len(times_A) > 1:  # 如果已經有多於一個值
            recent_times_A = [t for t in times_A if current_time - t <= areatimesec]
            recent_values_A = values_A[-len(recent_times_A):]

            recent_times_B = [t for t in times_B if current_time - t <= areatimesec]
            recent_values_B = values_B[-len(recent_times_B):]

            # 合併 A 和 B 的最近數據來調整 y 軸
            recent_values = recent_values_A + recent_values_B
            if recent_values:
                y_min = min(recent_values)
                y_max = max(recent_values)
                buffer = (y_max - y_min) * 0.2  # 添加 20% 的緩衝區
                ax.set_ylim(y_min - buffer, y_max + buffer)

        # 更新兩條數據線
        points_A.set_data(times_A, values_A)
        points_B.set_data(times_B, values_B)

        # 動態更新圖例的 label
        points_A.set_label(f'{symbol_A} {UDP_PORT_A} ')
        points_B.set_label(f'{symbol_B} {UDP_PORT_B} ')

        ax.legend()

        if doblit:
            # restore background
            fig.canvas.restore_region(background)

            # redraw just the points
            ax.draw_artist(points_A)
            ax.draw_artist(points_B)

            # blit the axes
            fig.canvas.blit(ax.bbox)
        else:
            # redraw everything
            fig.canvas.draw()

        # 將數據寫入緩衝區，格式為 time, symbol_A, price_A, symbol_B, price_B
        log_buffer.append(f"{current_time}, {symbol_A}, {value_A}, {symbol_B}, {value_B}")

        # 定期寫入文件
        if time.time() - last_log_write_time >= log_write_interval:
            write_log_to_file()  # 寫入日誌
            last_log_write_time = time.time()

        # pause for a short interval to allow for animation effect
        plt.pause(0.02)  # 每 0.5 秒更新一次數據

    plt.show()

# 運行模擬
run()
