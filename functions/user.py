import os, sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(here)

from models import User
from db_util import DatabaseManager

