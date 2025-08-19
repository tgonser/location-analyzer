import os
import json
import time
import requests
import math

geo_cache = {}
cache_file = "config/geo_cache.json"
if os.path.exists(cache_file):
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            geo_cache = json.load(f)
        print(f"Loaded {len(geo_cache)} cache entries from {cache_file}")
    except Exception as e:
        print(f"⚠️ Failed to load config/geo_cache.json: {e}")

def save_geo_cache():
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(geo_cache, f)
        print(f"Saved {len(geo_cache)} cache entries to {cache_file}")
    except Exception as e:
        print(f"⚠️ Failed to save config/geo_cache.json: {e}")

def reverse_geocode(lat, lon, geoapify_key, google_key, delay=0.5, log_func=None):
    key = f"{round(lat, 5)},{round(lon, 5)}"
    key_fallback = f"{round(lat, 4)},{round(lon, 4)}"  # Fallback for old cache
    if key in geo_cache:
        if log_func:
            log_func(f"📍 HIT: ({lat:.5f}, {lon:.5f}) => {geo_cache[key]}")
        return geo_cache[key]
    if key_fallback in geo_cache:
        if log_func:
            log_func(f"📍 HIT (fallback): ({lat:.5f}, {lon:.5f}) => {geo_cache[key_fallback]}")
        return geo_cache[key_fallback]

    if log_func:
        log_func(f"🌐 MISS: ({lat:.5f}, {lon:.5f}) → API call")

    result = {}
    if geoapify_key:
        url = f"https://api.geoapify.com/v1/geocode/reverse?lat={lat}&lon={lon}&apiKey={geoapify_key}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            features = data.get("features", [])
            if features:
                props = features[0].get("properties", {})
                place_name = props.get("name", "").lower()
                result = {
                    "state": props.get("state"),
                    "city": props.get("city", props.get("county")),
                    "country": props.get("country"),
                    "place": place_name,
                    "is_water": (props.get("category") == "natural" and props.get("class") == "water") or
                                any(w in place_name for w in ["waters", "sea", "ocean", "bay", "channel"])
                }
            else:
                result = {"is_water": True, "place": "open water"}
        except Exception as e:
            if log_func:
                log_func(f"Geoapify error for ({lat:.5f}, {lon:.5f}): {e}")

    if not result and google_key:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={google_key}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "OK":
                result = {
                    "state": None,
                    "city": None,
                    "country": None,
                    "place": "",
                    "is_water": False
                }
                for comp in data["results"][0]["address_components"]:
                    if "administrative_area_level_1" in comp["types"]:
                        result["state"] = comp["long_name"]
                    if "locality" in comp["types"]:
                        result["city"] = comp["long_name"]
                    if "country" in comp["types"]:
                        result["country"] = comp["long_name"]
                if not result["city"]:
                    for comp in data["results"][0]["address_components"]:
                        if "administrative_area_level_2" in comp["types"]:
                            result["city"] = comp["long_name"]
                if "natural_feature" in data["results"][0]["types"]:
                    result["is_water"] = True
                result["place"] = data["results"][0].get("formatted_address", "").lower()
            elif data.get("status") == "ZERO_RESULTS":
                result = {"is_water": True, "place": "open water"}
        except Exception as e:
            if log_func:
                log_func(f"Google Maps error for ({lat:.5f}, {lon:.5f}): {e}")

    geo_cache[key] = result
    save_geo_cache()

    if delay:
        time.sleep(delay)

    return result

def is_over_water(lat, lon, onwater_key, delay=0.5, log_func=None, geoapify_key="", google_key=""):
    """
    Checks if a point is over water using OnWater API with retry logic.
    Falls back to Geoapify/Google if OnWater fails.
    Returns True if over water, False if land, None on error.
    """
    key = f"water:{round(lat, 5)},{round(lon, 5)}"
    key_fallback = f"water:{round(lat, 4)},{round(lon, 4)}"
    if key in geo_cache:
        if log_func:
            log_func(f"🌊 HIT: ({lat:.5f}, {lon:.5f}) => {'Water' if geo_cache[key] else 'Land'}")
        return geo_cache[key]
    if key_fallback in geo_cache:
        if log_func:
            log_func(f"🌊 HIT (fallback): ({lat:.5f}, {lon:.5f}) => {'Water' if geo_cache[key_fallback] else 'Land'}")
        return geo_cache[key_fallback]

    if not onwater_key:
        if log_func:
            log_func("⚠️ OnWater API key missing; falling back to Geoapify/Google.")
        result = reverse_geocode(lat, lon, geoapify_key, google_key, delay, log_func)
        is_water = result.get("is_water", False)
        geo_cache[key] = is_water
        save_geo_cache()
        return is_water

    url = f"https://isitwater-com.p.rapidapi.com/?latitude={lat}&longitude={lon}"
    headers = {
        "x-rapidapi-key": onwater_key,
        "x-rapidapi-host": "isitwater-com.p.rapidapi.com"
    }
    retries = 3
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            is_water = data.get("water", False)
            geo_cache[key] = is_water
            save_geo_cache()
            if log_func:
                log_func(f"🌊 Water check for ({lat:.5f}, {lon:.5f}): {'Water' if is_water else 'Land'}")
            if delay:
                time.sleep(delay)
            return is_water
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                if log_func:
                    log_func(f"OnWater rate limit hit for ({lat:.5f}, {lon:.5f}); retrying in {2**attempt}s")
                time.sleep(2**attempt)
                continue
            elif response.status_code == 403:
                if log_func:
                    log_func(f"OnWater forbidden error for ({lat:.5f}, {lon:.5f}): {e}. Check API key validity.")
                break
            if log_func:
                log_func(f"OnWater error for ({lat:.5f}, {lon:.5f}): {e}")
            break
        except Exception as e:
            if log_func:
                log_func(f"OnWater error for ({lat:.5f}, {lon:.5f}): {e}")
            break

    if log_func:
        log_func(f"⚠️ OnWater failed for ({lat:.5f}, {lon:.5f}); falling back to Geoapify/Google")
    result = reverse_geocode(lat, lon, geoapify_key, google_key, delay, log_func)
    is_water = result.get("is_water", False)
    geo_cache[key] = is_water
    save_geo_cache()
    return is_water

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 3958.8  # miles
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def load_cache():
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f)
