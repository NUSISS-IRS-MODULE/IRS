# rasa/actions/actions.py
from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import requests
import re
import os
import json

# ✅ Import central config (loads .env variables)
from config import Config

FLASK_URL = os.getenv("SMART_TOURISM_BACKEND", "http://localhost:5000/api/plan")

def try_extract_coords(text: str):
    """
    Look for 'lat:xx, lon:yy' OR 'xx,yy' patterns.
    """
    m = re.search(r"lat[: ]?(-?\d+\.\d+)[, ]+lon[: ]?(-?\d+\.\d+)", text, re.I)
    if m:
        return float(m.group(1)), float(m.group(2))
    # format: 48.8566,2.3522
    m2 = re.search(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", text)
    if m2:
        return float(m2.group(1)), float(m2.group(2))
    return None


def parse_budget(text: str) -> Optional[float]:
    m = re.search(r"\$?(\d+)", text)
    if m:
        try:
            return float(m.group(1))
        except:
            return None
    return None

def parse_days(text: str) -> Optional[int]:
    m = re.search(r"(\d+)\s*(day|days)", text)
    if m:
        return int(m.group(1))
    # also single-digits without word
    m2 = re.search(r"\b(\d+)\b", text)
    if m2:
        return int(m2.group(1))
    return None

class ActionPlanTrip(Action):
    def name(self) -> Text:
        return "action_plan_trip"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Prefer slots -> last user message -> defaults
        last_msg = tracker.latest_message.get('text') or ""
        city = tracker.get_slot("city") or None
        lat = tracker.get_slot("lat") or None
        lon = tracker.get_slot("lon") or None
        days = tracker.get_slot("days") or None
        budget = tracker.get_slot("budget") or None
        interests = tracker.get_slot("interests") or None

        # try parse from last message if missing
        if not (lat and lon):
            coords = try_extract_coords(last_msg)
            if coords:
                lat, lon = coords

        if not days:
            days = parse_days(last_msg) or 1
        if not budget:
            budget = parse_budget(last_msg) or None
        if not interests:
            # try to find keywords after "interests" or "for"
            m = re.search(r"interests?:\s*([A-Za-z, ]+)", last_msg)
            if m:
                interests = [s.strip() for s in m.group(1).split(",")]
            else:
                # fallback simple heuristics
                if "kids" in last_msg.lower():
                    interests = ["Kids"]
                elif "culture" in last_msg.lower() or "museum" in last_msg.lower():
                    interests = ["Culture"]
                else:
                    interests = []

        # If city provided but no coords, we'll try GeoNames
        if city and not (lat and lon):
            try:
                if Config.GEONAMES_USERNAME:   # ✅ use config.py
                    params = {"q": city, "maxRows": 1, "username": Config.GEONAMES_USERNAME}
                    r = requests.get("http://api.geonames.org/searchJSON", params=params, timeout=6)
                    data = r.json()
                    if data.get("geonames"):
                        g = data["geonames"][0]
                        lat = float(g["lat"])
                        lon = float(g["lng"])
            except Exception:
                pass

        # Final payload for backend
        try:
            budget_value = float(budget) if budget else None
        except (ValueError, TypeError):
            budget_value = None

        payload = {
            "city": city,
            "lat": lat,
            "lon": lon,
            "days": days or 1,
            "budget_per_day": budget,
            "interests": interests or [],
            "start_time": "09:00",
            "end_time": "18:00",
            "transport": "walking"
        }

        # Validate coords
        if (not lat) or (not lon):
            dispatcher.utter_message(
                text="I couldn't determine coordinates for that location. Could you provide city name or lat,lon?"
            )
            return []

        # Call backend
        try:
            r = requests.post(FLASK_URL, json=payload, timeout=600)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I had trouble planning the trip: {e}")
            return []

        # Build a short human summary
        itinerary = data.get("itinerary", [])
        if not itinerary:
            dispatcher.utter_message(
                text="I couldn't find a viable itinerary for those inputs. Try changing budget, location, or dates."
            )
            return []

        # ✅ Flatten first few POI names across days
        top_names = []
        for day in itinerary:
            for poi in day.get("plan", []):
                name = poi.get("name")
                if name:
                    top_names.append(name)
                if len(top_names) >= 4:
                    break
            if len(top_names) >= 4:
                break

        if top_names:
            summary = f"{sum(len(day.get('plan', [])) for day in itinerary)} places planned: " + ", ".join(top_names)
        else:
            summary = f"{sum(len(day.get('plan', [])) for day in itinerary)} places planned."



        dispatcher.utter_message(text=f"Plan ready! {summary}")
        dispatcher.utter_message(json_message={"itinerary": itinerary, "summary": summary})

        daywise_text = ""
        for day in itinerary:
            daywise_text += f"\nDay {day['day']}:\n"
            for stop in day["plan"]:
                daywise_text += f"  {stop['arrival']} - {stop['departure']}: {stop['name']}\n"

        dispatcher.utter_message(text="Here’s your itinerary:" + daywise_text)

        return [SlotSet("last_plan", itinerary)]