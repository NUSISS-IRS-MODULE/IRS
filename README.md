
---

# Smart Tourism Recommender with Itinerary Optimizer

## 🧩 Objective
Build an intelligent tourism system that recommends personalized places of interest (POIs) and generates optimized travel itineraries based on tourist preferences, time, budget, and location.

---

## 📌 Features & Workflow

### 1. Problem Definition & Requirements
- Personalized POI recommendations
- Budget-based filtering
- Time optimization
- Weather-aware scheduling
- Interactive chatbot interface (Rasa)

### 2. Data Collection & Integration
- **OpenTripMap API**: Place metadata (category, coordinates, rating)
- **OpenWeatherMap**: Current/forecast weather
- **GeoNames**: Location/geography data

### 3. Preference & Rule-Based Filtering
- User profile: age, interests, budget, trip duration
- Hard constraints: opening hours, travel time, cost, weather suitability
- Logical filtering and heuristics

### 4. Personalized POI Recommendation
- Content-based filtering (TF-IDF + cosine similarity)
- Collaborative filtering (optional)
- Ranking top-N POIs

### 5. Itinerary Optimization
- Genetic Algorithm (GA): sequence and timing of POIs
- Fitness: maximize satisfaction, minimize travel time/cost
- Constraints: opening hours, travel time, daily limits

### 6. Chatbot Interface (Rasa)
- Natural language queries (e.g., "Plan a 3-day trip to Paris under $500")
- Intents: plan_trip, recommend_places, ask_weather
- Rasa custom action calls Flask backend

### 7. Evaluation & Testing
- Metrics: recommendation quality, optimization quality, user satisfaction, bot performance
- Unit, integration, and usability tests

### 8. UI / UX Design
- Map-based itinerary (Leaflet.js)
- Preference adjustment
- POI details, travel route, cost estimate

---

## 📊 Architecture Diagram
```
[User Input] ---> [Chatbot (Rasa)] ---> [Preference Engine]
                                                      ⬇
                                    [Recommendation Engine]
                                                      ⬇
                                    [Itinerary Optimizer (GA)]
                                                      ⬇
                                     [Data APIs: OpenTripMap, Weather, GeoNames]
                                                      ⬇
                                                   [Frontend UI]
```

---

## 🧰 Tools & Libraries
| Component         | Tool / Library                |
|-------------------|------------------------------|
| Data APIs         | OpenTripMap, OpenWeatherMap, GeoNames |
| NLP Interface     | Rasa, Dialogflow, HuggingFace |
| Recommendation    | Surprise, scikit-learn        |
| Optimization      | DEAP, PyGAD, custom GA        |
| Backend           | Flask / Django                |
| Frontend          | Leaflet.js, HTML/CSS/JS       |

---

## 🗂️ Project Structure
```
smart_tourism/
├─ app.py                      # Flask app (API + frontend)
├─ config.py                   # Configuration (API keys via env)
├─ data_clients.py             # API wrappers
├─ recommender.py              # Filtering + recommender
├─ optimizer.py                # Genetic Algorithm optimizer
├─ static/
│  ├─ main.css
│  └─ main.js
├─ templates/
│  └─ index.html
├─ tests/
│  └─ test_pipeline.py
├─ requirements.txt
├─ README.md
└─ rasa/
    ├─ config.yml
    ├─ domain.yml
    ├─ credentials.yml
    ├─ endpoints.yml
    ├─ data/
    │  ├─ nlu.yml
    │  ├─ stories.yml
    │  └─ rules.yml
    ├─ actions/
    │  └─ actions.py
    └─ requirements.txt
```

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/NUSISS-IRS-MODULE/IRS.git
cd IRS
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API Keys
Create a `.env` file in the project root:
```
OPENTRIPMAP_KEY=your_opentripmap_key
OPENWEATHER_KEY=your_openweather_key
GEONAMES_USERNAME=your_geonames_username
```

### 3. Run Flask Backend
```bash
python app.py
```
Access the UI at [http://127.0.0.1:5000](http://127.0.0.1:5000)

### 4. Run Rasa Chatbot
```bash
cd rasa
python -m venv venv-rasa
source venv-rasa/bin/activate
pip install -r requirements.txt
rasa train
rasa run actions --port 5055
rasa run --enable-api -p 5005
```

### 5. Test Chatbot
Send a message via REST:
```bash
curl -s -XPOST http://localhost:5005/webhooks/rest/webhook \
   -H "Content-Type: application/json" \
   -d '{"sender":"user1","message":"Plan a 2-day trip to Paris under $300"}'
```

### 6. Run Tests
```bash
pytest -q
```

---

## 📝 Notes & Next Steps
- **APIs & Keys**: Sign up for OpenTripMap, OpenWeather, and GeoNames; add keys to `.env`.
- **Recommendation**: Content-based filtering (TF-IDF); collaborative filtering can be added.
- **Optimization**: Custom GA; can be extended for multi-day trips and advanced routing.
- **Chatbot**: Rasa handles NLU/dialog; custom action calls Flask backend.
- **Frontend**: Minimal Leaflet map; can be upgraded to React or other SPA.
- **Scaling**: Add caching, rate-limiting, persistent user profiles, and advanced routing for production.

---

## 📚 References
- [OpenTripMap API](https://dev.opentripmap.org/)
- [OpenWeatherMap API](https://openweathermap.org/api)
- [GeoNames API](https://www.geonames.org/export/web-services.html)
- [Rasa Documentation](https://rasa.com/docs/)

---

## 🤝 Contributing
Contributions are welcome! Please open issues or submit pull requests for improvements, bug fixes, or new features.

## 📄 License
MIT License

## 📬 Contact
For questions or collaboration, please contact the repository owner or open an issue.