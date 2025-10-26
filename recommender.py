import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from data_clients import OpenTripMapClient, OpenWeatherClient
from geopy.distance import geodesic
import datetime

# Preference & Rule-based filtering
def filter_pois(pois, user_profile, weather_info=None):
    """
    pois: list of dicts (from OpenTripMap)
    user_profile: dict {interests: [..], budget_per_day: float, mobility: 'car'/'walking' }
    weather_info: optional weather data from OpenWeather onecall
    """

    # 🔧 Normalize budget to float
    budget = user_profile.get("budget_per_day")
    try:
        budget = float(budget) if budget is not None else None
    except (ValueError, TypeError):
        budget = None

    filtered = []
    for p in pois:
        kind = p.get("kinds", "")
        name = p.get("name", "")
        dist = p.get("dist", 0)

        # Example: exclude outdoor in heavy rain/storm
        if weather_info:
            try:
                pop = weather_info.get("daily", [])[0].get("pop", 0)
            except Exception:
                pop = 0
            outdoor_kinds = ["natural", "beaches", "sport", "garden", "zoo"]
            if pop > 0.6 and any(o in kind for o in outdoor_kinds):
                continue

        # Budget heuristic
        if budget is not None:
            if "hotel" in kind and budget < 50:
                continue

        filtered.append(p)
    return filtered


# Content-based scoring using description + kinds + name
def build_poi_dataframe(pois):
    rows = []
    for p in pois:
        desc = (
            p.get("wikipedia_extracts", {}).get("text", "")
            or p.get("info", {}).get("descr", "")
            or ""
        )
        kinds = p.get("kinds", "")

        # ✅ Prefer normalized lat/lon if available
        lat = p.get("lat") or (p.get("point") or {}).get("lat")
        lon = p.get("lon") or (p.get("point") or {}).get("lon")

        rows.append({
            "xid": p.get("xid"),
            "name": p.get("name"),
            "lat": lat,
            "lon": lon,
            "kinds": kinds,
            "description": desc,
            "raw": p   # keep full POI reference
        })
    return pd.DataFrame(rows)


def recommend_pois(filtered_pois, user_profile, top_n=12):
    """
    content-based: combine name + kinds + description, TF-IDF and cosine with user 'pseudo-document'
    """
    df = build_poi_dataframe(filtered_pois)
    if df.empty:
        return []
    docs = (df["name"].fillna("") + " " + df["kinds"].fillna("") + " " + df["description"].fillna("")).tolist()
    vectorizer = TfidfVectorizer(max_features=1500, stop_words="english")
    X = vectorizer.fit_transform(docs)
    # Create user profile document
    up_doc = " ".join(user_profile.get("interests", [])) + " " + user_profile.get("preferred_kinds", "")
    up_vec = vectorizer.transform([up_doc])
    cosine_sim = linear_kernel(up_vec, X).flatten()
    df["score"] = cosine_sim
    df = df.sort_values("score", ascending=False)
    return df.head(top_n).to_dict(orient="records")

# Utility
def travel_time_minutes(a_lat, a_lon, b_lat, b_lon, mode="walking"):
    # naive: geodesic distance / speed
    dist_km = geodesic((a_lat, a_lon), (b_lat, b_lon)).km
    if mode == "driving":
        speed_kmh = 40
    else:
        speed_kmh = 5
    return (dist_km / speed_kmh) * 60