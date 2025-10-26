const map = L.map('map').setView([48.8566,2.3522], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19
}).addTo(map);

document.getElementById("plan").onclick = async () => {
  const lat = parseFloat(document.getElementById("lat").value);
  const lon = parseFloat(document.getElementById("lon").value);
  const body = {
    city: document.getElementById("city").value,
    lat, lon, days:1, budget_per_day:80, interests:["Culture"], start_time:"09:00", end_time:"18:00"
  };
  const res = await fetch("/api/plan", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(body)
  });
  const js = await res.json();
  document.getElementById("output").innerText = JSON.stringify(js.itinerary, null, 2);
  // plot markers
  js.itinerary.forEach(item => {
    L.marker([item.lat, item.lon]).addTo(map)
      .bindPopup(`<b>${item.name}</b><br>${item.arrival} - ${item.departure}`);
  });
  map.setView([lat, lon], 13);
};