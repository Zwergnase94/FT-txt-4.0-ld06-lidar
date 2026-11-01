import QtQuick 2.2
import QtQuick.Window 2.0
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Extras 1.4

TXTWindow {
  Rectangle {
    id: bg
    color: "#0a0e14"
    anchors.fill: parent
  }

  // Info Bar (y: 4..28)
  Rectangle {
    x: 10; y: 4; width: 220; height: 24; radius: 4
    color: "#121a24"; border.color: "#1c2b3d"
    Text {
      id: txt_info
      anchors.centerIn: parent
      text: "Verbinde mit Sensor..."
      color: "#ffffff"
      font.pixelSize: 11
      font.bold: true
    }
  }

  // Radar Canvas (y: 32..172, 140x140, centered at x: 50)
  Canvas {
    id: radar_canvas
    x: 50; y: 32; width: 140; height: 140
    property string rawPoints: ""
    property real maxDist: 200.0

    onRawPointsChanged: {
      requestPaint();
    }

    onMaxDistChanged: {
      requestPaint();
    }

    onPaint: {
      var ctx = getContext("2d");
      var w = width;
      var h = height;
      var cx = w / 2;
      var cy = h / 2;
      var rMax = w / 2 - 5;

      // Background
      ctx.fillStyle = "#070b10";
      ctx.fillRect(0, 0, w, h);

      // Concentric Rings
      ctx.strokeStyle = "#1b2a3d";
      ctx.lineWidth = 1;
      for (var i = 1; i <= 4; i++) {
        var r = (rMax / 4) * i;
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.stroke();

        // Distance label
        ctx.fillStyle = "#465d75";
        ctx.font = "8px monospace";
        var lbl = ((maxDist / 4) * i / 100.0).toFixed(1) + "m";
        ctx.fillText(lbl, cx + 2, cy - r + 8);
      }

      // Crosshairs
      ctx.beginPath();
      ctx.moveTo(cx, cy - rMax); ctx.lineTo(cx, cy + rMax);
      ctx.moveTo(cx - rMax, cy); ctx.lineTo(cx + rMax, cy);
      ctx.stroke();

      // Direction Labels
      ctx.fillStyle = "#8fa5bf";
      ctx.font = "bold 9px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("V", cx, cy - rMax + 9);
      ctx.fillText("H", cx, cy + rMax - 2);
      ctx.fillText("L", cx - rMax + 7, cy + 3);
      ctx.fillText("R", cx + rMax - 7, cy + 3);

      // Draw Point Cloud
      if (rawPoints && rawPoints.length > 0) {
        var pairs = rawPoints.split(";");
        for (var p = 0; p < pairs.length; p++) {
          var item = pairs[p].split(",");
          if (item.length < 2) continue;
          var deg = parseFloat(item[0]);
          var distCm = parseFloat(item[1]);
          if (distCm <= 0 || distCm > maxDist) continue;

          var rad = (deg - 90) * Math.PI / 180.0;
          var pr = (distCm / maxDist) * rMax;
          var px = cx + pr * Math.cos(rad);
          var py = cy + pr * Math.sin(rad);

          if (distCm < 30) {
            ctx.fillStyle = "#ff3366";
          } else if (distCm < 80) {
            ctx.fillStyle = "#ffcc00";
          } else {
            ctx.fillStyle = "#00e5ff";
          }
          ctx.fillRect(px - 1.5, py - 1.5, 3, 3);
        }
      }

      // Center Robot Dot & Arrow
      ctx.fillStyle = "#00ff88";
      ctx.beginPath();
      ctx.arc(cx, cy, 3, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = "#00ff88";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx, cy - 7);
      ctx.stroke();
    }
  }

  // Buttons at y: 180..222 (within 230 max height!)
  TXTButton {
    id: txt_btn_zoom
    x: 15; y: 180; width: 100; height: 42
    text: "Zoom: 2m"
    font.pixelSize: 13
    enabled: true
  }

  TXTButton {
    id: txt_btn_exit
    x: 125; y: 180; width: 100; height: 42
    text: "Beenden"
    font.pixelSize: 13
    enabled: true
  }
}
