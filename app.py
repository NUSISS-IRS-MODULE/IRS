from flask import Flask, request, jsonify, render_template
from data_clients import OpenTripMapClient, OpenWeatherClient, GeoNamesClient
from recommender import filter_pois, recommend_pois
from optimizer import ItineraryGA
from config import Config
from flask_cors import CORS
import os
import requests

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)
app.config.from_object("config.Config")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    rasa_url = "http://localhost:5005/webhooks/rest/webhook"
    try:
        r = requests.post(rasa_url, json=data, timeout=600)
        return jsonify(r.json())
    except Exception as e:
        return jsonify([{"text": f"Error connecting to Rasa: {str(e)}"}])



@app.route("/api/plan", methods=["POST"])
def plan_trip():
    payload = request.get_json()
    if payload is None:
        return jsonify({"error": "Invalid JSON"}), 400

    city = payload.get("city", "")
    lat = payload.get("lat")
    lon = payload.get("lon")

    # Auto-fetch lat/lon from GeoNames if missing
    city = payload.get("city")

    # 🔍 If no lat/lon provided, fetch coordinates from city name
    if (not lat or not lon) and city:
        try:
            # Option 1: Using your GeoNamesClient
            geoinfo = GeoNamesClient.get_coords(city)

            # Option 2: If your GeoNamesClient lacks get_coords, use OpenTripMap as fallback
            if not geoinfo or "lat" not in geoinfo:
                geoinfo = OpenTripMapClient.geoname_lookup(city)

            lat = geoinfo.get("lat")
            lon = geoinfo.get("lon")
        except Exception as e:
            return jsonify({
                "error": f"Failed to get coordinates for {city}",
                "details": str(e)
            }), 400

    # If still None, reject request
    if not lat or not lon:
        return jsonify({
            "error": "No coordinates found. Please provide a valid city name or lat/lon."
        }), 400


    days = int(payload.get("days", 1))
    user_profile = {
        "budget_per_day": payload.get("budget_per_day"),
        "interests": payload.get("interests", []),
        "preferred_kinds": ",".join(payload.get("preferred_kinds", [])),
        "start_time": payload.get("start_time", "09:00"),
        "end_time": payload.get("end_time", "18:00"),
        "transport": payload.get("transport", "walking"),
    }

    # 1) Fetch POIs
    try:
        raw = OpenTripMapClient.radius_places(lat, lon, radius=Config.DEFAULT_RADIUS, limit=150)
    except Exception as e:
        return jsonify({"error": "Failed to fetch POIs", "details": str(e)}), 502

    pois = []
    for item in raw.get("features", [])[:150]:
        xid = item["properties"].get("xid") or item.get("id")
        if not xid:
            continue
        try:
            detail = OpenTripMapClient.get_place(xid)
        except Exception:
            continue

        # ✅ normalize important fields
        point = detail.get("point") or item.get("geometry", {}).get("coordinates")
        if isinstance(point, list) and len(point) == 2:
            lon, lat = point[0], point[1]
        else:
            lat = detail.get("point", {}).get("lat")
            lon = detail.get("point", {}).get("lon")

        name = detail.get("name")
        if not name:   # 🚫 skip unnamed places
            continue

        poi = {
            "xid": detail.get("xid"),
            "name": name,
            "kinds": detail.get("kinds", ""),
            "lat": float(lat) if lat else None,
            "lon": float(lon) if lon else None,
            "wikipedia_extracts": detail.get("wikipedia_extracts", {}),
            "info": detail.get("info", {}),
        }

        print(f"✅ Added POI: {poi['name']} ({poi['lat']}, {poi['lon']})")
        pois.append(poi)



    # 2) Get weather (optional)
    try:
        weather = OpenWeatherClient.onecall(lat, lon, exclude=["minutely", "alerts"])
    except Exception:
        weather = None

    # 3) Filter + recommend
    filtered = filter_pois(pois, user_profile, weather_info=weather)
    recs = recommend_pois(filtered, user_profile, top_n=80)

    for r in recs:
        lat = (
            r.get("lat")
            or r.get("latitude")
            or (r.get("point") or {}).get("lat")
            or (r.get("geometry", {}).get("coordinates")[1] if r.get("geometry", {}).get("coordinates") else None)
        )
        lon = (
            r.get("lon")
            or r.get("longitude")
            or (r.get("point") or {}).get("lon")
            or (r.get("geometry", {}).get("coordinates")[0] if r.get("geometry", {}).get("coordinates") else None)
        )

        try:
            r["lat"] = float(lat) if lat not in (None, 0, "0", "0.0") else None
            r["lon"] = float(lon) if lon not in (None, 0, "0", "0.0") else None
        except Exception:
            r["lat"], r["lon"] = None, None

        r["score"] = float(r.get("score") or 0)


    # 4) Multi-day itinerary
    split_size = max(1, len(recs) // days)
    itineraries = []
    for i in range(days):
        day_pois = recs[i * split_size : (i + 1) * split_size]
        if not day_pois:
            continue
        ga = ItineraryGA(day_pois, user_profile,
                         pop_size=Config.GA_POP_SIZE,
                         generations=Config.GA_GENERATIONS,
                         mutation_rate=Config.GA_MUTATION_RATE)
        day_plan = ga.run()
        itineraries.append({
            "day": i + 1,
            "plan": day_plan
        })

    response = {
        "city": city,
        "days": days,
        "itinerary": itineraries,
        "top_recommendations": recs[:20],
        "weather": weather
    }
    return jsonify(response)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
