from configparser import ConfigParser
from typing import Dict


def load_config(filename: str ='database.ini', section: str ='postgresql') -> Dict[str, str]:
    parser = ConfigParser()
    parser.read(filename)
    # get section, default to postgresql
    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))
    
    return config

if __name__ == '__main__':
    config = load_config()
    print(config)