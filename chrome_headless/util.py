# -*- coding: utf-8 -*-

'''公共函数库
'''

import sys


def general_encode(s):
    '''字符串通用编码处理
    python2 => utf8
    python3 => unicode
    '''
    is_py3 = sys.version_info[0] == 3
    if not is_py3 and isinstance(s, (unicode, )):
        s = s.encode('utf8')
    elif is_py3 and isinstance(s, (bytes,)):
        s = s.decode('utf8')
    return s
