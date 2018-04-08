import ConfigParser
import inspect
import os

filename = inspect.getframeinfo(inspect.currentframe()).filename
file_directory = os.path.dirname(os.path.abspath(filename))

def get_config():
    config_name = 'pennyaday.conf'
    conf = ConfigParser.ConfigParser()
    conf.read(os.path.join(file_directory, '{}.example'.format(config_name)))
    conf.read(os.path.join(file_directory, config_name))
    return conf

__all__ = ['get_config']
