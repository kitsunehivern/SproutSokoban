import threading
import ctypes


class StoppableThread:
    def __init__(self, target):
        self.target = target
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self.target)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if self.thread and self.thread.is_alive():
            self._raise_exception(SystemExit)

    def _raise_exception(self, exception_type):
        thread_id = self.thread.ident
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread_id), ctypes.py_object(exception_type)
        )

        if res == 0:
            raise ValueError("Invalid thread ID")
        elif res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            raise SystemError("Exception raise failure")
