# -*- coding: utf-8 -*-
"""Headless模式测试基类
"""

import logging
import os
import time

import chrome_master
import qt4w
import testbase.testcase as tc
from qt4w import browser, util

from .browser import ChromeHeadlessBrowser


class WebHeadlessTestBase(tc.TestCase):
    """Headless Web测试基类
    """

    logger_path = "qt4w_headless_%s.log" % os.getpid()


    def _clean_env(self):
        logger = logging.getLogger("qt4w_headless")
        if os.environ.get("QT4W_DEBUG") != "1":
            logger.info("[%s] Kill all chrome processes" % self.__class__.__name__)
            ChromeHeadlessBrowser.killall()  # 清理残留进程
            ChromeHeadlessBrowser.clearall()
        else:
            logger.info("[%s] Ignore clear chrome" % self.__class__.__name__)

    def pre_test(self):
        logger = logging.getLogger("qt4w_headless")
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(self.logger_path)
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(thread)d %(message)s")
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
        chrome_master.set_logger(logger)
        qt4w.set_logger(logger)
        browser.Browser.register_browser(
            "Chrome", "chrome_headless.browser.ChromeHeadlessBrowser"
        )  # 注册Chrome Headless浏览器
        self._clean_env()

    def post_test(self):
        logger = logging.getLogger("qt4w_headless")
        logger.info("[%s] post_test run" % self.__class__.__name__)
        self._clean_env()

        log_files = {self.logger_path: self.logger_path}
        if (
            not self.test_result.passed
            and os.environ.get("QT4W_AUTO_RECORD_SCREEN") == "1"
        ):
            # 保存录屏文件
            for browser in ChromeHeadlessBrowser.instances:
                for i, webview in enumerate(browser.webviews):
                    video_path = "%s_%s_%s_%d.mp4" % (
                        self.__class__.__name__,
                        browser.port,
                        int(time.time()),
                        (i + 1),
                    )
                    try:
                        webview.stop_record_screen()
                        webview.save_screen_video(video_path)
                    except:
                        util.logger.exception("Save screen video failed")
                    else:
                        self.test_result.info(
                            "Page %s的录屏" % webview.url, attachments={"录屏": video_path}
                        )
        self.test_result.info("QT4W日志", attachments=log_files)

    def get_extra_fail_record(self):
        """用例执行失败时，用于获取用例相关的错误记录和附件信息
        """
        pic_attachments = {}
        for browser in ChromeHeadlessBrowser.instances:
            for i, webview in enumerate(browser.webviews):
                pic_path = "%s_%s_%s_%d.png" % (
                    self.__class__.__name__,
                    browser.port,
                    int(time.time()),
                    (i + 1),
                )
                try:
                    image = webview.screenshot()
                    image.save(pic_path)
                except:
                    util.logger.exception("Take screenshot failed")
                else:
                    pic_attachments["Page %s的截图" % webview.url] = pic_path

        return {}, pic_attachments
