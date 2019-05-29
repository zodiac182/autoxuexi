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
import requests
import sqlite3
# from PIL import Image, ImageTk
# import base64
# import cv2
# import numpy as np


logging.basicConfig(level=logging.ERROR)

#  download dataindex.js
# https://www.xuexi.cn/dataindex.js?v=1549968788


global version
version = '2.1.0'


def read_check(id, type):
    try:
        conn = sqlite3.Connection('data/xuexi.db')
        cursor = conn.cursor()
        if cursor.execute('select * from read_history where id = "%s"' % id).fetchall() == []:
            cursor.execute('insert into read_history values("%s","%s")' % (id, type))
            conn.commit()
            logging.debug('new content %s %s' % (id, type))
            return True
        else:
            logging.debug('%s is in read history' % id)
            return False
    except Exception as error:
        logging.debug(error)
    finally:
        cursor.close()
        conn.close()

    return True


class Autoresized_Notebook(ttk.Notebook):
    def __init__(self, master=None, **kw):
        ttk.Notebook.__init__(self, master, **kw)
        self.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event):
        event.widget.update_idletasks()

        tab = event.widget.nametowidget(event.widget.select())
        # event.widget.configure(height=tab.winfo_reqheight())
        event.widget.configure(width=tab.winfo_reqwidth())


class XUEXI:
    def __init__(self, use_Dingtalk=False):
        chrome_options = Options()
        self.__exit_flag = threading.Event()
        self.__exit_flag.clear()
        self.use_Dingtalk = use_Dingtalk
        if config['mute']:
            chrome_options.add_argument('--mute-audio')  # 关闭声音

        if os.path.exists('driver/chrome.exe'):
            chrome_options.binary_location = 'driver/chrome.exe'
        # chrome_options.add_argument('--no-sandbox')#解决DevToolsActivePort文件不存在的报错
        # chrome_options.add_argument('window-size=800x600') #指定浏览器分辨率
        # chrome_options.add_argument('--disable-gpu') #谷歌文档提到需要加上这个属性来规避bug
        # chrome_options.add_argument('--hide-scrollbars') #隐藏滚动条, 应对一些特殊页面
        # chrome_options.add_argument('blink-settings=imagesEnabled=false') #不加载图片, 提升速度
        if config['background_process'] and self.use_Dingtalk:
            chrome_options.add_argument('--headless')  # 浏览器不提供可视化页面. linux下如果系统不支持可视化不加这条会启动失败
        self.driver = webdriver.Chrome('driver/chromedriver.exe', options=chrome_options)
        LOGGER.setLevel(logging.CRITICAL)

    '''
        return value:
            True: al;ready login
            False: not login
    '''

    def login(self):
        self.driver.get('https://pc.xuexi.cn/points/login.html?ref=https://pc.xuexi.cn/points/my-points.html')

        if re.match(r'^https://pc.xuexi.cn/points/login.html.*', self.driver.current_url) and (login_method.get() == 'Dingtalk' or self.use_Dingtalk):
            self.driver.get('https://login.dingtalk.com/login/index.htm?goto=https%3A%2F%2Foapi.dingtalk.com%2Fconnect%2Foauth2%2Fsns_authorize%3F'
                            'appid%3Ddingoankubyrfkttorhpou%26response_type%3Dcode%26scope%3Dsnsapi_login%26redirect_uri%3Dhttps%3A%2F%2Fpc-api.xuexi.cn'
                            '%2Fopen%2Fapi%2Fsns%2Fcallback')
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
            app.log(u'%s: %s' % (next(score_title), s.text), printtime=False)
            try:
                score.append({'score': int(s.text.split('/')[0][:-1]), 'target': int(s.text.split('/')[1][:-1])})
            except Exception:
                pass

        return score

    '''
    get an new article url, and open it
    '''

    def read_new_article(self):
        article_url = 'https://www.xuexi.cn/lgdata/1jscb6pu1n2.json'

        try:
            resp = requests.get(article_url, proxies=config['proxies'] if config['use_proxy'] else {})
        except Exception:
            raise TimeoutError('Timeout')

        resp_list = eval(resp.text)

        self.__exit_flag.clear()

        for link in resp_list:
            try:
                if not read_check(link['itemId'], 'article'):
                    continue

                self.driver.get(link['url'])
                app.log(u'正在学习文章：%s' % link['title'])
                while not self.__exit_flag.isSet():
                    ActionChains(self.driver).key_down(Keys.DOWN).perform()

                    self.driver.execute_script("""
                        (function(){
                            if (document.documentElement.scrollTop + document.documentElement.clientHeight  >= document.documentElement.scrollHeight*0.9){
                                document.title = 'scroll-done';}
                            })();
                            """)
                    if u'scroll-done' in self.driver.title:
                        break
                    else:
                        self.__exit_flag.wait(random.randint(2, 5))
                app.log(u'%s 学习完毕' % link['title'])
                yield True
            except Exception as error:
                logging.debug(error)
                yield False

    '''
    get an new video url, and open it
    '''

    def watch_new_video(self):
        video_url = 'https://www.xuexi.cn/lgdata/1novbsbi47k.json'

        try:
            resp = requests.get(video_url, proxies=config['proxies'] if config['use_proxy'] else {})
        except Exception as error:
            raise TimeoutError(error)

        resp_list = eval(resp.text)

        self.__exit_flag.clear()

        for link in resp_list:
            try:
                if not read_check(link['itemId'], 'video'):
                    continue

                self.driver.get(link['url'])

                app.log(u'找到视频: %s' % (link['title']))

                web_duration = WebDriverWait(self.driver, 10).until(expected_conditions.presence_of_element_located(
                    (By.CSS_SELECTOR, '.duration')))

                self.__exit_flag.wait(5)  # wait 10 minutes for video loading

                duration = web_duration.get_attribute('innerText')

                app.log(u'正在观看视频: %s, 视频长度:%s' % (link['title'], duration))

                time_arr = duration.split(':')
                try:
                    play = WebDriverWait(self.driver, 2).until(expected_conditions.visibility_of_element_located(
                        (By.CSS_SELECTOR, '.prism-big-play-btn')))
                    play.click()
                except Exception:
                    pass

                video_duration = 0
                if len(time_arr) == 2:
                    video_duration = int(time_arr[-1]) + int(time_arr[-2]) * 60
                elif len(time_arr) == 3:
                    video_duration = 60 * 60   # more than 1 hour, count it as 1 hour
                else:
                    video_duration = 0

                # self.__exit_flag.wait(video_duration)
                while not self.__exit_flag.isSet():
                    web_current_time = WebDriverWait(self.driver, 10).until(expected_conditions.presence_of_element_located(
                        (By.CSS_SELECTOR, '.current-time')))
                    currtime = web_current_time.get_attribute('innerText')
                    if currtime == duration:
                        break
                    else:
                        self.__exit_flag.wait(1)

                # if video_duration > 0 and video_duration < 5 * 60:
                #     self.__exit_flag.wait(video_duration)
                # else:
                #     self.__exit_flag.wait(random.randint(3 * 60, 5 * 60))
                app.log(u'%s 观看完毕' % link['title'])
                yield True
            except Exception as error:
                logging.debug(error)
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
                except TimeoutError as error:
                    app.log('%s %s' % (error, u'如使用代理服务器，请检查代理服务器设置。'))
                    self.__running.clear()

                try:
                    next(new_article)
                except StopIteration:
                    app.log(u'当日学习任务未完成。但爬取的文章已经全部阅读完毕。 ')
                    self.__running.clear()
                except TimeoutError as error:
                    app.log('%s %s' % (error, u'如果使用代理服务器，请检查代理服务器设置。'))
                    self.__running.clear()
                except Exception as error:
                    app.log('%s %s' % (u'错误！请重试', error))
                    self.__running.clear()

            elif score[2]['score'] < score[2]['target'] or score[4]['score'] < score[4]['target']:  # watch videos
                try:
                    if not new_video:
                        new_video = self.xx_obj.watch_new_video()
                except NameError:
                    new_video = self.xx_obj.watch_new_video()
                except TimeoutError as error:
                    app.log('%s %s' % (error, u'如果使用代理服务器，请检查代理服务器设置。'))
                    self.__running.clear()
                try:
                    next(new_video)
                except StopIteration:
                    app.log(u'当日学习任务未完成。但爬取的视频已经全部观看完毕。 ')
                    self.__running.clear()
                except Exception as error:
                    app.log('%s %s' % (u'错误！请重试', error))
                    self.__running.clear()
            else:                          # all tasks are done, sleep
                app.log(u'当日学习任务已完成。 ')
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
        Grid.columnconfigure(parent, 1, weight=1)

        Grid.rowconfigure(parent, 0, weight=1)

        self.tab = Autoresized_Notebook(parent)
        self.auto_tab = ttk.Frame(self.tab)
        self.manually_tab = ttk.Frame(self.tab)
        self.setting_tab = ttk.Frame(self.tab)

        self.tab.add(self.manually_tab, text=u'手动')
        self.tab.add(self.auto_tab, text=u'自动')
        self.tab.add(self.setting_tab, text=u'设置')

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

        self.separator_tab1 = ttk.Separator(self.manually_tab, orient=HORIZONTAL)
        self.separator_tab1.grid(row=1, column=0, sticky='WE', padx=0, pady=0)

        self.btn_start = ttk.Button(self.manually_tab, text=u"开始学习", command=self.start_click)
        self.btn_start.grid(row=2, column=0, padx=5, pady=5, sticky='NSE')

        self.btn_pause = ttk.Button(self.manually_tab, text=u"暂停学习", command=self.pause_click)
        self.btn_pause.grid(row=3, column=0, padx=5, pady=5, sticky='NSE')

        self.btn_quit = ttk.Button(self.manually_tab, text=u"退出学习", command=self.quit_click)
        self.btn_quit.grid(row=4, column=0, padx=5, pady=5, sticky='NSE')

        # log window
        self.log_content = Listbox(parent, selectmode=EXTENDED, bg='#FFFFFF')
        self.log_content.grid(row=0, column=1, padx=5, pady=5, sticky='NSWE')

        self.vbar = ttk.Scrollbar(
            parent, orient=VERTICAL, command=self.log_content.yview)
        self.log_content.configure(yscrollcommand=self.vbar.set)
        self.vbar.grid(row=0, column=2, sticky='NS')

        # ######################## setting panel begin ###############################################
        def validate_time():
            try:
                self.schd_time.set(time.strftime('%H:%M', time.strptime(self.schd_time.get(), '%H:%M')))
                return True
            except ValueError:
                messagebox.showerror(u'错误', u'时间错误。正确格式例子：23:59')
                return False
            return False

        def restore_input_text():
            self.schd_time.set('')
            return True

        self.separator_beforestatus = ttk.Separator(self.auto_tab, orient=HORIZONTAL)
        self.separator_beforestatus.grid(row=3, column=0, sticky='WE', columnspan=2, padx=0, pady=0)

        self.separator_afterstatus = ttk.Separator(self.auto_tab, orient=HORIZONTAL)
        self.separator_afterstatus.grid(row=5, column=0, sticky='WE', columnspan=2, padx=0, pady=0)

        # dingtalk-user
        self.dingtalk_user_title = ttk.Label(self.auto_tab, text=u'钉钉账号：')
        self.dingtalk_user_title.grid(row=0, column=0, pady=5, stick='NSE')

        self.dingtalk_user = StringVar()
        self.dingtalk_user_input = ttk.Entry(self.auto_tab, textvariable=self.dingtalk_user, width=12)
        self.dingtalk_user_input.grid(row=0, column=1, pady=5, stick='NSW')

        # dingtalk passwd
        self.dingtalk_pwd_title = ttk.Label(self.auto_tab, text=u'钉钉密码：')
        self.dingtalk_pwd_title.grid(row=1, column=0, pady=5, stick='NSE')

        self.dingtalk_pwd = StringVar()
        self.dingtalk_pwd_input = ttk.Entry(self.auto_tab, textvariable=self.dingtalk_pwd, show='*', width=12)
        self.dingtalk_pwd_input.grid(row=1, column=1, pady=5, stick='NSW')

        # schedule titie
        self.schd_title = ttk.Label(self.auto_tab, text=u'学习时钟:')
        self.schd_title.grid(row=2, column=0, pady=0, stick='NSW')

        # schedule_time
        self.schd_time = StringVar()
        self.schd_time_input = ttk.Entry(self.auto_tab, textvariable=self.schd_time, validate='focusout',
                                         validatecommand=validate_time, invalidcommand=restore_input_text, width=5)
        self.schd_time_input.grid(row=2, column=1, pady=5, stick='NSW')

        self.auto_status = StringVar()
        self.auto_status.set(u'状态：停止')
        self.auto_status_label = ttk.Label(self.auto_tab, textvariable=self.auto_status)
        self.auto_status_label.grid(row=4, column=0, pady=5, columnspan=2, sticky='NSW')
        # init monitor task

        self.__monitor_flag = threading.Event()
        self.__monitor_flag.set()
        # submit button

        self.btn_go = ttk.Button(self.auto_tab, text=u'Go!', command=self.go_click)
        self.btn_go.grid(row=6, column=1, padx=5, pady=5, sticky='NSE')

        self.btn_stop = ttk.Button(self.auto_tab, text=u'Stop!', command=self.stop_click)
        self.btn_stop.grid(row=7, column=1, padx=5, pady=5, sticky='NSE')

        # ######################## setting panel end ###############################################

        # ############### proxy settings ############

        self.separator_after_proxies = ttk.Separator(self.setting_tab, orient=HORIZONTAL)
        self.separator_after_proxies.grid(row=5, column=0, sticky='WE', columnspan=2, padx=0, pady=0)

        # self.separator_before_proxies = ttk.Separator(self.setting_tab, orient=VERTICAL)
        # self.separator_before_proxies.grid(row=0, column=1, sticky='NS', padx=10, pady=0)

        self.use_proxy = IntVar()
        self.use_proxy_checkbox = ttk.Checkbutton(self.setting_tab, variable=self.use_proxy, text='使用代理')
        self.use_proxy_checkbox.grid(row=0, column=0, pady=5, columnspan=2, stick='NSW')

        self.http_proxy_title = ttk.Label(self.setting_tab, text=u'Http:')
        self.http_proxy_title.grid(row=1, column=0, pady=5, stick='NSE')

        self.http_proxy = StringVar()
        self.http_proxy_input = ttk.Entry(self.setting_tab, textvariable=self.http_proxy, width=16)
        self.http_proxy_input.grid(row=1, column=1, pady=5, stick='NSW')

        # dingtalk passwd
        self.https_proxy_title = ttk.Label(self.setting_tab, text=u'Https:')
        self.https_proxy_title.grid(row=2, column=0, pady=5, padx=5, stick='NSE')

        self.https_proxy = StringVar()
        self.https_proxy_input = ttk.Entry(self.setting_tab, textvariable=self.https_proxy, width=16)
        self.https_proxy_input.grid(row=2, column=1, pady=5, stick='NSW')

        self.mute = IntVar()
        self.mute_checkbox = ttk.Checkbutton(self.setting_tab, variable=self.mute, text='关闭声音')
        self.mute_checkbox.grid(row=3, column=0, pady=5, columnspan=2, stick='NSW')

        self.background_process = IntVar()
        self.background_process_checkbox = ttk.Checkbutton(self.setting_tab, variable=self.background_process, text='后台运行')
        self.background_process_checkbox.grid(row=4, column=0, pady=5, columnspan=2, stick='NSW')

        def proxy_submit():
            app.log(u'保存{0}! 使用代理:：{config[use_proxy]}. '
                    '关闭声音：{config[mute]}.  '
                    '后台播放：{config[background_process]}'.format(u'成功' if self.save_settings() else u'失败', config=config))

        self.proxy_submit = ttk.Button(self.setting_tab, text=u'提交', command=proxy_submit)
        self.proxy_submit.grid(row=6, column=0, pady=5, columnspan=2)

        # load settings
        global config
        self.dingtalk_user.set(config['dingtalk']['username'])
        self.dingtalk_pwd.set(config['dingtalk']['password'])
        self.schd_time.set(config['schedule']['schedule_time'])
        if 'use_proxy' in config:
            self.use_proxy.set(config['use_proxy'])
        if 'proxies' in config:
            self.http_proxy.set(config['proxies']['http'])
            self.https_proxy.set(config['proxies']['https'])

        if 'mute' in config:
            self.mute.set(config['mute'])

        if 'background_process' in config:
            self.background_process.set(config['background_process'])

    def save_settings(self):
        global config
        config['dingtalk']['username'] = self.dingtalk_user.get()
        config['dingtalk']['password'] = self.dingtalk_pwd.get()
        config['schedule']['schedule_time'] = self.schd_time.get()
        config['use_proxy'] = True if self.use_proxy.get() else False
        config['proxies'] = {
            'http': self.http_proxy.get(),
            'https': self.https_proxy.get()
        }
        config['mute'] = True if self.mute.get() else False
        config['background_process'] = True if self.background_process.get() else False

        try:
            with open('./config/xuexi.conf', 'w+') as f:
                json.dump(config, f)
        except FileNotFoundError as error:
            app.log(error)
            return False
        return True

    def run_monitor(self):
        self.__monitor_flag.set()
        while self.__monitor_flag.isSet():
            schedule.run_pending()
            time.sleep(1)
            # self.__monitor_flag.wait()
            if schedule.next_run is not None:
                self.auto_status.set(u'运行中...\n下次运行时间：\n %s\n当前时间:\n %s' % (schedule.next_run(), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            else:
                self.auto_status.set(u'状态：无任务')

        self.auto_status.set(u'状态：停止')

    def log(self, logstring, printtime=True):
        if printtime:
            self.log_content.insert(END, u'%s %s' % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), logstring))
        else:
            self.log_content.insert(END, u'    %s' % (logstring))

        self.log_content.see(END)

    def start_click(self, sched_task=False):
        try:
            self.job.isAlive()
        except AttributeError:
            self.job = Job(sched_task=sched_task)
        else:
            if not self.job.isAlive():
                self.job = Job(sched_task=sched_task)
        finally:
            if not self.job.isAlive():
                self.job.setDaemon(True)
                self.job.start()
                self.log(u'开始学习。请不要最小化浏览器。可在设置中选择后台运行隐藏浏览器进行学习。')
            else:
                if self.job.status() != 'running':
                    self.job.job_start()
                    self.log(u'继续当日学习。请不要最小化浏览器。可在设置中选择后台运行隐藏浏览器进行学习。')

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

    def go_click(self):
        self.save_settings()

        schedule.clear()
        if config['schedule']['schedule_time']:
            schedule.every().day.at(config['schedule']['schedule_time']).do(self.start_click, sched_task=True)
        else:
            schedule.every().day.at("08:00").do(self.start_click)

        try:
            self.task_monitor.isAlive()
        except AttributeError:
            self.task_monitor = threading.Thread(target=self.run_monitor)
        else:
            if not self.task_monitor.isAlive():
                self.task_monitor = threading.Thread(target=self.run_monitor)
        finally:
            if not self.task_monitor.isAlive():
                self.task_monitor.setDaemon(True)
                self.task_monitor.start()

        app.log('当前账号： %s' % config['dingtalk']['username'])
        app.log('等待下次学习时间: %s' % schedule.next_run())

    def stop_click(self):
        schedule.clear()
        self.__monitor_flag.clear()
        self.quit_click()

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
            'dingtalk':
            {
                'username': '',
                'password': ''
            },
            'schedule':
            {
                'schedule_time': '08:00'
            },
            'use_proxy': False,
            'proxies':
            {
                'http': '',
                'https': ''
            },
            'mute': True,
            'background_process': False
        }


if __name__ == '__main__':
    pre_init()
    root = Tk()
    global app
    app = App(parent=root)
    root.geometry('800x480')
    root.title(u'自动学习--学习强国 v' + version)
    root.mainloop()
