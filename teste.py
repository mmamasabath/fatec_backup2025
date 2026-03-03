# ti_levu_rastreamento.py
# Requisitos: requests, bottle
# pip install requests bottle
from bottle import Bottle, request, run, response
import requests, json
from datetime import datetime

app = Bottle()

def log(*a):
    print(f"[{datetime.now().isoformat()}]", *a)

HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>TI LeVU — Simulação de Rastreamento</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>html,body,#map{height:100%;margin:0;padding:0} #info{position:absolute;left:8px;top:8px;z-index:600;background:#fff;padding:6px;border-radius:6px;box-shadow:0 1px 4px rgba(0,0,0,0.3)}</style>
</head>
<body>
<div id="map"></div>
<div id="info">
  <div><b>Simulação TI LeVU</b></div>
  <div id="status">Clique em "Iniciar" e permita o GPS</div>
  <button id="start">Iniciar</button>
  <button id="stop">Parar</button>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const centerFranca = [-20.5386, -47.4008]; // ponto inicial do veículo
const map = L.map('map').setView(centerFranca, 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19, attribution:'© OpenStreetMap contributors'}).addTo(map);

let userMarker = null;
let vehicleMarker = L.marker(centerFranca).addTo(map);
let routeLine = null;

const statusEl = document.getElementById('status');
const btnStart = document.getElementById('start');
const btnStop = document.getElementById('stop');

let stopRequested = false;
let currentAnimation = null;

// Haversine (metros)
function distanceMeters(a, b){
  const R = 6371000;
  const toRad = v => v * Math.PI / 180;
  const dLat = toRad(b[0]-a[0]), dLon = toRad(b[1]-a[1]);
  const lat1 = toRad(a[0]), lat2 = toRad(b[0]);
  const sinDlat = Math.sin(dLat/2), sinDlon = Math.sin(dLon/2);
  const aa = sinDlat*sinDlat + Math.cos(lat1)*Math.cos(lat2)*sinDlon*sinDlon;
  return 2 * R * Math.asin(Math.sqrt(aa));
}

// solicita rota ao servidor; retorna array de [lat,lon]
async function fetchRoute(fromLat, fromLon, toLat, toLon){
  const qs = `/route?from_lat=${encodeURIComponent(fromLat)}&from_lon=${encodeURIComponent(fromLon)}&to_lat=${encodeURIComponent(toLat)}&to_lon=${encodeURIComponent(toLon)}`;
  const resp = await fetch(qs);
  const data = await resp.json();
  if(data.error){
    throw data;
  }
  // coords do servidor são [lon,lat] (OSRM) ou fallback [lon,lat]
  const coords = (data.coords || data.route || []).map(c => [c[1], c[0]]);
  return { coords: coords, fallback: !!data.fallback };
}

// animação suave: percorre latlngs (array de [lat,lon]) com velocidade em m/s
function animateAlong(latlngs, options = {}){
  if(!latlngs || latlngs.length === 0) return;
  const speed = options.speed || 10; // m/s
  const tickMs = options.tickMs || 50; // intervalo de atualização (ms)
  stopRequested = false;

  // cancelar animação anterior
  if(currentAnimation && currentAnimation.cancel) currentAnimation.cancel();

  // caso de único ponto: teleporta e pronto
  if(latlngs.length === 1){
    vehicleMarker.setLatLng(latlngs[0]);
    map.panTo(latlngs[0]);
    statusEl.textContent = "Veículo posicionado (mesma coordenada).";
    return;
  }

  // Função que retorna cancel token
  let cancelled = false;
  const token = {
    cancel: () => { cancelled = true; }
  };
  currentAnimation = token;

  (async ()=>{
    for(let s = 0; s < latlngs.length - 1; s++){
      if(cancelled || stopRequested) break;
      const A = latlngs[s], B = latlngs[s+1];
      const segmentDist = distanceMeters(A,B);
      // metros por tick
      const metersPerTick = speed * (tickMs/1000);
      const steps = Math.max(1, Math.ceil(segmentDist / metersPerTick));
      const dLat = (B[0] - A[0]) / steps;
      const dLon = (B[1] - A[1]) / steps;
      for(let i=0; i<=steps; i++){
        if(cancelled || stopRequested) break;
        const lat = A[0] + dLat * i;
        const lon = A[1] + dLon * i;
        vehicleMarker.setLatLng([lat, lon]);
        // opcional: centralizar suavemente
        if(options.follow) map.panTo([lat, lon]);
        await new Promise(res => setTimeout(res, tickMs));
      }
    }
    if(!cancelled && !stopRequested){
      statusEl.textContent = "Veículo chegou ao destino (simulado).";
    } else {
      statusEl.textContent = "Animação interrompida.";
    }
  })();

  return token;
}

// desenha rota (limpa anterior)
function drawRoute(latlngs){
  if(routeLine) map.removeLayer(routeLine);
  routeLine = L.polyline(latlngs, {color:'blue', weight:5, opacity:0.8}).addTo(map);
  map.fitBounds(routeLine.getBounds(), {padding:[40,40]});
}

// iniciar fluxo: pega GPS, solicita rota, desenha e anima
async function startFlow(){
  stopRequested = false;
  statusEl.textContent = "Solicitando permissão de localização...";
  if(!navigator.geolocation){ statusEl.textContent = "Geolocation não suportado."; return; }

  navigator.geolocation.getCurrentPosition(async (pos)=>{
    const lat = pos.coords.latitude, lon = pos.coords.longitude;
    statusEl.textContent = `Posição obtida: ${lat.toFixed(6)}, ${lon.toFixed(6)} → calculando rota...`;
    if(userMarker) userMarker.setLatLng([lat,lon]);
    else userMarker = L.marker([lat,lon], {title:'Você'}).addTo(map);

    try {
      // ponto inicial do veículo = centro de Franca (conforme seu pedido)
      const from = centerFranca;
      const routeResp = await fetchRoute(from[0], from[1], lat, lon);
      let latlngs = routeResp.coords;
      if(!latlngs || latlngs.length === 0){
        throw {error:"rota vazia"};
      }
      statusEl.textContent = routeResp.fallback ? "Usando fallback (rota linear)." : "Rota obtida com sucesso.";
      drawRoute(latlngs);
      // posiciona veículo no início da rota
      vehicleMarker.setLatLng(latlngs[0]);
      // anima com velocidade ~ 12 m/s (43 km/h) e panFollow
      animateAlong(latlngs, {speed: 12, tickMs: 50, follow: true});
    } catch (err) {
      console.error("Erro rota:", err);
      statusEl.textContent = "Erro ao obter rota: " + (err && err.error ? JSON.stringify(err) : String(err));
      // Fallback local: desenha reta do centro até usuário e anima
      const fallback = [[from[0], from[1]], [lat, lon]]; // cuidado: our fetchRoute conversion expects [lat,lon]
      // construir N pontos entre centro e usuário para animação suave
      const N = 120;
      const pts = [];
      for(let i=0;i<=N;i++){
        const t = i/N;
        const latf = from[0] + (lat - from[0]) * t;
        const lonf = from[1] + (lon - from[1]) * t;
        pts.push([latf, lonf]);
      }
      drawRoute(pts);
      vehicleMarker.setLatLng(pts[0]);
      animateAlong(pts, {speed: 12, tickMs: 50, follow: true});
    }
  }, (err)=>{
    statusEl.textContent = "Erro GPS: " + (err && err.message ? err.message : JSON.stringify(err));
  }, {enableHighAccuracy:true, timeout:10000, maximumAge:0});
}

btnStart.addEventListener('click', ()=>{ startFlow(); });
btnStop.addEventListener('click', ()=>{
  stopRequested = true;
  statusEl.textContent = "Parando simulação...";
  if(currentAnimation && currentAnimation.cancel) currentAnimation.cancel();
});
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML

@app.get('/route')
def route():
    # lê parâmetros
    try:
        f_lat = float(request.query.get('from_lat'))
        f_lon = float(request.query.get('from_lon'))
        t_lat = float(request.query.get('to_lat'))
        t_lon = float(request.query.get('to_lon'))
    except Exception as e:
        response.status = 400
        return {"error": "parâmetros inválidos: " + str(e)}

    log("rota solicitada de", f_lat, f_lon, "→", t_lat, t_lon)

    # se mesma coordenada, retorna único ponto
    if abs(f_lat - t_lat) < 1e-9 and abs(f_lon - t_lon) < 1e-9:
        return {"coords": [[f_lon, f_lat]]}

    osrm_url = f"https://router.project-osrm.org/route/v1/driving/{f_lon},{f_lat};{t_lon},{t_lat}?overview=full&geometries=geojson"
    try:
        r = requests.get(osrm_url, timeout=12)
        log("OSRM status", r.status_code)
        if r.status_code == 200:
            data = r.json()
            routes = data.get('routes')
            if routes and len(routes) > 0 and 'geometry' in routes[0]:
                coords = routes[0]['geometry']['coordinates']  # list of [lon,lat]
                return {"coords": coords}
            else:
                log("OSRM sem rota ou geometry:", json.dumps(data)[:400])
        else:
            log("OSRM resposta:", r.status_code, r.text[:300])
    except Exception as e:
        log("Erro acessando OSRM:", e)

    # fallback: gerar linha reta subdividida entre pontos (retorna [lon,lat] como OSRM)
    log("Usando fallback linear entre pontos")
    points = []
    N = 160  # mais pontos => animação mais suave
    for i in range(N+1):
        t = i / N
        lon = f_lon + (t_lon - f_lon) * t
        lat = f_lat + (t_lat - f_lat) * t
        points.append([lon, lat])
    response.status = 200
    return {"coords": points, "fallback": True}

if __name__ == '__main__':
    log("Iniciando servidor em http://0.0.0.0:8080")
    run(app, host='0.0.0.0', port=8380, debug=True)
