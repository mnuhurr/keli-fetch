"""
download weather data from fmi & foreca

"""

from datetime import datetime, timezone
import urllib3
import json
import re

def fetch_page(url: str) -> str:
    """
    download a web page.
    :param url:
    :return: page contents
    :rtype: str
    """

    http = urllib3.PoolManager()
    resp = http.request('GET', url)

    if resp.status == 200:
        return resp.data.decode('utf-8')
    else:
        return None
        #print('got status {status}: {r}'.format(status=resp.status, r=resp.data))



def jsonify(s: str) -> str:
    """
    javascript var -> json, i.e. add quotation to dict keys

    :param s:
    :return:
    """

    # do some small cleanings
    s = s.replace('\t', ' ').replace('\'', '"')

    # regexps to match for variable names and null values
    patt = re.compile(r'(\w+)(:)')
    null_replace = re.compile(r' (null)([\,\}])')

    rs = patt.sub(r'"\1"\2', s)
    rs = null_replace.sub(r' 0\2', rs)

    return rs



def weather_fmi(station_id: int, timestamp_key='time', temperature_key='temp', humidity_key='hum'):
    """
    fetch latest observation from ilmatieteenlaitos

    :param station: fmi station id
    :param timestamp_key: key to use for timestamp in the returned data
    :param temperature_key: key to use for temperature in the returned data
    :param humidity_key: key to use for humidity in the returned data
    :return: dict of weather data
    """
    url = 'https://www.ilmatieteenlaitos.fi/api/weather/observations?fmisid={}&observations=true'.format(station_id)
    data = fetch_page(url)
    weather = json.loads(data)

    observations = []
    for observation in weather['observations']:
        if observation['t2m'] is not None:
            tstp = datetime.strptime(observation['localtime'], '%Y%m%dT%H%M%S')
            temp = observation['t2m']
            hum = observation['Humidity']
            observations.append([tstp, temp, hum])

    info = {}

    if len(observations) == 0:
        return info

    observations.sort()

    last_observation = observations[-1]
    info[timestamp_key] = last_observation[0]
    info[temperature_key] = float(last_observation[1])
    info[humidity_key] = float(last_observation[2])
        
    return info


def weather_foreca(locality: str, timestamp_key='time', temperature_key='temp', humidity_key='hum'):
    """
    fetch latest observation from foreca. this function needs the station id and corresponding locality.

    :param locality: place (e.g. Helsinki)
    :param timestamp_key: key to use for timestamp in the returned data
    :param temperature_key: key to use for temperature in the returned data
    :param humidity_key: key to use for humidity in the returned data
    :return: dict of weather data for all stations of the given locality
    """
    url = 'https://www.foreca.fi/Finland/' + locality
    data = fetch_page(url)

    if data is None or 'var observations =' not in data:
        return info

    # this needs a bit of hand work.
    # 1) get the observations dict code
    idx_start = data.find('var observations =') + 19
    idx_end = data.find('};', idx_start) + 1

    # 2) correct it a bit to make it proper json
    obs_str = jsonify(data[idx_start:idx_end])

    # 3) parse json object
    observations = json.loads(obs_str)

    info = {}
    for st_id in observations:
        info[st_id] = {}

        obs = observations[st_id]

        # parse datetime
        yr = datetime.today().year
        dstr = str(yr) + ' ' + obs['date'] + ' ' + obs['time']
        dt = datetime.strptime(dstr, '%Y %d.%m. %H.%M')

        info[st_id][timestamp_key] = dt
        info[st_id][temperature_key] = obs['temp']
        info[st_id][humidity_key] = obs['rhum']

    return info


def foreca_stations(locality: str):
    """
    Find weather stations for a given locality.

    :param locality: place (e.g. Helsinki)
    :return: dict of station_id: station_name pairs
    :rtype: Dict[key, str]
    """
    url = 'https://www.foreca.fi/Finland/' + locality
    data = fetch_page(url)

    if data is None or 'var stations =' not in data:
        return None

    # 1) get the observations dict code
    idx_start = data.find('var stations =') + 14
    idx_end = data.find('}];', idx_start) + 2

    # 2) correct it a bit to make it proper json
    obs_str = jsonify(data[idx_start:idx_end])

    # 3) parse json object
    stations = json.loads(obs_str)

    info = {}

    # 4) build a dict: id as key, name as value
    for stat in stations:
        stat_id = stat['id']
        name = stat['n']

        info[stat_id] = name

    return info


