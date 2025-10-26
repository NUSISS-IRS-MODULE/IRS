import requests
from urllib.parse import urlencode
from config import Config
import time

class OpenTripMapClient:
    BASE = "https://api.opentripmap.com/0.1/en/places"
    KEY = Config.OPENTRIPMAP_KEY

    @staticmethod
    def radius_places(lat, lon, radius=2000, kinds=None, limit=50, rate=None):
        """
        Fetch list of POIs around coordinates using OpenTripMap /radius method.
        """
        params = {
            "apikey": OpenTripMapClient.KEY,
            "radius": int(radius),
            "lon": lon,
            "lat": lat,
            "limit": int(limit)
        }
        if kinds:
            params["kinds"] = kinds
        if rate is not None:
            params["rate"] = rate
        url = f"{OpenTripMapClient.BASE}/radius?{urlencode(params)}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_place(xid):
        url = f"{OpenTripMapClient.BASE}/xid/{xid}?apikey={OpenTripMapClient.KEY}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()

class OpenWeatherClient:
    CURRENT = "https://api.openweathermap.org/data/2.5/weather"
    FORECAST = "https://api.openweathermap.org/data/2.5/forecast"
    ONECALL = "https://api.openweathermap.org/data/3.0/onecall"

    KEY = Config.OPENWEATHER_KEY

    @staticmethod
    def current_by_coords(lat, lon):
        params = {"lat": lat, "lon": lon, "appid": OpenWeatherClient.KEY, "units": "metric"}
        resp = requests.get(OpenWeatherClient.CURRENT, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def forecast_by_coords(lat, lon):
        params = {"lat": lat, "lon": lon, "appid": OpenWeatherClient.KEY, "units": "metric"}
        resp = requests.get(OpenWeatherClient.FORECAST, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def onecall(lat, lon, exclude=None):
        params = {"lat": lat, "lon": lon, "appid": OpenWeatherClient.KEY, "units": "metric"}
        if exclude:
            params["exclude"] = ",".join(exclude)
        resp = requests.get(OpenWeatherClient.ONECALL, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

class GeoNamesClient:
    BASE = "http://api.geonames.org"
    USER = Config.GEONAMES_USERNAME

    @staticmethod
    def search_place(name, maxRows=10):
        params = {"q": name, "maxRows": maxRows, "username": GeoNamesClient.USER}
        resp = requests.get(f"{GeoNamesClient.BASE}/searchJSON", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def reverse_geocode(lat, lon):
        params = {"lat": lat, "lng": lon, "username": GeoNamesClient.USER}
        resp = requests.get(f"{GeoNamesClient.BASE}/findNearbyJSON", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    
    @staticmethod
    def get_coords(city):
        import requests
        from config import Config
        url = f"http://api.geonames.org/searchJSON?q={city}&maxRows=1&username={Config.GEONAMES_USERNAME}"
        resp = requests.get(url).json()
        if resp.get("geonames"):
            g = resp["geonames"][0]
            return {"lat": g["lat"], "lon": g["lng"]}
        return {}

