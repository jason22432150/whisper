import whisper
import os
import datetime, time
from zhconv import convert  # 简繁体转换
from tqdm import tqdm
import imageio  # 用来获取视频时长
import torch
import threading

device = torch.device('cuda', 0)


# 获取mp4文件列表
def find_files(path, suffix):
    # """
    # 用来获取path下的所有suffix格式文件
    # @params:
    #     path     - Required  : 目标路径 (str)
    #     suffix   - Required  : 视频文件格式 (str)
    # """
    mp4_files = []
    for root, dirs, files in os.walk(path):
        print("find_files:" + root)
        for file in files:
            if file.endswith('.' + suffix):
                mp4_files.append(os.path.abspath(os.path.join(root, file)))
    return mp4_files


# 秒转时分秒毫秒
def seconds_to_hmsm(seconds):
    hours = str(int(seconds // 3600))
    minutes = str(int((seconds % 3600) // 60))
    seconds = seconds % 60
    milliseconds = str(int(int((seconds - int(seconds)) * 1000)))  # 毫秒留三位
    seconds = str(int(seconds))
    # 补0
    if len(hours) < 2:
        hours = '0' + hours
    if len(minutes) < 2:
        minutes = '0' + minutes
    if len(seconds) < 2:
        seconds = '0' + seconds
    if len(milliseconds) < 3:
        milliseconds = '0' * (3 - len(milliseconds)) + milliseconds
    return f"{hours}:{minutes}:{seconds},{milliseconds}"


def model_transcribe(model, file, verbose, language, q):
    start_transcribe = datetime.datetime.now()
    res = model.transcribe(file, fp16=False, verbose=True, language='Chinese')
    end_transcribe = datetime.datetime.now()
    print('AI花費時間:', end_transcribe - start_transcribe)
    q.put(data)


def write_str(save_file,q):
    start_write = datetime.datetime.now()
    # 写入字幕文件
    res = q.get()
    with open(save_file, 'w', encoding='utf-8') as f:
        print("# 写入字幕文件")
        i = 1
        for r in res['segments']:
            f.write(str(i) + '\n')
            f.write(seconds_to_hmsm(float(r['start'])) + ' --> ' + seconds_to_hmsm(float(r['end'])) + '\n')
            i += 1
            f.write(convert(r['text'], 'zh-tw') + '\n')  # 结果可能是繁体，转为简体zh-cn
            # f.write(convert(r['text']) + '\n')  # 结果可能是繁体，转为简体zh-cn
            f.write('\n')
    end_write = datetime.datetime.now()
    print('寫入字幕花費時間:', end_write - start_write)

def main():
    # 主文件夹
    # file_path = r'\\DESKTOP-0NFCVV5\nas\資工研究所\演算法 Algorithms  交大 電機工程學系 江蕙如老師'
    file_path = r'\\DESKTOP-0NFCVV5\nas\資工研究所\計算機組織\2022年 講義+影片\2022年影片'
    # mp4_files = find_files(file_path, suffix='mp4')
    mp4_files = find_files(file_path, suffix='wmv')

    # 获取模型
    model = whisper.load_model('medium', device=device)

    q = Queue()

    for file in tqdm(mp4_files):
        print("\n")
        print("mp4_files:" + file)
        # 字幕文件保存路径
        # xxx.mp4 --> xxx. + srt
        # 如果是其他格式，如mpweg需要改一下，这里因为都是mp4就直接对字符串切片了
        save_file = file[:-3] + "srt"
        # 判断文件是否存在，存在则说明已经有字幕，跳出不识别
        if os.path.exists(save_file):
            time.sleep(0.01)
            continue
        # 获取当前视频识别开始时间
        start_time = datetime.datetime.now()
        print('正在识别：{} --{}'.format('\\'.join(file.split('\\')[2:]), start_time.strftime('%Y-%m-%d %H:%M:%S')))
        # 获取视频时长
        video = imageio.get_reader(file)
        duration = seconds_to_hmsm(video.get_meta_data()['duration'])
        video.close()
        print('视频时长：{}'.format(duration))
        # 文字识别
        # model_transcribe(model, file, verbose=True, language='Chinese')
        transcribe_threading = threading.Thread(
            target=model_transcribe(model, file, verbose=True, language='Chinese', q=q)) 
        write_str = threading.Thread(target=write_str(save_file=save_file,q=q))   

        transcribe_threading.start()
        transcribe_threading.join()
        write_str.start()
        write_str.join()
        # res = model.transcribe(file, fp16=False, verbose=True, language='Chinese')
        # 获取当前视频识别结束时间
        end_time = datetime.datetime.now()
        print('完成识别：{} --{}'.format('\\'.join(file.split('\\')[2:]), end_time.strftime('%Y-%m-%d %H:%M:%S')))
        print('總共花费时间:', end_time - start_time)


if __name__ == "__main__":
    main()
