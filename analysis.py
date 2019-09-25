import cv2
import numpy as np
import time
import os
np.set_printoptions(threshold=np.inf)

BLACK_PIX = 0.1  # 帧判断为黑的阈值
# BLACK_AREA = 0.98  # 帧判断为黑屏的面积阈值
IGNORE_TIME = 5  # 忽略视频尾部的时长阈值
MIN_TIME = 10  # 视频的最小时长阈值
BLACK_TIME = 1  # 判断为黑屏的时长阈值
# BLACK_NUM = 5  # 最大黑屏的次数阈值
FREEZE_DIFF = 1  # 判断为静帧的变化阈值
FREEZE_TIME = 1  # 判断为静帧的时长阈值


def black_detect(cur):
    pix = np.mean(cur)  # 求帧像素的平均值
    return True if pix <= BLACK_PIX*255 else False


def freeze_detect(cur,pre):
    if pre is not None:
        # print(np.mean(np.absolute(cur - pre)))
        # if np.mean(np.absolute(cur - pre))<1:
        #     print(np.absolute(cur - pre))
            # print(np.mean(np.absolute(cur - pre)))
        return True if 0 <= np.mean(np.absolute(cur - pre)) <= FREEZE_DIFF else False  #求帧间差
# def freeze_detect(frame):


def video_test(video_path):
    start = time.time()
    cap = cv2.VideoCapture(video_path)
    if cap.isOpened():
        print("process: ", video_path)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        print("总帧数：", frame_count)
        fps = cap.get(cv2.CAP_PROP_FPS)
        print("帧率：", fps)
        num = frame_count - fps * IGNORE_TIME
        # 视频时长检测
        if frame_count <= MIN_TIME*fps:
            print("视频时长不足！")
            return False
        #
        # is_read, frame = cap.read()
        # row = frame.shape[0]
        # col = frame.shape[1]
        # print("row: ",row)
        # print("col: ",col)
        # cap.set(cv2.CAP_PROP_POS_FRAMES,0)
        serial_black = 0
        serial_freeze = 0
        pre = None
        while num:
            is_read, frame = cap.read()
            if is_read:
                frame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
                current_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
                # print(current_pos)
                # print(frame)
                is_black = True if black_detect(frame) else False
                # is_black = True if count_black >= BLACK_AREA * row * col else False
                if is_black:
                    serial_black += 1
                else:
                    if serial_black >= BLACK_TIME * fps:
                        current_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
                        start_time = (current_pos-serial_black)/fps
                        end_time = current_pos/fps
                        duration = serial_black/fps
                        with open('logs/black_log.txt','a') as f:
                            f.write(""+video_path+"  black_start: " + str(start_time)
                                    + "  black_end: " + str(end_time) + "  duration: "+str(duration)+"\n")
                    serial_black = 0
                # print("black detect done!")
                is_freeze = True if freeze_detect(frame, pre) else False
                if is_freeze:
                    serial_freeze += 1
                else:
                    if serial_freeze >= FREEZE_TIME * fps:
                        current_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
                        start_time = (current_pos-serial_freeze)/fps
                        end_time = current_pos/fps
                        duration = serial_freeze/fps
                        with open('logs/freeze_log.txt','a') as f:
                            f.write(""+video_path+"  freeze_start: " + str(start_time)
                                    + "  freeze_end: " + str(end_time) + "  duration: "+str(duration)+"\n")
                    serial_freeze = 0
                # print("freeze detect done!")
                # cv2.imshow("video",frame)
                # cv2.waitKey(1)
            num -= 1
            pre = frame
        cap.release()
        end = time.time()
        print("处理用时：",end-start)
        # return is_black


if __name__ == '__main__':
    start = time.time()
    root_path ="D:\\ai面试\\videoDownload\\1.2\\"
    mid_path = os.listdir(root_path)
    for folder in mid_path:
        video = os.listdir(os.path.join(root_path,folder))
        for v in video:
            file_path = os.path.join(root_path,folder,v)
            video_test(file_path)
    end = time.time()
    print("总用时：", end-start)
    # video_test("test/1.mp4")
