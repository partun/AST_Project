import time
import signal


class TimeoutException(Exception):
    pass


def set_timeout(timeout: int):
    def alarm_handler(signum, frame):
        raise TimeoutException()

    def set_timeout_decorator(func):
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, alarm_handler)
            signal.alarm(timeout)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wrapper
    return set_timeout_decorator


def wrap_with_timeout(func, timeout: int):
    def alarm_handler(signum, frame):
        raise TimeoutException()

    def wrapper(*args, **kwargs):
        signal.signal(signal.SIGALRM, alarm_handler)
        signal.alarm(timeout)
        try:
            result = func(*args, **kwargs)
        finally:
            signal.alarm(0)
        return result

    return wrapper



# @set_timeout(5)
# def loop(n):
#     for sec in range(n):
#         print("sec {}".format(sec))
#         time.sleep(1)
#
# def loop2(n):
#     for sec in range(n):
#         print("sec {}".format(sec))
#         time.sleep(1)
#     return True
#
# @set_timeout(3)
# def long_function():
#     x = 0
#     for i in range(1_000_000_000):
#         x += i
#
#
# def test():
#
#     loop(4)
#
#     print(loop2(10))
#
# if __name__ == '__main__':
#     test()