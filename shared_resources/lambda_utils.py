import os
import shutil
from datetime import datetime, timezone

def clear_tmp():
    for file_name in os.listdir('/tmp'):
        file_path = '/tmp/' + file_name
        if os.path.isfile(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
