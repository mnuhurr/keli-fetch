"""
download weather data from fmi & foreca

"""

from datetime import datetime, timezone
import urllib3
import json
import re

def fetch_page(url) -> str:
    """
    download a web page.
    :param url:
    :return:
    """
    http = urllib3.PoolManager()
    hdrs = urllib3.make_headers(user_agent='Mozilla/5.0 (Windows NT 6.1; Win64; x64)')
    resp = http.request('GET', url, headers=hdrs)


    if resp.status == 200:
        return resp.data.decode('utf-8')
    else:
        return None
        #print('got status {status}: {r}'.format(status=resp.status, r=resp.data))




def weather_fmi(station: int, timestamp_key='time', temperature_key='temp', humidity_key='hum'):
    """
    fetch latest observation from ilmatieteenlaitos

    :param station: station id
    :return: dict
    """
    url = 'https://www.ilmatieteenlaitos.fi/observation-data?station=' + str(station)
    data = fetch_page(url)
    weather = json.loads(data)

    # collect everything to this
    info = {}

    # dump the history: we want the current data only
    obs_time = weather['latestObservationTime']

    # construct datetime object from the timestamp
    dt = datetime.fromtimestamp(obs_time // 1000, tz=timezone.utc).replace(tzinfo=None)

    info[timestamp_key] = dt

    # start gathering data
    if 't2m' in weather:
        for l in weather['t2m']:
            if l[0] == obs_time:
                info[temperature_key] = l[1]


    if 'Humidity' in weather:
        for l in weather['Humidity']:
            if l[0] == obs_time:
                info[humidity_key] = l[1]

    return info

def jsonify(s: str) -> str:
    """
    javascript var -> json, i.e. add quotation to dict keys

    :param s:
    :return:
    """
    s = s.replace('\t', '').replace('\'', '"')

    patt = re.compile(r'(\w+)(:)')
    null_replace = re.compile(r' (null)([\,\}])')

    rs = patt.sub(r'"\1"\2', s)
    rs = null_replace.sub(r' 0\2', rs)

    return rs

def weather_foreca(locality:str, stat: int, timestamp_key='time', temperature_key='temp', humidity_key='hum'):
    url = 'https://www.foreca.fi/Finland/' + locality
    data = fetch_page(url)

    info = {}

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

    if str(stat) in observations:
        ob = observations[str(stat)]

        # parse datetime
        yr = datetime.today().year
        dstr = str(yr) + ' ' + ob['date'] + ' ' + ob['time']
        dt = datetime.strptime(dstr, '%Y %d.%m. %H.%M')

        info[timestamp_key] = dt
        info[temperature_key] = ob['temp']
        info[humidity_key] = ob['rhum']
    return info

def foreca_stations(locality: str):
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

    for stat in stations:
        stat_id = int(stat['id'])
        name = stat['n']

        info[stat_id] = name

    return info



if __name__ == '__main__':
    # get weather data from ilmatieteen laitos
    weather_info = weather_fmi(151049) # tampella
    print(weather_info)

    # get weather data from foreca
    weather_info = weather_foreca('Tampere', 1020002763) # härmälä
    print(weather_info)

    # get stations from foreca
    stat_ids = foreca_stations('Tampere')
    print(stat_ids)