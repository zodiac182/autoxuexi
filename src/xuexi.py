#! /usr/bin/env python
# -*- coding:utf-8 -*-
from selenium import webdriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import requests
from datetime import datetime
import os
from Tkinter import *
import tkMessageBox
import json
import time
import logging
import threading
import random
from selenium.webdriver.remote.remote_connection import LOGGER
# from selenium.webdriver.chrome.options import Options
# from PIL import Image, ImageTk
# import base64
# import cv2
# import numpy as np


logging.basicConfig(level=logging.ERROR)

#  download dataindex.js 
# https://www.xuexi.cn/dataindex.js?v=1549968788


'''
Since it is used in personal PC, no database is available.
Try to store url list by files.
    articles: 
    videos:

File named *.old means it has been read.
'''

class XUEXI:
    def __init__(self):
        # chrome_options = Options()
        # chrome_options.add_argument('--no-sandbox')#解决DevToolsActivePort文件不存在的报错

        # chrome_options.add_argument('window-size=800x600') #指定浏览器分辨率
        # chrome_options.add_argument('--disable-gpu') #谷歌文档提到需要加上这个属性来规避bug
        # chrome_options.add_argument('--hide-scrollbars') #隐藏滚动条, 应对一些特殊页面
        # chrome_options.add_argument('blink-settings=imagesEnabled=false') #不加载图片, 提升速度
        # chrome_options.add_argument('--headless') #浏览器不提供可视化页面. linux下如果系统不支持可视化不加这条会启动失败
        # self.driver = webdriver.Chrome('driver/chromedriver.exe', chrome_options=chrome_options)
        self.driver = webdriver.Chrome('driver/chromedriver.exe')
        LOGGER.setLevel(logging.ERROR)
        #self.driver.get('https://pc.xuexi.cn/points/my-points.html')

    '''
    return json:
        url: 
        title:
        id:
    '''
    def get_new_article(self):
        ret = ''
        list_a = iter(os.listdir('articles/'))
        while True:
            try:
                file = next(list_a)
                if os.path.exists('articles/' + file + '.old'):
                    os.remove('articles/' + file + '.old')

                if not file.endswith('old'):
                    os.rename('articles/' + file, 'articles/' + file + '.old')

                    with open('articles/' + file + '.old', 'rb') as f:
                        ret = json.load(f)
                    yield ret
            except StopIteration:
                ret = ''
                yield ret


    '''
    return json:
        url: 
        title:
        id:
    '''
    def get_new_video(self):
        ret = ''
        list_v = iter(os.listdir('videos/'))
        while True:
            try:
                file = next(list_v)
                if os.path.exists('videos/' + file + '.old'):
                    os.remove('videos/' + file + '.old')

                if not file.endswith('old'):
                    os.rename('videos/' + file, 'videos/' + file + '.old')

                    with open('videos/' + file + '.old', 'rb') as f:
                        ret = json.load(f)
                    yield ret
            except StopIteration:
                ret = ''
                yield ret

    '''
        return value:
            True: already login
            False: not login
    '''
    def login(self):
        reg_url = r'https://pc.xuexi.cn/points/login.html.*'  # check if it has been login

        self.driver.get('https://pc.xuexi.cn/points/my-points.html')
        #self.driver.switch_to.frame('ddlogin-iframe')

        if re.match(reg_url, self.driver.current_url):
            # login_QR = WebDriverWait(self.driver, 10).until(
            #     expected_conditions.presence_of_element_located((By.XPATH, '//div[@id="qrcode"]//img')))
            # base64QR = login_QR.get_attribute('src')

            # imgData = base64.b64decode(base64QR[22:])
            # nparr = np.fromstring(imgData, np.uint8)
            # img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            # cv2.imshow("test",img_np)
            # cv2.waitKey(0)

            # current_image = Image.fromarray(img_np)
            # global app
            # app.show_img(current_image)

            # wait for login
            app.log(u'请扫码登陆')
            try:
                WebDriverWait(self.driver, 60).until(
                    expected_conditions.presence_of_element_located((By.XPATH, '//div[@class="my-points-card-text"]')))
                return True
            except:
                return False
        else:
            return True

    # return: [u'每日登陆', u'阅读文章', u'观看视频', u'文章学习时长', u'视频学习时长']
    def get_score(self):
        # login_url = r'https://pc.xuexi.cn/points/login.html.*'  # check if it has been login
        # score_url = r'https://pc.xuexi.cn/points/my-points.html.*'
        # if not re.match(login_url, self.driver.current_url) and not re.match(score_url, self.driver.current_url):
        #     self.driver.get('https://pc.xuexi.cn/points/my-points.html')
        #self.driver.switch_to.default_content()
        while self.login() == False:
            pass


        score = []
        app.log(u'当前得分情况：')
        score_title = iter([u'每日登陆', u'阅读文章', u'观看视频', u'文章学习时长', u'视频学习时长'])
        score_reg = u'^(%d)分.*'
        for s in self.driver.find_elements_by_xpath('//div[@class="my-points-card-text"]'):
            app.log(u'      %s: %s' %(score_title.next(),s.text), printtime=False)
            try:
                score.append(int(s.text.split('/')[0][:-1]))
            except:
                pass
        return score

    '''
    get an new article url, and open it
    '''
    def read_new_article(self):
        new_article = next(self.get_new_article())

        if new_article == '':
            app.log(u'没有找到新文章，请重新更新数据')
            app.log(u'自动进行数据更新...')
            update_local_data()
            return

        self.driver.get(new_article['url'])
        app.log(u'正在学习文章：%s' % new_article['title'])
        while True:
            ActionChains(self.driver).key_down(Keys.DOWN).perform()

            self.driver.execute_script("""
                (function(){
                    if (document.documentElement.scrollTop + document.body.clientHeight >= document.body.scrollHeight - 10){
                        document.title += "scroll-done";}
                    })();
                    """)
            if u'scroll-done' in self.driver.title:
                break
            else:
                time.sleep(random.randint(0,3))

    '''
    get an new video url, and open it
    '''
    def read_new_video(self):
        new_video = next(self.get_new_video())
        if new_video == '':
            app.log(u'没有找到新视频，请重新更新数据')
            app.log(u'自动进行数据更新...')
            update_local_data()
            return

        self.driver.get(new_video['url'])
        app.log(u'正在观看视频: %s' % new_video['title'])
        duration = self.driver.find_element_by_xpath('.//span[@class="duration"]')

        ret = duration.get_attribute('innerText')

        time_arr = ret.split(':')

        video_duration = 0
        if len(time_arr) == 2:
            video_duration = int(time_arr[1]) + int(time_arr[0]) * 60
        elif len(time_arr) == 3:
            video_duration = int(time_arr[2]) + int(time_arr[1]) * 60 + int(time_arr[2]) * 60 * 60
        else:
            video_duration = 0

        for i in range(10):
            ActionChains(self.driver).key_down(Keys.DOWN).perform()
            time.sleep(1)

        # wait at most 10 minute for each video
        if video_duration > 0 and video_duration < 10 * 60:
            time.sleep(video_duration)
        else:
            time.sleep(random.randint(6 * 60, 10 * 60))

    def close(self):
        self.driver.quit()


class Job(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(Job, self).__init__()
        self.__running = threading.Event()
        self.__running.clear()

    def run(self):
        self.xx_obj = XUEXI()
        self.__running.set()
        while self.__running.isSet():
            score = self.xx_obj.get_score()
            if len(score) < 5:
                continue

            if score[1] < 6 or score[3] < 8:  # read articles
                self.xx_obj.read_new_article()
            elif score[2] < 6 or score[4] < 10:  # watch videos
                self.xx_obj.read_new_video()
            else:                          #  all tasks are done, sleep
                app.log(u'当日学习任务已完成。 如果保持程序继续运行，明天将自动进行学习。')
                time.sleep(random.randint(30*60, 90 * 60))

    def stop(self):
        self.__running.clear()
        self.xx_obj.close()

class App():
    def __init__(self, parent=None, *args, **kwargs):
        Grid.columnconfigure(parent, 0, weight=1)
        Grid.columnconfigure(parent, 1, weight=1)
        Grid.columnconfigure(parent, 2, weight=1)

        Grid.rowconfigure(parent, 1, weight=1)

        self.btn_start = Button(parent, text=u"开始学习", command=self.start_click)
        self.btn_start.grid(row=0, column=0, padx=5, pady=5, sticky='NWSE')

        self.btn_stop = Button(parent, text=u"停止学习", command=self.stop_click)
        # self.btn_stop.grid(row=0, column=1, padx=5, pady=5, sticky='NWSE')

        self.btn_sync = Button(parent, text=u"更新数据", command=self.sync_click)
        self.btn_sync.grid(row=0, column=1, padx=5, pady=5, sticky='NWSE')

        self.btn_clear = Button(parent, text=u"清理数据", command=self.clear_click)
        self.btn_clear.grid(row=0, column=2, padx=5, pady=5, sticky='NWSE')

        self.log_content = Listbox(parent, selectmode=EXTENDED, bg='#FFFFFF')
        self.log_content.grid(row=1, column=0, padx=5, pady=5, columnspan=3, sticky='NSWE')

        self.vbar = Scrollbar(
            parent, orient=VERTICAL, command=self.log_content.yview)
        self.log_content.configure(yscrollcommand=self.vbar.set)
        self.vbar.grid(row=1, column=3, sticky='NS')


        self.job = Job()

    def log(self, logstring, printtime=True):
        if printtime:
            self.log_content.insert(END, u'%s %s' % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), logstring))
        else:
            self.log_content.insert(END, u'%s' % (logstring))

        self.log_content.see(END)

    def start_click(self):
        if not self.job.isAlive():
            self.job = Job()
            self.job.setDaemon(True)
            self.job.start()
            self.log(u'开始学习，请不要将浏览器最小化。期间您可以正常使用电脑。')
            self.btn_start.grid_forget()
            self.btn_stop.grid(row=0, column=0, padx=5, pady=5, sticky='NWSE')

    def stop_click(self):
        self.btn_stop.grid_forget()
        self.btn_start.grid(row=0, column=0, padx=5, pady=5, sticky='NWSE')
        self.log(u'用户停止')
        self.job.stop()

    def sync_click(self):
        p = threading.Thread(target=update_local_data)
        p.setDaemon(True)
        p.start()

    def clear_click(self):
        if tkMessageBox.askokcancel(u'谨慎操作', u'清理数据将删除您的阅读记录，您确定要清理数据吗？'):
            for file in os.listdir('articles/'):
                os.remove('articles/' + file)
            for file in os.listdir('videos/'):
                os.remove('videos/' + file)

            app.log(u'数据清理完毕')

    # def show_img(self, pil_image):
    #     tk_image = ImageTk.PhotoImage(pil_image)

    #     self.label_img = Label(root, image = tk_image)

    #     self.label_img.grid(row=2, column=0, padx=5, pady=5, columnspan=3, sticky='NSWE')

def update_local_data():
    resp = requests.get('https://www.xuexi.cn/dataindex.js')
    new_video_count = 0
    new_article_count = 0
    if resp.ok:
        data = json.loads(resp.content[14:-1])
        for key in data:
            for child_key in data[key]:
                if type(data[key][child_key]) == list:
                    for detail in data[key][child_key]:
                        if '_id' in detail and 'static_page_url' in detail:
                            if 'e43e220633a65f9b6d8b53712cba9caa' in detail['static_page_url']:
                                if not os.path.exists('articles/' + detail['_id'] + '.old') and not os.path.exists('articles/' + detail['_id']):
                                    with open('articles/' + detail['_id'], 'wb+') as f:
                                        content = {
                                            'id': detail['_id'],
                                            'url': detail['static_page_url'],
                                            'title': detail['frst_name']
                                        }
                                        json.dump(content, f)
                                    new_article_count += 1
                            elif 'cf94877c29e1c685574e0226618fb1be' in detail['static_page_url']:
                                if not os.path.exists('videos/' + detail['_id'] + '.old') and not os.path.exists('videos/' + detail['_id']):
                                    with open('videos/' + detail['_id'], 'wb+') as f:
                                        content = {
                                            'id': detail['_id'],
                                            'url': detail['static_page_url'],
                                            'title': detail['frst_name']
                                        }
                                        json.dump(content, f)
                                    new_video_count += 1
        app.log(u'数据更新完毕, 新增文章%d篇，新增视频%d个' % (new_article_count, new_video_count))
    else:
        app.log(u'获取新数据失败，请重试')


if __name__ == '__main__':
    root = Tk()
    global app
    app = App(parent=root)
    root.geometry('640x480')
    root.title(u'自动学习--学习强国 v0.1 beta')
    root.mainloop()
