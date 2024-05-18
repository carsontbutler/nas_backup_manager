import logging
import datetime
today = datetime.datetime.now().date()
logger = logging.getLogger()
FORMAT = ('%(asctime)s (%(levelname)s)'
          '%(filename)s::%(funcName)s() - %(message)s')
logging.basicConfig(filename=f'logs/{today}.log',
                    level=logging.INFO,
                    format=FORMAT,
                    datefmt='%Y-%m-%d %H:%M:%S')
