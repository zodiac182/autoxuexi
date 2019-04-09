#! /usr/bin/env python
# -*- coding:utf-8 -*-
from selenium import webdriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
import os
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import json
import time
import logging
import threading
import random
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.chrome.options import Options
import schedule
import sched
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
    def __init__(self, use_Dingtalk=False):
        chrome_options = Options()
        self.__exit_flag = threading.Event()
        self.__exit_flag.clear()
        self.use_Dingtalk = use_Dingtalk
        chrome_options.add_argument('--mute-audio')  # 关闭声音
        if os.path.exists('driver/chrome.exe'):
            chrome_options.binary_location = 'driver/chrome.exe'
        # chrome_options.add_argument('--no-sandbox')#解决DevToolsActivePort文件不存在的报错

        # chrome_options.add_argument('window-size=800x600') #指定浏览器分辨率
        # chrome_options.add_argument('--disable-gpu') #谷歌文档提到需要加上这个属性来规避bug
        # chrome_options.add_argument('--hide-scrollbars') #隐藏滚动条, 应对一些特殊页面
        # chrome_options.add_argument('blink-settings=imagesEnabled=false') #不加载图片, 提升速度
        # chrome_options.add_argument('--headless') #浏览器不提供可视化页面. linux下如果系统不支持可视化不加这条会启动失败
        self.driver = webdriver.Chrome('driver/chromedriver.exe', chrome_options=chrome_options)
        LOGGER.setLevel(logging.CRITICAL)
        # self.driver.get('https://pc.xuexi.cn/points/my-points.html')

    '''
        return value:
            True: already login
            False: not login
    '''

    def login(self):
        self.driver.get('https://pc.xuexi.cn/points/login.html')

        if re.match(r'^https://pc.xuexi.cn/points/login.html.*', self.driver.current_url) and (login_method.get() == 'Dingtalk' or self.use_Dingtalk):
            self.driver.get('https://login.dingtalk.com/login/index.htm?goto=https%3A%2F%2Foapi.dingtalk.com%2Fconnect%2Foauth2%2Fsns_authorize%3Fappid%3Ddingoankubyrfkttorhpou%26response_type%3Dcode%26scope%3Dsnsapi_login%26redirect_uri%3Dhttps%3A%2F%2Fpc-api.xuexi.cn%2Fopen%2Fapi%2Fsns%2Fcallback')
            if self.use_Dingtalk:    # use profile to login
                try:
                    WebDriverWait(self.driver, 60).until(expected_conditions.presence_of_element_located(
                        (By.ID, 'mobile')))
                    for div in self.driver.find_elements_by_id('mobilePlaceholder'):
                        if div.text == u'请输入手机号码':
                            div.click()
                            self.driver.find_element_by_id('mobile').send_keys(config['dingtalk']['username'])

                        if div.text == u'请输入密码':
                            div.click()
                            self.driver.find_element_by_id('pwd').send_keys(config['dingtalk']['password'])

                    self.driver.find_element_by_id('loginBtn').click()
                except Exception:
                    return False

            while (login_method.get() == 'Dingtalk' or self.use_Dingtalk)and not self.__exit_flag.isSet():
                try:
                    WebDriverWait(self.driver, 10).until(expected_conditions.url_matches(r'https://[a-z]*.xuexi.cn.*'))
                    break
                except Exception:
                    pass

        # self.driver.switch_to.frame('ddlogin-iframe')

        if re.match(r'^https://pc.xuexi.cn/points/login.html.*', self.driver.current_url) and login_method.get() == 'QR':
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
            while not self.__exit_flag.isSet():
                try:
                    WebDriverWait(self.driver, 3).until(
                        expected_conditions.presence_of_element_located((By.XPATH, '//div[@class="my-points-card-text"]')))
                    break
                except Exception:
                    pass

        return True

    # return: [u'每日登陆', u'阅读文章', u'观看视频', u'文章学习时长', u'视频学习时长']
    def get_score(self):
        login_url = r'https://pc.xuexi.cn/points/login.html.*'  # check if it has been login
        # score_url = r'https://pc.xuexi.cn/points/my-points.html.*'
        # if not re.match(login_url, self.driver.current_url) and not re.match(score_url, self.driver.current_url):
        #     self.driver.get('https://pc.xuexi.cn/points/my-points.html')
        # self.driver.switch_to.default_content()

        score_url = 'https://pc.xuexi.cn/points/my-points.html'

        try:
            self.driver.get(score_url)
        except selenium.common.exceptions.NoSuchWindowException as error:
            raise Exception(error)

        if re.match(login_url, self.driver.current_url):
            if not self.login():
                return []
        else:
            try:
                WebDriverWait(self.driver, 3).until(
                    expected_conditions.presence_of_element_located((By.XPATH, '//div[@class="my-points-card-text"]')))
            except Exception:
                return []

        score = []
        app.log(u'当前得分情况：')
        score_title = iter([u'每日登陆', u'阅读文章', u'观看视频', u'文章学习时长', u'视频学习时长'])
        for s in self.driver.find_elements_by_xpath('//div[@class="my-points-card-text"]'):
            app.log(u'                     %s: %s' % (next(score_title), s.text), printtime=False)
            try:
                score.append({'score': int(s.text.split('/')[0][:-1]), 'target': int(s.text.split('/')[1][:-1])})
            except Exception:
                pass

        '''
        if there is only one handle, keep it.
        Otherwise, just use it to check the points, and then close it.
        '''
        if len(self.driver.window_handles) > 1:
            self.driver.close()
        return score

    '''
    get an new article url, and open it
    '''

    def read_new_article(self, page=1):
        article_url = 'https://www.xuexi.cn/98d5ae483720f701144e4dabf99a4a34/5957f69bffab66811b99940516ec8784.html?pageNumber=%d' % page
        # https://login.dingtalk.com/login/index.htm?goto=https%3A%2F%2Foapi.dingtalk.com%2Fconnect%2Foauth2%2Fsns_authorize%3Fappid%3Ddingoankubyrfkttorhpou%26response_type%3Dcode%26scope%3Dsnsapi_login%26redirect_uri%3Dhttps%3A%2F%2Fpc-api.xuexi.cn%2Fopen%2Fapi%2Fsns%2Fcallback

        self.driver.get(article_url)
        main_tab = self.driver.current_window_handle      # main page tab, used to open the main page

        self.__exit_flag.clear()

        for link in self.driver.find_elements_by_id("Ca4gvo4bwg7400"):
            self.driver.switch_to.window(main_tab)
            try:
                link.click()
                app.log(u'正在学习文章：%s' % link.text)
                all_tab = self.driver.window_handles
                self.driver.switch_to.window(all_tab[-1])   # switch to new tab
                while not self.__exit_flag.isSet():
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
                        self.__exit_flag.wait(random.randint(0, 3))
                yield True
            except Exception:
                yield False

    '''
    get an new video url, and open it
    '''

    def watch_new_video(self):
        video_url = 'https://www.xuexi.cn/4426aa87b0b64ac671c96379a3a8bd26/db086044562a57b441c24f2af1c8e101.html'

        self.driver.get(video_url)
        main_tab = self.driver.current_window_handle      # main page tab, used to open the main page

        self.__exit_flag.clear()

        for link in self.driver.find_elements_by_id("Ck3ln2wlyg3k00"):
            self.driver.switch_to.window(main_tab)
            try:
                link.click()
                app.log(u'正在观看视频: %s' % link.text)
                all_tab = self.driver.window_handles
                self.driver.switch_to.window(all_tab[-1])   # switch to new tab

                for i in range(10):
                    ActionChains(self.driver).key_down(Keys.DOWN).perform()
                    self.__exit_flag.wait(1)

                duration = WebDriverWait(self.driver, 60).until(expected_conditions.presence_of_element_located(
                    (By.XPATH, './/span[@class="duration"]')))

                ret = duration.get_attribute('innerText')

                time_arr = ret.split(':')

                video_duration = 0
                if len(time_arr) == 2:
                    video_duration = int(time_arr[-1]) + int(time_arr[-2]) * 60
                elif len(time_arr) == 3:
                    video_duration = 60 * 60   # more than 1 hour, count it as i hour
                else:
                    video_duration = 0

                # wait at most 10 minute for each video
                if video_duration > 0 and video_duration < 5 * 60:
                    self.__exit_flag.wait(video_duration)
                else:
                    self.__exit_flag.wait(random.randint(3 * 60, 5 * 60))
                yield True
            except Exception:
                yield False

    def stop(self):
        self.__exit_flag.set()

    def resume(self):
        self.__exit_flag.clear()

    def close(self):
        self.driver.quit()


class Job(threading.Thread):
    def __init__(self, sched_task=False):
        super(Job, self).__init__()
        self.__running = threading.Event()   # true: running    false: quit
        self.__in_progress = threading.Event()      # true: in progress     flase: done
        self.__running.set()
        self.__in_progress.set()
        self.xx_obj = XUEXI(sched_task)

    def run(self):
        while not self.xx_obj.login() and self.__running.isSet():
            return

        self.__in_progress.set()

        while self.__running.isSet():
            try:
                score = self.xx_obj.get_score()
            except Exception:
                app.log(u'网页被异常关闭，当前学习已被终止。')
                break

            if len(score) < 5:
                continue

            if score[1]['score'] < score[1]['target'] or score[3]['score'] < score[3]['target']:  # read articles
                try:
                    if not new_article:
                        new_article = self.xx_obj.read_new_article()
                except NameError:
                    new_article = self.xx_obj.read_new_article()

                try:
                    next(new_article)
                except StopIteration:
                    app.log(u'当日学习任务未完成。但爬取的文章已经全部阅读完毕。 ')
                    self.__running.clear()
                except Exception:
                    new_article = self.xx_obj.read_new_article()
            elif score[2]['score'] < score[2]['target'] or score[4]['score'] < score[4]['target']:  # watch videos
                try:
                    if not new_video:
                        new_video = self.xx_obj.watch_new_video()
                except NameError:
                    new_video = self.xx_obj.watch_new_video()

                try:
                    next(new_video)
                except StopIteration:
                    app.log(u'当日学习任务未完成。但爬取的视频已经全部观看完毕。 ')
                    self.__running.clear()
                except Exception:
                    new_video = self.xx_obj.watch_new_video()
            else:                          # all tasks are done, sleep
                app.log(u'当日学习任务已完成。 ')
                app.log('下次学习时间: %s' % schedule.next_run())
                self.__running.clear()

            self.__in_progress.wait()                     # wait until next task

        self.xx_obj.close()     # close the driver if finished.

    #  pause
    def pause(self):
        self.__in_progress.clear()
        self.xx_obj.stop()

    def job_start(self):
        self.__running.set()
        self.__in_progress.set()
        self.xx_obj.resume()

    def status(self):
        if self.__in_progress.isSet():
            return 'running'
        elif self.__running.isSet():
            return 'pause'
        else:
            return 'not-start'

    def quit(self):
        self.__running.clear()
        self.xx_obj.close()


class App():
    def __init__(self, parent=None, *args, **kwargs):
        # init GUI
        Grid.columnconfigure(parent, 0, weight=1)

        Grid.rowconfigure(parent, 1, weight=1)

        self.tab = ttk.Notebook(parent)
        self.auto_tab = ttk.Frame(self.tab)
        self.manually_tab = ttk.Frame(self.tab)

        self.tab.add(self.manually_tab, text=u'手动学习')
        self.tab.add(self.auto_tab, text=u'自动学习')

        self.tab.grid(row=0, column=0, sticky='NSWE')

        # tab 1
        # widget to display the login method. QR code or By Dingtalk
        self.login_method_menu = ttk.Menubutton(self.manually_tab, text=u'选择登陆方式')
        self.login_method_menu.grid(row=0, column=0, padx=5, pady=5, sticky='NWSE')

        self.menu = Menu(self.login_method_menu, tearoff=False)
        self.login_method_menu.config(menu=self.menu)

        global login_method
        login_method = StringVar()
        login_method.set('QR')

        self.menu.add_radiobutton(label=u"扫码登陆",
                                  variabl=login_method,
                                  value='QR')

        self.menu.add_radiobutton(label=u"钉钉授权登陆",
                                  variabl=login_method,
                                  value='Dingtalk')

        self.separator_tab1 = ttk.Separator(self.manually_tab, orient=VERTICAL)
        self.separator_tab1.grid(row=0, column=1, sticky='NS', padx=10, pady=0)

        self.btn_start = ttk.Button(self.manually_tab, text=u"开始学习", command=self.start_click)
        self.btn_start.grid(row=0, column=2, padx=5, pady=5, sticky='NWSE')

        self.btn_pause = ttk.Button(self.manually_tab, text=u"暂停学习", command=self.pause_click)
        self.btn_pause.grid(row=0, column=3, padx=5, pady=5, sticky='NWSE')

        self.btn_quit = ttk.Button(self.manually_tab, text=u"退出学习", command=self.quit_click)
        self.btn_quit.grid(row=0, column=4, padx=5, pady=5, sticky='NWSE')

        # log window
        self.log_content = Listbox(parent, selectmode=EXTENDED, bg='#FFFFFF')
        self.log_content.grid(row=1, column=0, padx=5, pady=5, sticky='NSWE')

        self.vbar = ttk.Scrollbar(
            parent, orient=VERTICAL, command=self.log_content.yview)
        self.log_content.configure(yscrollcommand=self.vbar.set)
        self.vbar.grid(row=1, column=2, sticky='NS')

        # ######################## setting panel begin ###############################################
        def validate_time():
            try:
                time.strptime(self.schd_time.get(), '%H:%M')
                return True
            except ValueError:
                messagebox.showerror(u'错误', u'时间错误。正确格式例子：23：59')
                return False
            return False

        def restore_input_text():
            self.schd_time.set('')
            return True

        # separator
        self.separator1 = ttk.Separator(self.auto_tab, orient=VERTICAL)
        self.separator1.grid(row=0, column=4, sticky='NS', padx=10, pady=0)

        self.separator2 = ttk.Separator(self.auto_tab, orient=VERTICAL)
        self.separator2.grid(row=0, column=7, sticky='NS', padx=10, pady=0)

        # self.separator4 = ttk.Separator(self.auto_tab, orient=HORIZONTAL)
        # self.separator4.grid(row=2, column=0, columnspan=5, sticky='WE', padx=5, pady=0)

        # use dingtalk
        # self.use_dingtalk = IntVar()
        # self.use_dingtalk_box = ttk.Checkbutton(self.auto_tab, variable=self.use_dingtalk, text=u'钉钉登陆', command=test)
        # self.use_dingtalk_box.grid(row=0, column=0, sticky='NWS')

        # # use_schedule
        # self.use_shcd = IntVar()
        # self.use_shcd_box = ttk.Checkbutton(self.auto_tab, variable=self.use_shcd, text=u'定时学习')
        # self.use_shcd_box.grid(row=1, column=0, sticky='NWS')

        # dingtalk-user
        self.dingtalk_user_title = ttk.Label(self.auto_tab, text=u'钉钉账号：')
        self.dingtalk_user_title.grid(row=0, column=0, pady=5, stick='NSE')

        self.dingtalk_user = StringVar()
        self.dingtalk_user_input = ttk.Entry(self.auto_tab, textvariable=self.dingtalk_user, width=16)
        self.dingtalk_user_input.grid(row=0, column=1, pady=5, stick='NSW')

        # dingtalk passwd
        self.dingtalk_pwd_title = ttk.Label(self.auto_tab, text=u'钉钉密码：')
        self.dingtalk_pwd_title.grid(row=0, column=2, pady=5, stick='NSE')

        self.dingtalk_pwd = StringVar()
        self.dingtalk_pwd_input = ttk.Entry(self.auto_tab, textvariable=self.dingtalk_pwd, show='*', width=16)
        self.dingtalk_pwd_input.grid(row=0, column=3, pady=5, stick='NSW')

        # schedule titie
        self.schd_title = ttk.Label(self.auto_tab, text=u'每日学习时刻:')
        self.schd_title.grid(row=0, column=5, pady=5, stick='NSW')

        # schedule_time
        self.schd_time = StringVar()
        self.schd_time_input = ttk.Entry(self.auto_tab, textvariable=self.schd_time, validate='focusout',
                                         validatecommand=validate_time, invalidcommand=restore_input_text, width=5)
        self.schd_time_input.grid(row=0, column=6, pady=5, stick='NSW')

        # init monitor task
        self.task_monitor = threading.Thread(target=self.run_monitor)
        self.__monitor_flag = threading.Event()
        self.__monitor_flag.set()
        # submit button

        def go_click():
            global config
            config['dingtalk']['username'] = self.dingtalk_user.get()
            config['dingtalk']['password'] = self.dingtalk_pwd.get()
            config['schedule']['schedule_time'] = self.schd_time.get()

            with open('./config/xuexi.conf', 'w+') as f:
                json.dump(config, f)

            app.log(u'保存配置成功。配置及时生效')
            app.log('                    钉钉用户名: %s' % config['dingtalk']['username'], printtime=False)

            schedule.clear()
            if config['schedule']['schedule_time']:
                schedule.every().day.at(config['schedule']['schedule_time']).do(self.start_click, sched_task=True)
            else:
                schedule.every().day.at("08:00").do(self.start_click)

            if not self.task_monitor.isAlive():
                self.task_monitor.setDaemon(True)
                self.task_monitor.start()

            app.log('                    下次学习时间: %s' % schedule.next_run(), printtime=False)

        def stop_click():
            schedule.clear()
            self.__monitor_flag.clear()
            self.quit_click()

        self.btn_go = ttk.Button(self.auto_tab, text=u'Go!', command=go_click)
        self.btn_go.grid(row=0, column=8, pady=5)

        self.btn_stop = ttk.Button(self.auto_tab, text=u'Stop!', command=stop_click)
        self.btn_stop.grid(row=0, column=9, pady=5, columnspan=5)

        # ######################## setting panel end ###############################################
        global config
        self.dingtalk_user.set(config['dingtalk']['username'])
        self.dingtalk_pwd.set(config['dingtalk']['password'])
        self.schd_time.set(config['schedule']['schedule_time'])

    def run_monitor(self):
        self.__monitor_flag.set()
        while self.__monitor_flag.isSet():
            schedule.run_pending()
            time.sleep(1)

    def log(self, logstring, printtime=True):
        if printtime:
            self.log_content.insert(END, u'%s %s' % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), logstring))
        else:
            self.log_content.insert(END, u'%s' % (logstring))

        self.log_content.see(END)

    def start_click(self, sched_task=False):
        try:
            if self.job.isAlive():
                if self.job.status() != 'running':
                    self.job.job_start()
                    self.log(u'继续当日学习。期间您可以正常使用电脑。')
            else:
                self.job = Job(sched_task=sched_task)
                self.job.setDaemon(True)
                self.job.start()
                self.log(u'开始学习。期间您可以正常使用电脑。')
        except Exception:
            self.job = Job(sched_task=sched_task)
            self.job.setDaemon(True)
            self.job.start()
            self.log(u'开始学习，请不要将浏览器最小化。期间您可以正常使用电脑。')

    def pause_click(self):
        try:
            if self.job.isAlive():
                self.log(u'用户暂停学习，请不要关闭浏览器。')
                self.job.pause()
        except AttributeError:
            self.log(u'没有正在进行的学习任务！')

    def quit_click(self):
        try:
            self.job.quit()
            self.log(u'用户退出!停止当前任务。')
        except AttributeError:
            self.log(u'没有正在进行的学习任务！')

    # def show_img(self, pil_image):
    #     tk_image = ImageTk.PhotoImage(pil_image)

    #     self.label_img = Label(root, image = tk_image)

    #     self.label_img.grid(row=2, column=0, padx=5, pady=5, columnspan=3, sticky='NSWE')


def pre_init():
    if not os.path.exists('./driver/chromedriver.exe'):
        raise IOError('chromedriver.exe not found')

    if not os.path.exists('./config/'):
        os.mkdir('./config/')

    global config
    if os.path.exists('./config/xuexi.conf'):
        with open('./config/xuexi.conf', 'r') as f:
            config = json.load(f)
    else:
        config = {
            'use_dingtalk': False,
            'use_schedule': False,
            'dingtalk':
            {
                'username': '',
                'password': ''
            },
            'schedule':
            {
                'schedule_time': '08:00'
            }
        }


if __name__ == '__main__':
    pre_init()
    root = Tk()
    global app
    app = App(parent=root)
    root.geometry('800x480')
    root.title(u'自动学习--学习强国 v0.1.1')
    root.mainloop()
