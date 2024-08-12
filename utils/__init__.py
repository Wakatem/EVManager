
from .db_manager import DBManager
from .states import States
import random
import string

def generate_id(prefix=None, length=6):
    if prefix:
        return prefix + "#" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

