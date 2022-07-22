# -*- coding: utf-8 -*-
"""chrome headless browser
"""

import logging
import os
import shutil
import socket
import subprocess
import sys
import time
from qt4w.browser import IBrowser
from qt4w.webcontrols import WebPage

from .webview import ChromeHeadlessWebView


class ChromeHeadlessBrowser(IBrowser):
    """chrome headless browser"""

    if sys.platform == "win32":
        user_data_dir_tmpl = os.path.join(os.environ["TEMP"], "Chrome_%d")
    else:
        user_data_dir_tmpl = "/tmp/Chrome_%d"
    instances = []

    def __init__(self, port=9200):
        self._port = port
        self._webviews = []
        ChromeHeadlessBrowser.instances.append(self)

    @property
    def port(self):
        return self._port

    @property
    def webview(self):
        return self._webviews[-1] if self._webviews else None

    @property
    def webviews(self):
        return self._webviews

    def is_port_free(self, port):
        """端口是否空闲"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("localhost", port))
        except:
            return False
        else:
            sock.close()
            return True

    def check_server(self, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(("127.0.0.1", port))
        except:
            return False
        else:
            sock.close()
            return True

    def get_next_free_port(self, port):
        """获取下一个空闲的端口"""
        while not self.is_port_free(port):
            port += 1
        return port

    def open_url(self, url, page_cls=None, proxy_server=None, **kwargs):
        """打开一个url，返回page_cls类的实例

        :param url: 要打开页面的url
        :type url:  string
        :param page_cls: 要返回的具体WebPage类,为None表示返回WebPage实例
        :type page_cls: Class
        :param proxy_server: 使用的代理服务器地址
        :type proxy_server: string
        """
        if "&" in url:
            url = url.replace("&", "\&")

        self._port = self.get_next_free_port(self._port)
        stdin = subprocess.PIPE
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE
        user_data_dir = self.user_data_dir_tmpl % self._port
        if os.path.isdir(user_data_dir):
            shutil.rmtree(user_data_dir)

        if sys.platform == "win32":
            for path in os.environ["PATH"].split(";"):
                chrome_path = os.path.join(path, "Chrome.exe")
                if os.path.exists(chrome_path):
                    break
            else:
                raise RuntimeError("Please add chrome install path to PATH environment")
            args = [
                "chrome",
                "--window-size=1920,1080",
                "--ignore-certificate-errors",
                "--user-data-dir=%s" % user_data_dir,
                "--remote-debugging-port=%d" % self._port,
            ]
            if proxy_server:
                args.append("--proxy-server=%s" % proxy_server)
            if os.environ.get("QT4W_DEBUG") != "1":
                args.insert(1, "--headless")
            args.append(url)
        elif sys.platform == "darwin":
            args = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "--window-size=1920,1080",
                "--ignore-certificate-errors",
                "--user-data-dir=%s" % user_data_dir,
                "--no-default-browser-check",
                "--no-first-run",
                "--remote-debugging-port=%d" % self._port,
            ]
            if proxy_server:
                args.append("--proxy-server=%s" % proxy_server)
            if os.environ.get("QT4W_DEBUG") != "1":
                args.insert(1, "--headless")
            args.append(url)
        else:
            args = [
                "chrome",
                "--headless",
                "--disable-gpu",
                "--ignore-certificate-errors",
                "--single-process",
                "--disable-dev-shm-usage",
                "--window-size=1920,1080",
                "--user-data-dir=%s" % user_data_dir,
                "--remote-debugging-port=%d" % self._port,
            ]
            if not os.environ.get("CHROME_DEVEL_SANDBOX"):
                args.append("--no-sandbox")
                args.append("--disable-setuid-sandbox")
            if proxy_server:
                args.append("--proxy-server=%s" % proxy_server)
            args.append(url)

            if os.getuid() == 0 and os.environ.get("CHROME_DEVEL_SANDBOX"):
                # Use chrome user to start process
                username = "chrome"
                try:
                    import pwd
                    pwd.getpwnam(username)
                except KeyError:
                    os.system("useradd %s" % username)
                args = ["su", username, "-c", " ".join(args)]
        
        if kwargs.get("extra_params", None):
            for item in kwargs["extra_params"]:
                if item not in args:
                    args.append(item)
        
        logging.info("Start chrome with cmdline %s" % (" ".join(args)))

        proc = subprocess.Popen(args, close_fds=True)  # shell=True,
        timeout = 10
        time0 = time.time()
        while time.time() - time0 < timeout:
            if self.check_server(self._port):
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("Start chrome failed")
        webview = ChromeHeadlessWebView(self._port)
        if webview not in self._webviews:
            self._webviews.append(webview)
        return (page_cls or WebPage)(webview)

    def find_by_url(self, url, page_cls=None, timeout=10):
        """在当前打开的页面中查找指定url,返回page_cls类的实例，如果未找到，返回None

        :param url: 要查找的页面url
        :type url:  string
        :param page_cls: 要返回的具体WebPage类,为None表示返回WebPage实例
        :type page_cls: Class
        :param timeout: 查找超时时间，单位：秒
        :type timeout: int/float
        """
        webview = ChromeHeadlessWebView(self._port, url=url, timeout=timeout)
        if webview not in self._webviews:
            self._webviews.append(webview)
        return (page_cls or WebPage)(webview)

    def _get_process_list(self):
        process_list = []
        if sys.platform == "linux2":
            root = "/proc"
            for it in os.listdir(root):
                if not it.isdigit():
                    continue

                exe_path = os.path.join(root, it, "exe")
                try:
                    exe_path = os.readlink(exe_path)
                except OSError as ex:
                    logging.warn(
                        "[%s] Read link %s failed: %s"
                        % (self.__class__.__name__, exe_path, ex)
                    )
                    continue
                cmdline_path = os.path.join(root, it, "cmdline")
                with open(cmdline_path, "r") as fp:
                    cmdline = fp.read()
                status_path = os.path.join(root, it, "status")
                with open(status_path, "r") as fp:
                    status = fp.read()
                ppid = 0
                for line in status.split("\n"):
                    items = line.split(":")
                    if len(items) > 1 and items[0] == "PPid":
                        ppid = int(items[1].strip())
                        break
                process_list.append(
                    {
                        "pid": int(it),
                        "ppid": ppid,
                        "exe_path": exe_path,
                        "cmdline": " ".join(cmdline[:-1].split("\x00")),
                    }
                )
        return process_list

    def close(self):
        """close browser"""
        if self in ChromeHeadlessBrowser.instances:
            ChromeHeadlessBrowser.instances.remove(self)

        process_list = self._get_process_list()
        chrome_pid = 0
        for process in process_list:
            if (
                process["cmdline"].startswith("chrome")
                and ("--remote-debugging-port=%d" % self._port) in process["cmdline"]
            ):
                chrome_pid = process["pid"]
                break
        if not chrome_pid:
            logging.warn(
                "[%s] Find chrome process with port %d failed"
                % (self.__class__.__name__, self._port)
            )
            return
        pid_list = [chrome_pid]
        for process in process_list:
            if process["ppid"] == chrome_pid:
                pid_list.append(process["pid"])
        for pid in pid_list:
            os.kill(pid, 9)

    def clearcache(self):
        """清理缓存"""
        user_data_dir = self.user_data_dir_tmpl % self._port
        if os.path.isdir(user_data_dir):
            shutil.rmtree(user_data_dir)

    @staticmethod
    def killall():
        """close all browsers"""
        if sys.platform == "win32":
            cmdline = "taskkill /F /IM chrome.exe"
        else:
            cmdline = "pkill -9 -f chrome"
        os.system(cmdline)

    @staticmethod
    def clearall():
        """clear all cache"""
        if sys.platform == "win32":
            root = os.environ["TEMP"]
        else:
            root = "/tmp"
        for it in os.listdir(root):
            path = os.path.join(root, it)
            if not os.path.isdir(path):
                continue
            if not it.startswith("Chrome_"):
                continue
            shutil.rmtree(path)
