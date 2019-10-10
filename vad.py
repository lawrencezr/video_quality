# -*- coding: utf-8 -*-
import collections
import contextlib
import sys
import os
import wave
import subprocess
import webrtcvad
import numpy as np
import shutil
AGGRESSIVENESS = 2
from analysis import video_test
import time


def read_wave(path):
    """Reads wave file.

    Takes the path, and returns (PCM audio data, sample rate).
    """
    with contextlib.closing(wave.open(path, 'rb')) as wf:
        num_channels = wf.getnchannels()
        print(num_channels)
        assert num_channels == 2
        sample_width = wf.getsampwidth()
        assert sample_width == 2
        sample_rate = wf.getframerate()
        assert sample_rate in (8000, 16000, 32000)
        nframes = wf.getnframes()
        pcm_data = wf.readframes(nframes)
        return nframes, pcm_data, sample_rate


def write_wave(path, audio, sample_rate):
    """Writes a .wav file.

    Takes path, PCM audio data, and sample rate.
    """
    with contextlib.closing(wave.open(path, 'wb')) as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio)


class Frame(object):
    """Represents a "frame" of audio data."""
    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration


def frame_generator(frame_duration_ms, audio, sample_rate):
    """Generates audio frames from PCM audio data.

    Args:
        frame_duration_ms: The desired frame duration in milliseconds.
        audio: The PCM data.
        sample_rate: The sample rate
    """
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n


def vad_collector(sample_rate, vad, frames):
    """Filters out non-voiced audio frames.

    Args:
        sample_rate: The audio sample rate, in Hz.
        vad: An instance of webrtcvad.Vad.
        frames: A source of audio frames (sequence or generator).

    Returns: A generator that yields PCM audio data.
    """

    voiced_frames = []
    for idx, frame in enumerate(frames):
        is_speech = vad.is_speech(frame.bytes, sample_rate)
        if is_speech:
            voiced_frames.append(frame)

    return b''.join([f.bytes for f in voiced_frames])


def voiced_frames_expand(voiced_frames, duration=2):
    total = duration * 8000 * 2
    expanded_voiced_frames = voiced_frames
    while len(expanded_voiced_frames) < total:
        expand_num = total - len(expanded_voiced_frames)
        expanded_voiced_frames += voiced_frames[:expand_num]

    return expanded_voiced_frames



def filter(wavpath, out_dir, expand=False):
    '''Apply vad with wave file.

    Args:
        wavpath: The input wave file.
        out_dir: The directory that contains the voiced audio.
        expand: Expand the frames or not, default False.
    '''
    flag = 0
    print("wavpath:", wavpath)
    nframes, audio, sample_rate = read_wave(wavpath)
    print('sample rate:%d'%sample_rate)
    vad = webrtcvad.Vad(2)  # 0: Normal，1：low Bitrate， 2：Aggressive；3：Very Aggressive
    frames = frame_generator(30, audio, sample_rate)
    frames = list(frames)
    voiced_frames = vad_collector(sample_rate, vad, frames)
    voiced_frames = voiced_frames_expand(voiced_frames, 2) if expand else voiced_frames
    waveData = np.fromstring(voiced_frames, dtype=np.int16)
    wav_name = wavpath.split('\\')[-1]
    save_path = out_dir + '\\' + wav_name
    if nframes > np.size(waveData)*2:
        write_wave(save_path, voiced_frames, sample_rate)
        flag = 1
    return flag




def all_path(dirname):

    result = []#所有的文件

    for maindir, subdir, file_name_list in os.walk(dirname):

        print("1:",maindir)  # 当前主目录
        print("2:",subdir)  # 当前主目录下的所有目录
        print("3:",file_name_list)   # 当前主目录下的所有文件

        for filename in file_name_list:
            apath = os.path.join(maindir, filename)#合并成一个完整路径
            result.append(apath)

    return result


def main():
    error_video = []
    dir = 'D:\\ai面试\\videoDownload\\1.2'  # 原视频存储路径
    wave_path = 'D:\\pyprojects\\quality_analysis\\wav\\'  # 转换为wav格式的视频存储路径
    out_dir = 'D:\\pyprojects\\quality_analysis\\clean'  # 去除噪音和静音之后的人声视频储存路径
    error = 'D:\\pyprojects\\quality_analysis\\detect_error_video\\'  # 有问题的视频储存路径
    all_filepath = all_path(dir)

    start = time.time()
    for filepath in all_filepath:
        filepath_no_ext = os.path.splitext(filepath)[0]
        wav_name = filepath_no_ext.split('\\')[-1]
        error_path = error+wav_name + '.mp4'
        try:
            start_time = time.time()
            command = "ffmpeg -i" + " " + filepath + " " + "-ar 16000 -vn" + " " + wave_path+wav_name + ".wav"
            print('command', command)
            subprocess.call(command, shell=True)
            video_test(filepath)
        except Exception as e:
            print(e)
        in_wav = wave_path+wav_name + '.wav'
        flag = filter(in_wav, out_dir, expand=False)
        # 你会在你out_dir目录下得到经过vad的test.wav文件
        if flag == 1:
            error_video.append(filepath)
            shutil.copy(filepath, error_path)
        end_time = time.time()
        print("处理用时："+str(end_time-start_time))
    end = time.time()
    print(error_video)
    print(str(len(all_filepath))+"个视频用时："+str(end-start))

if __name__ == '__main__':
    main()
