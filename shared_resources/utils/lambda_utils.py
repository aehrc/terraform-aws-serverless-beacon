import contextlib
import os
import shutil
import tempfile


def clear_tmp():
    for file_name in os.listdir("/tmp"):
        file_path = "/tmp/" + file_name
        if os.path.isfile(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)


@contextlib.contextmanager
def make_temp_file():
    # the race condition does not affect
    # lambdas as only one request processed at
    # any given time
    tempf = tempfile.mktemp()
    try:
        yield tempf
    finally:
        os.unlink(tempf)
