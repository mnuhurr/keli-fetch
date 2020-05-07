# keli-fetch

Utility functions to fetch Finnish weather data.

#### Requirements
- urllib3

#### Usage
FMI (Ilmatieteen laitos) data can be downloaded by using the weather station id.

```python
weather_info = weather_fmi(151049) # Tampella station
```

Downloading Foreca data requires a place string and a station id
```python
weather_info = weather_foreca('Tampere', 1020002763) # Härmälä station
```

Foreca stations can be listed with

```python
stations = foreca_stations('Tampere')
```
