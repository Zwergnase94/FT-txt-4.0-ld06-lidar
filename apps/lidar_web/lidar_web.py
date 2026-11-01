#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import socket
import threading
import json
import http.server
import socketserver

ws_dir = os.path.dirname(os.path.abspath(__file__))
if ws_dir not in sys.path:
    sys.path.insert(0, ws_dir)

from lib.display import display
from ld06 import LD06

PORT = 8088

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '192.168.86.138'

class LidarState:
    def __init__(self):
        self.lock = threading.Lock()
        self.points = []
        self.sectors = [9999.0] * 8
        self.rate = 0
        self.running = True
        self.closest = "--"

state = LidarState()
httpd = None

HTML_PAGE = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
  <title>fischertechnik TXT 4.0 - LD06 LiDAR Live-Radar</title>
  <style>
    :root {
      --bg: #0f141c;
      --card-bg: #182232;
      --card-border: #223247;
      --text: #e0e8f5;
      --accent-cyan: #00e5ff;
      --accent-red: #ff3366;
      --accent-yellow: #ffcc00;
      --accent-green: #00ff88;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
      padding: 12px;
    }
    header {
      width: 100%;
      max-width: 900px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--card-border);
    }
    h1 { font-size: 1.25rem; font-weight: 700; color: var(--accent-cyan); display: flex; align-items: center; gap: 8px; }
    .badge {
      font-size: 0.75rem;
      background: #1e334d;
      color: var(--accent-cyan);
      padding: 3px 8px;
      border-radius: 12px;
      border: 1px solid #2a4970;
    }
    .layout {
      width: 100%;
      max-width: 900px;
      display: grid;
      grid-template-columns: 1fr;
      gap: 16px;
    }
    @media (min-width: 768px) {
      .layout { grid-template-columns: 500px 1fr; }
    }
    .radar-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      align-items: center;
      box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    }
    canvas {
      width: 100%;
      max-width: 460px;
      aspect-ratio: 1;
      background: #080d14;
      border-radius: 12px;
      border: 1px solid #1a2a3e;
      touch-action: none;
    }
    .controls {
      display: flex;
      gap: 8px;
      margin-top: 12px;
      width: 100%;
      justify-content: center;
    }
    button {
      background: #1b2a3c;
      border: 1px solid #2a415d;
      color: #9cb3ce;
      padding: 6px 14px;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.85rem;
      cursor: pointer;
      transition: all 0.2s;
    }
    button.active {
      background: var(--accent-cyan);
      color: #081018;
      border-color: var(--accent-cyan);
      box-shadow: 0 0 12px rgba(0,229,255,0.4);
    }
    .side-panel {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .stat-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 16px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    }
    .stat-title {
      font-size: 0.85rem;
      color: #7d96b3;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 8px;
    }
    .grid-sectors {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
    }
    .sector-tile {
      background: #121a25;
      border: 1px solid #1c2b3d;
      border-radius: 10px;
      padding: 10px;
      display: flex;
      flex-direction: column;
      transition: border-color 0.2s;
    }
    .sector-tile.danger {
      border-color: var(--accent-red);
      background: rgba(255, 51, 102, 0.12);
    }
    .sector-tile.warning {
      border-color: var(--accent-yellow);
      background: rgba(255, 204, 0, 0.08);
    }
    .sec-name { font-size: 0.75rem; color: #8fa5bf; }
    .sec-val { font-size: 1.2rem; font-weight: 700; margin-top: 4px; font-variant-numeric: tabular-nums; }
    .min-alert {
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: #121a25;
      padding: 12px 16px;
      border-radius: 10px;
      border: 1px solid #1c2b3d;
    }
    .min-alert-val { font-size: 1.3rem; font-weight: 700; color: var(--accent-cyan); }
  </style>
</head>
<body>
  <header>
    <h1><span>📡</span> fischertechnik TXT 4.0</h1>
    <div style="display: flex; gap: 8px; align-items: center;">
      <span class="badge" id="rate-badge">0 Pkt/s</span>
      <span class="badge" style="background: #103322; color: var(--accent-green); border-color: #1a5938;">● LIVE</span>
    </div>
  </header>

  <div class="layout">
    <div class="radar-card">
      <canvas id="radar" width="600" height="600"></canvas>
      <div class="controls">
        <span style="font-size: 0.8rem; color: #6f86a0; align-self: center; margin-right: 4px;">Zoom:</span>
        <button onclick="setZoom(1.0)" id="z1">1.0 m</button>
        <button onclick="setZoom(2.0)" id="z2" class="active">2.0 m</button>
        <button onclick="setZoom(4.0)" id="z4">4.0 m</button>
        <button onclick="setZoom(8.0)" id="z8">8.0 m</button>
      </div>
    </div>

    <div class="side-panel">
      <div class="stat-card">
        <div class="stat-title">Nächstes Hindernis</div>
        <div class="min-alert">
          <div>
            <div id="min-dir" style="font-size: 0.85rem; color: #8fa5bf;">Richtung: --</div>
            <div id="min-dist" class="min-alert-val">-- cm</div>
          </div>
          <div style="font-size: 1.8rem;" id="min-icon">🛡️</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-title">8-Zonen Abstände (cm)</div>
        <div class="grid-sectors">
          <div class="sector-tile" id="tile-0"><span class="sec-name">Vorne (0°)</span><span class="sec-val" id="val-0">--</span></div>
          <div class="sector-tile" id="tile-1"><span class="sec-name">V-Rechts (45°)</span><span class="sec-val" id="val-1">--</span></div>
          <div class="sector-tile" id="tile-7"><span class="sec-name">V-Links (315°)</span><span class="sec-val" id="val-7">--</span></div>
          <div class="sector-tile" id="tile-2"><span class="sec-name">Rechts (90°)</span><span class="sec-val" id="val-2">--</span></div>
          <div class="sector-tile" id="tile-6"><span class="sec-name">Links (270°)</span><span class="sec-val" id="val-6">--</span></div>
          <div class="sector-tile" id="tile-3"><span class="sec-name">H-Rechts (135°)</span><span class="sec-val" id="val-3">--</span></div>
          <div class="sector-tile" id="tile-5"><span class="sec-name">H-Links (225°)</span><span class="sec-val" id="val-5">--</span></div>
          <div class="sector-tile" id="tile-4"><span class="sec-name">Hinten (180°)</span><span class="sec-val" id="val-4">--</span></div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let maxDist = 200.0;
    const SEC_NAMES = ["Vorne", "Vorne-Rechts", "Rechts", "Hinten-Rechts", "Hinten", "Hinten-Links", "Links", "Vorne-Links"];
    const canvas = document.getElementById("radar");
    const ctx = canvas.getContext("2d");
    let currentData = { points: [], sectors: [], rate: 0 };

    function setZoom(m) {
      maxDist = m * 100.0;
      document.querySelectorAll(".controls button").forEach(b => b.classList.remove("active"));
      const btn = document.getElementById("z" + Math.round(m));
      if (btn) btn.classList.add("active");
    }

    async function poll() {
      try {
        const resp = await fetch("/data");
        if (resp.ok) {
          currentData = await resp.json();
          updateUI();
        }
      } catch (e) {}
      setTimeout(poll, 60);
    }

    function updateUI() {
      document.getElementById("rate-badge").textContent = currentData.rate + " Pkt/s";
      let overallMin = 9999;
      let overallMinIdx = -1;

      if (currentData.sectors) {
        for (let i = 0; i < 8; i++) {
          const val = currentData.sectors[i];
          const el = document.getElementById("val-" + i);
          const tile = document.getElementById("tile-" + i);
          if (val !== null && val !== undefined) {
            el.textContent = val.toFixed(1) + " cm";
            if (val < 30) {
              tile.className = "sector-tile danger";
              el.style.color = "var(--accent-red)";
            } else if (val < 80) {
              tile.className = "sector-tile warning";
              el.style.color = "var(--accent-yellow)";
            } else {
              tile.className = "sector-tile";
              el.style.color = "var(--text)";
            }
            if (val < overallMin) {
              overallMin = val;
              overallMinIdx = i;
            }
          } else {
            el.textContent = "--";
            tile.className = "sector-tile";
            el.style.color = "#556a80";
          }
        }
      }

      if (overallMinIdx >= 0) {
        document.getElementById("min-dir").textContent = "Richtung: " + SEC_NAMES[overallMinIdx];
        document.getElementById("min-dist").textContent = overallMin.toFixed(1) + " cm";
        const icon = document.getElementById("min-icon");
        if (overallMin < 30) {
          document.getElementById("min-dist").style.color = "var(--accent-red)";
          icon.textContent = "⚠️";
        } else if (overallMin < 80) {
          document.getElementById("min-dist").style.color = "var(--accent-yellow)";
          icon.textContent = "⚡";
        } else {
          document.getElementById("min-dist").style.color = "var(--accent-cyan)";
          icon.textContent = "🛡️";
        }
      }
    }

    function drawRadar() {
      const w = canvas.width;
      const h = canvas.height;
      const cx = w / 2;
      const cy = h / 2;
      const rMax = w / 2 - 25;

      ctx.clearRect(0, 0, w, h);

      const rings = 4;
      ctx.strokeStyle = "#1b2a3d";
      ctx.lineWidth = 1;
      for (let i = 1; i <= rings; i++) {
        const r = (rMax / rings) * i;
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.stroke();

        ctx.fillStyle = "#4a627d";
        ctx.font = "11px monospace";
        const distLabel = ((maxDist / rings) * i / 100.0).toFixed(1) + "m";
        ctx.fillText(distLabel, cx + 4, cy - r + 13);
      }

      ctx.beginPath();
      ctx.moveTo(cx, cy - rMax); ctx.lineTo(cx, cy + rMax);
      ctx.moveTo(cx - rMax, cy); ctx.lineTo(cx + rMax, cy);
      ctx.stroke();

      ctx.fillStyle = "#8fa5bf";
      ctx.font = "bold 13px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("VORNE", cx, cy - rMax - 6);
      ctx.fillText("HINTEN", cx, cy + rMax + 18);
      ctx.fillText("LINKS", cx - rMax + 15, cy + 4);
      ctx.fillText("RECHTS", cx + rMax - 15, cy + 4);

      if (currentData.points && currentData.points.length > 0) {
        for (let p of currentData.points) {
          const deg = p[0];
          const distCm = p[1];
          if (distCm <= 0 || distCm > maxDist) continue;

          const rad = (deg - 90) * Math.PI / 180.0;
          const r = (distCm / maxDist) * rMax;
          const px = cx + r * Math.cos(rad);
          const py = cy + r * Math.sin(rad);

          if (distCm < 30) {
            ctx.fillStyle = "#ff3366";
          } else if (distCm < 80) {
            ctx.fillStyle = "#ffcc00";
          } else {
            ctx.fillStyle = "#00e5ff";
          }

          ctx.beginPath();
          ctx.arc(px, py, 2.5, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      ctx.fillStyle = "#00e5ff";
      ctx.beginPath();
      ctx.arc(cx, cy, 6, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = "#00ff88";
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx, cy - 20);
      ctx.lineTo(cx - 5, cy - 14);
      ctx.moveTo(cx, cy - 20);
      ctx.lineTo(cx + 5, cy - 14);
      ctx.stroke();

      requestAnimationFrame(drawRadar);
    }

    drawRadar();
    poll();
  </script>
</body>
</html>"""

class RadarHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path == "/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            with state.lock:
                data = {
                    "points": state.points,
                    "sectors": state.sectors,
                    "rate": state.rate
                }
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

class ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

def on_txt_btn_exit_clicked(event):
    state.running = False
    try:
        display.stop()
    except Exception:
        pass
    if httpd:
        try: httpd.shutdown()
        except Exception: pass
    os._exit(0)

try:
    display.button_clicked("txt_btn_exit", on_txt_btn_exit_clicked)
except Exception:
    pass

def lidar_worker():
    global state
    lidar = None
    while state.running and (lidar is None or not lidar.is_connected()):
        try:
            lidar = LD06("/dev/ttyUSB0")
            if lidar.is_connected():
                break
        except Exception:
            pass
        time.sleep(0.5)

    sec_names = ["V", "VR", "R", "HR", "H", "HL", "L", "VL"]
    last_rate_time = time.time()
    pts_count = 0
    recent_scan = []

    while state.running:
        try:
            pts = lidar.read_points(block_size=400)
            if pts:
                pts_count += len(pts)
                recent_scan.extend(pts)
                if len(recent_scan) > 600:
                    del recent_scan[:-500]

                now = time.time()
                if now - last_rate_time >= 0.5:
                    current_rate = int(pts_count / (now - last_rate_time))
                    pts_count = 0
                    last_rate_time = now

                    sec_mins = [9999.0] * 8
                    overall_min = 9999.0
                    min_sec_name = ""
                    for angle, dist, conf in recent_scan:
                        if dist > 0:
                            s_idx = int((angle + 22.5) % 360 / 45)
                            d_cm = dist / 10.0
                            if d_cm < sec_mins[s_idx]:
                                sec_mins[s_idx] = d_cm
                            if d_cm < overall_min:
                                overall_min = d_cm
                                min_sec_name = sec_names[s_idx]

                    with state.lock:
                        state.points = [[round(a, 1), round(d / 10.0, 1), c] for a, d, c in recent_scan[-450:] if d > 0]
                        state.sectors = [round(m, 1) if m < 9000 else None for m in sec_mins]
                        state.rate = current_rate
                        if overall_min < 9000:
                            state.closest = "{:4.1f} cm ({})".format(overall_min, min_sec_name)
                        else:
                            state.closest = "Frei"
            else:
                time.sleep(0.005)
        except Exception:
            time.sleep(0.1)

    if lidar:
        lidar.close()

def main():
    global httpd
    my_ip = get_ip()
    url_str = "http://{}:{}".format(my_ip, PORT)
    display.set_attr("txt_url.text", url_str)
    display.set_attr("txt_rate.text", "Starte Server...")

    t = threading.Thread(target=lidar_worker, daemon=True)
    t.start()

    try:
        httpd = ReusableTCPServer(("0.0.0.0", PORT), RadarHandler)
    except Exception as e:
        display.set_attr("txt_rate.text", "Port {} belegt!".format(PORT))
        return

    # Background thread for updating TXT display labels
    def display_updater():
        while state.running:
            try:
                with state.lock:
                    rate = state.rate
                    pts_len = len(state.points)
                    closest = state.closest
                display.set_attr("txt_rate.text", "Scanrate: {:d} Pkt/s".format(rate))
                display.set_attr("txt_pts.text", "Punktwolke: {:d} Pkt".format(pts_len))
                display.set_attr("txt_near.text", "Naechstes: " + closest)
            except Exception:
                pass
            time.sleep(0.5)

    threading.Thread(target=display_updater, daemon=True).start()

    try:
        httpd.serve_forever()
    except Exception:
        pass
    finally:
        state.running = False
        if httpd:
            httpd.server_close()

if __name__ == "__main__":
    main()
