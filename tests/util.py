# -*- coding: utf-8 -*-


class MockHandler(object):

    def __func_wrapper(self, *args, **kwargs):
        pass

    def get_window_size(self):
        return 1280, 800

    def get_frame_tree(self):
        return {
            'frame': {
                'id': '1234567890',
                'url': 'http://www.foo.com/'
            },
            'childFrames': []
        }

    def eval_script(self, frame_id, script):
        if 'window.devicePixelRatio' in script:
            return '1'
        elif 'document.readyState' in script:
            return 'complete'
        else:
            raise NotImplementedError(script)

    def __getattr__(self, attr):
        return self.__func_wrapper


class MockDebugger(object):

    def __init__(self, *args, **kwargs):
        pass

    def register_handler(self, handler):
        pass

    @property
    def page(self):
        return MockHandler()
    
    @property
    def runtime(self):
        return MockHandler()
