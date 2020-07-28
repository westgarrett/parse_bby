####################################################################################################################
# Tool Functions                                                                                                   #
####################################################################################################################
import time


def function_timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        x = func(*args, **kwargs)
        end = time.time()
        print(f"It took {end - start} seconds to process {func.__name__} for {args[0]}")
        return x

    return wrapper
