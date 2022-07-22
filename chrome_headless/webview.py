# -*- coding: utf-8 -*-

"""chrome headless webview
"""

import io
import os
import time

from PIL import Image

import chrome_master
from qt4w import util
from qt4w.webdriver.webkitwebdriver import WebkitWebDriver
from qt4w.webview.webview import IWebView

from .util import general_encode


class ChromeHeadlessWebView(IWebView):
    """chrome headless webview"""

    def __init__(self, debugging_port, url=None, title=None, timeout=10):
        self._debugging_port = debugging_port
        self._url = url
        self._title = title
        self._timeout = timeout
        self._debugger = self.get_debugger()
        self._debugger.register_handler(chrome_master.RuntimeHandler)
        self._debugger.register_handler(chrome_master.InputHandler)
        self._debugger.register_handler(chrome_master.DOMHandler)
        self._width, self._height = self._debugger.page.get_window_size()
        self._scale = self.get_scale()
        self._width *= self._scale
        self._height *= self._scale
        if os.environ.get("QT4W_AUTO_RECORD_SCREEN") == "1":
            self.start_record_screen()

    def __eq__(self, other):
        if not other or not isinstance(other, ChromeHeadlessWebView):
            return False
        return self._debugger == other._debugger

    @property
    def url(self):
        if not self._url:
            self._url = self.eval_script([], "location.href;")
        return general_encode(self._url)

    @property
    def debugger(self):
        return self._debugger

    def get_scale(self):
        result = self.eval_script([], "window.devicePixelRatio;")
        return float(result)

    def get_debugger(self):
        """get chrome debugger instance"""
        master = chrome_master.ChromeMaster(("127.0.0.1", self._debugging_port))
        try:
            return master.find_page(self._title, self._url, timeout=self._timeout)
        except Exception as e:
            process_list = os.popen("ps aux | grep chrome").read()
            util.logger.exception(
                "Get page debugger in 127.0.0.1:%d failed\nCurrent process list: %s"
                % (self._debugging_port, process_list)
            )
            raise e

    @property
    def webdriver_class(self):
        """WebView对应的WebDriver类"""
        return WebkitWebDriver

    @property
    def rect(self):
        """WebView控件的坐标信息"""
        return 0, 0, self._width, self._height

    def convert_frame_tree(self, frame_tree, parent=None):
        """将frame tree转化为Frame对象"""
        frame = util.Frame(
            frame_tree["frame"]["id"],
            frame_tree["frame"].get("name"),
            frame_tree["frame"]["url"],
        )
        if parent:
            parent.add_child(frame)
        if "childFrames" in frame_tree:
            for child in frame_tree["childFrames"]:
                self.convert_frame_tree(child, frame)
        return frame

    def get_frame_id_by_xpath(self, frame_xpaths, timeout=10):
        """获取frame id"""
        time0 = time.time()
        while time.time() - time0 < timeout:
            frame_tree = self._debugger.page.get_frame_tree()
            frame = self.convert_frame_tree(frame_tree)
            frame_selector = util.FrameSelector(self.webdriver_class(self), frame)
            try:
                frame = frame_selector.get_frame_by_xpath(frame_xpaths)
            except util.ControlNotFoundError:
                pass
            else:
                return frame.id
            time.sleep(0.5)
        else:
            raise util.ControlNotFoundError(
                "Find frame %s timeout" % "".join(frame_xpaths)
            )

    def eval_script(self, frame_xpaths, script):
        """在指定frame中执行JavaScript，并返回执行结果

        :param frame_xpaths: frame元素的XPATH路径，如果是顶层页面，则传入“[]”
        :type frame_xpaths:  list
        :param script:       要执行的JavaScript语句
        :type script:        string
        """
        if isinstance(frame_xpaths, list):
            frame_id = self.get_frame_id_by_xpath(frame_xpaths)
        else:
            frame_id = frame_xpaths

        try:
            return self._debugger.runtime.eval_script(frame_id, script)
        except chrome_master.util.JavaScriptError as e:
            raise util.JavaScriptError(e.frame, e.message)

    def screenshot(self):
        """当前WebView的截图
        :return: PIL.Image
        """
        screen_data = self._debugger.page.screenshot()
        return Image.open(io.BytesIO(screen_data))

    def start_record_screen(self):
        """开始录屏"""
        self._debugger.page.start_screencast()

    def stop_record_screen(self):
        """结束录屏"""
        self._debugger.page.stop_screencast()

    def save_screen_video(self, save_path):
        """保存录屏文件

        :param save_path: 文件保存路径
        :type  save_path: string
        """
        self._debugger.page.save_screen_record(save_path)

    def click(self, x_offset, y_offset):
        """点击WebView中的某个坐标
        :param x_offset: 与WebView左上角的横向偏移量
        :type x_offset:  int/float
        :param y_offset: 与WebView左上角的纵向偏移量
        :type y_offset:  int/float
        """
        x_offset /= self._scale
        y_offset /= self._scale
        self._debugger.input.click(x_offset, y_offset)

    def send_keys(self, text):
        """发送可见字符按键

        :param text: 要输入的文本
        :type  text: string
        """
        result = util.EnumKeyCode.parse(text)
        keys = []
        for it in result:
            if isinstance(it, util.KeyCode):
                keys.append(it.code)
            elif isinstance(it, tuple):
                keys.append(it[1])
            else:
                if keys:
                    self._debugger.input.send_keys(keys)
                    keys = []
                self._debugger.input.send_text(it)
        if keys:
            self._debugger.input.send_keys(keys)

    def long_click(self, x_offset, y_offset, duration=1):
        """长按WebView中的某个坐标

        :param x_offset: 与WebView左上角的横向偏移量
        :type x_offset:  int/float
        :param y_offset: 与WebView左上角的纵向偏移量
        :type y_offset:  int/float
        :param duration: 按住的持续时间
        :type duration:  int/float
        """
        x_offset /= self._scale
        y_offset /= self._scale
        self._debugger.input.click(x_offset, y_offset, duration)

    def right_click(self, x_offset, y_offset):
        """右键点击WebView中的某个坐标

        :param x_offset: 与WebView左上角的横向偏移量
        :type x_offset:  int/float
        :param y_offset: 与WebView左上角的纵向偏移量
        :type y_offset:  int/float
        """
        raise NotImplementedError

    def double_click(self, x_offset, y_offset):
        """双击WebView中的某个坐标

        :param x_offset: 与WebView左上角的横向偏移量
        :type x_offset:  int/float
        :param y_offset: 与WebView左上角的纵向偏移量
        :type y_offset:  int/float
        """
        self.click(x_offset, y_offset)
        self.click(x_offset, y_offset)

    def drag(
        self, x1, y1, x2, y2, step=10, fire_press_event=True, fire_release_event=True
    ):
        """从(x1, y1)点拖动到(x2, y2)点

        :param x1: 起点横坐标
        :type x1:  int/float
        :param y1: 起点纵坐标
        :type y1:  int/float
        :param x2: 终点横坐标
        :type x2:  int/float
        :param y2: 终点纵坐标
        :type y2:  int/float
        :param step: 步长
        :type  step: int
        :param fire_press_event:   是否发送Press事件
        :type  fire_press_event:   bool
        :param fire_release_event: 是否发送Release事件
        :type  fire_release_event: bool
        """
        x1 /= self._scale
        y1 /= self._scale
        x2 /= self._scale
        y2 /= self._scale
        self._debugger.input.drag(
            x1,
            y1,
            x2,
            y2,
            step=step,
            fire_press_event=fire_press_event,
            fire_release_event=fire_release_event,
        )

    def hover(self, x_offset, y_offset):
        """

        :param x_offset: 与WebView左上角的横向偏移量
        :type x_offset:  int/float
        :param y_offset: 与WebView左上角的纵向偏移量
        :type y_offset:  int/float
        """
        x_offset /= self._scale
        y_offset /= self._scale
        self._debugger.input.hover(x_offset, y_offset)

    def scroll(self, backward=True):
        """

        :param backward: 是否向后滚动，默认为True
        :type  backward: bool
        """
        raise NotImplementedError

    def upload_file(self, file_path):
        """上传文件

        :param file_path: 文件路径
        :type  file_path: str
        """
        self._debugger.dom.upload_files([file_path])
