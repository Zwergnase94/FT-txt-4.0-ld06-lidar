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

  // Omni 8-Zonen Dashboard Canvas (240x230 nutzbarer TXT 4.0 Bereich)
  Canvas {
    id: omni_canvas
    x: 0; y: 0; width: 240; height: 230

    // Gepackter Zustand:
    // "d0,d1,d2,d3,d4,d5,d6,d7|cmdSec|cmdBlocked|cmdRotate|driveEnabled|invertRot|statusMode|statusText|minText"
    property string stateStr: ""

    onStateStrChanged: {
      requestPaint();
    }

    function fillRoundRect(ctx, x, y, w, h, r) {
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.lineTo(x + w - r, y);
      ctx.quadraticCurveTo(x + w, y, x + w, y + r);
      ctx.lineTo(x + w, y + h - r);
      ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
      ctx.lineTo(x + r, y + h);
      ctx.quadraticCurveTo(x, y + h, x, y + h - r);
      ctx.lineTo(x, y + r);
      ctx.quadraticCurveTo(x, y, x + r, y);
      ctx.closePath();
    }

    function drawDashedCircle(ctx, cx, cy, r, segs) {
      var step = (Math.PI * 2) / segs;
      for (var i = 0; i < segs; i += 2) {
        ctx.beginPath();
        ctx.arc(cx, cy, r, i * step, (i + 1) * step, false);
        ctx.stroke();
      }
    }

    function drawDashedLine(ctx, x1, y1, x2, y2, segs) {
      var dx = (x2 - x1) / segs;
      var dy = (y2 - y1) / segs;
      for (var i = 0; i < segs; i += 2) {
        ctx.beginPath();
        ctx.moveTo(x1 + dx * i, y1 + dy * i);
        ctx.lineTo(x1 + dx * (i + 1), y1 + dy * (i + 1));
        ctx.stroke();
      }
    }

    onPaint: {
      var ctx = getContext("2d");
      var w = width;
      var h = height;

      // Standardwerte falls noch kein Update vom Python-Prozess eingetroffen ist
      var dists = [0, 0, 0, 0, 0, 0, 0, 0];
      var cmdSec = -1;
      var cmdBlocked = false;
      var cmdRotate = 0;
      var driveEnabled = true;
      var invertRot = false;
      var statusMode = "IDLE";
      var statusText = "BEREIT (>18cm frei)";
      var minText = "Warte LiDAR";

      if (stateStr && stateStr.length > 0) {
        var parts = stateStr.split("|");
        if (parts.length >= 9) {
          var dArr = parts[0].split(",");
          for (var k = 0; k < 8 && k < dArr.length; k++) {
            var v = parseInt(dArr[k], 10);
            dists[k] = isNaN(v) ? 0 : v;
          }
          cmdSec = parseInt(parts[1], 10);
          if (isNaN(cmdSec)) cmdSec = -1;
          cmdBlocked = (parts[2] === "1");
          cmdRotate = parseInt(parts[3], 10);
          if (isNaN(cmdRotate)) cmdRotate = 0;
          driveEnabled = (parts[4] !== "0");
          invertRot = (parts[5] === "1");
          statusMode = parts[6];
          statusText = parts[7];
          minText = parts[8];
        }
      }

      // 1. Hintergrund
      ctx.fillStyle = "#0a0e14";
      ctx.fillRect(0, 0, w, h);

      // Top-Buttons-Statusanzeige (Touch-Ziele liegen exakt darüber)
      // Oben links: Motor AN / PAUSE
      fillRoundRect(ctx, 6, 4, 58, 16, 3);
      ctx.fillStyle = driveEnabled ? "#0e303a" : "#372819";
      ctx.fill();
      ctx.strokeStyle = driveEnabled ? "#00b4a0" : "#f0b400";
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.font = "bold 8px sans-serif";
      ctx.textAlign = "center";
      ctx.fillStyle = driveEnabled ? "#00ffb4" : "#f0b400";
      ctx.fillText(driveEnabled ? "Motor: AN" : "PAUSE", 35, 15);

      // Oben rechts: Drehrichtung Normal / Invertiert
      fillRoundRect(ctx, 176, 4, 58, 16, 3);
      ctx.fillStyle = invertRot ? "#302410" : "#101a26";
      ctx.fill();
      ctx.strokeStyle = invertRot ? "#ffcc00" : "#1e324b";
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.fillStyle = invertRot ? "#ffcc00" : "#00e5ff";
      ctx.fillText(invertRot ? "Dreh: Inv" : "Dreh: L/R", 205, 15);

      // 2. 8-Zonen Sektor-Radar (oben zentriert)
      var cx = 120.0;
      var cy = 60.0;
      var rOuter = 46.0;
      var rInner = 18.0;
      var rStop = rInner + (1.0 - (18.0 / 160.0)) * (rOuter - rInner);

      // Gitterringe & Trennlinien (gestrichelt)
      ctx.strokeStyle = "rgba(0, 140, 110, 0.55)";
      ctx.lineWidth = 1;
      drawDashedCircle(ctx, cx, cy, rOuter, 40);
      drawDashedCircle(ctx, cx, cy, rInner, 20);

      for (var dIdx = 0; dIdx < 8; dIdx++) {
        var divAng = (dIdx * 45.0 + 22.5) * Math.PI / 180.0;
        var sDiv = Math.sin(divAng);
        var cDiv = Math.cos(divAng);
        drawDashedLine(
          ctx,
          cx + rInner * sDiv, cy - rInner * cDiv,
          cx + rOuter * sDiv, cy - rOuter * cDiv,
          6
        );
      }

      // 18 cm Stopp-Ring (rot gepunktet)
      ctx.strokeStyle = "rgba(255, 60, 60, 0.78)";
      ctx.lineWidth = 1;
      drawDashedCircle(ctx, cx, cy, rStop, 36);

      // Dynamische Sektor-Warnbögen (Rot <= 18 cm, Gelb <= 30 cm, Türkis > 30 cm)
      var minOverallMm = 99999;
      for (var i = 0; i < 8; i++) {
        var distMm = dists[i];
        if (distMm > 0) {
          if (distMm < minOverallMm) {
            minOverallMm = distMm;
          }
          var dCm = distMm * 0.1;
          if (distMm <= 180) {
            ctx.fillStyle = "rgba(255, 40, 40, 0.86)";
          } else if (distMm <= 300) {
            ctx.fillStyle = "rgba(255, 190, 0, 0.72)";
          } else {
            ctx.fillStyle = "rgba(0, 225, 200, 0.65)";
          }

          var ratio = Math.max(0.25, Math.min(1.0, 1.0 - (dCm / 160.0)));
          var rBar = rInner + ratio * (rOuter - rInner);
          var aStart = (i * 45.0 - 90.0 - 22.5) * Math.PI / 180.0;
          var aEnd = (i * 45.0 - 90.0 + 22.5) * Math.PI / 180.0;

          ctx.beginPath();
          ctx.moveTo(cx, cy);
          ctx.arc(cx, cy, rBar, aStart, aEnd, false);
          ctx.closePath();
          ctx.fill();
        }
      }

      // Aktiven Joystick-Sektor im Radar hervorheben
      if (cmdSec >= 0 && cmdSec < 8) {
        var selStart = (cmdSec * 45.0 - 90.0 - 22.5) * Math.PI / 180.0;
        var selEnd = (cmdSec * 45.0 - 90.0 + 22.5) * Math.PI / 180.0;
        ctx.strokeStyle = cmdBlocked ? "#ff3c3c" : "#00ffdc";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.arc(cx, cy, rOuter, selStart, selEnd, false);
        ctx.closePath();
        ctx.stroke();
      }

      // Inneren Kreis um den Roboter sauber freistellen
      ctx.fillStyle = "#0a0e14";
      ctx.beginPath();
      ctx.arc(cx, cy, rInner, 0, Math.PI * 2, false);
      ctx.fill();

      // Richtungs-Labels rund um den Radar-Kreis
      var dirLabels = ["V", "VR", "R", "HR", "H", "HL", "L", "VL"];
      ctx.font = "bold 9px sans-serif";
      ctx.textAlign = "center";
      ctx.fillStyle = "#00e6c8";
      for (var li = 0; li < 8; li++) {
        var lAng = (li * 45.0) * Math.PI / 180.0;
        var lx = cx + (rOuter + 8.5) * Math.sin(lAng);
        var ly = cy - (rOuter + 8.5) * Math.cos(lAng) + 3.0;
        ctx.fillText(dirLabels[li], lx, ly);
      }

      // Roboter-Symbol in der Mitte (Chassis + 4 gelbe Omniwheels + Pfeil/Drehung)
      fillRoundRect(ctx, cx - 8, cy - 11, 16, 22, 2.5);
      ctx.fillStyle = driveEnabled ? "#142d4b" : "#372819";
      ctx.fill();
      ctx.strokeStyle = "#64a0dc";
      ctx.lineWidth = 1;
      ctx.stroke();

      ctx.fillStyle = "#dca514";
      ctx.fillRect(cx - 11, cy - 9, 3, 6);
      ctx.fillRect(cx - 11, cy + 3, 3, 6);
      ctx.fillRect(cx + 8, cy - 9, 3, 6);
      ctx.fillRect(cx + 8, cy + 3, 3, 6);

      if (cmdRotate !== 0) {
        ctx.strokeStyle = "#00e6ff";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(cx, cy, 14, -Math.PI * 0.75, Math.PI * 0.9, false);
        ctx.stroke();
        ctx.font = "bold 9px sans-serif";
        ctx.textAlign = "center";
        ctx.fillStyle = "#00e1ff";
        ctx.fillText(cmdRotate > 0 ? "R" : "L", cx, cy + 3.5);
      } else if (cmdSec >= 0 && cmdSec < 8) {
        var mAng = (cmdSec * 45.0) * Math.PI / 180.0;
        var sinM = Math.sin(mAng);
        var cosM = Math.cos(mAng);
        ctx.fillStyle = cmdBlocked ? "#ff3737" : "#00ffb4";
        ctx.beginPath();
        ctx.moveTo(cx + 10.5 * sinM, cy - 10.5 * cosM);
        ctx.lineTo(cx - 3.5 * sinM + 4.5 * cosM, cy + 3.5 * cosM + 4.5 * sinM);
        ctx.lineTo(cx - 1.2 * sinM, cy + 1.2 * cosM);
        ctx.lineTo(cx - 3.5 * sinM - 4.5 * cosM, cy + 3.5 * cosM - 4.5 * sinM);
        ctx.closePath();
        ctx.fill();
      } else {
        ctx.fillStyle = "#00dcff";
        ctx.beginPath();
        ctx.moveTo(cx, cy - 9);
        ctx.lineTo(cx + 4.5, cy - 1);
        ctx.lineTo(cx, cy - 3.5);
        ctx.lineTo(cx - 4.5, cy - 1);
        ctx.closePath();
        ctx.fill();
      }

      // 3. 8-Sektoren-Karten (2 Spalten x 4 Reihen, y: 123..209)
      var secNames = [
        "Vorne", "V-Rechts", "Rechts", "H-Rechts",
        "Hinten", "H-Links", "Links", "V-Links"
      ];
      var cardW = 110.0;
      var cardH = 20.0;
      var startY = 123.0;
      var spacingY = 22.0;
      var badgeW = 42.0;
      var badgeH = 15.0;

      for (var col = 0; col < 2; col++) {
        var bx = (col === 0) ? 8.0 : 122.0;
        for (var row = 0; row < 4; row++) {
          var idx = col * 4 + row;
          var by = startY + row * spacingY;
          var isSelected = (idx === cmdSec);

          fillRoundRect(ctx, bx, by, cardW, cardH, 4);
          if (isSelected) {
            ctx.fillStyle = cmdBlocked ? "#3c1216" : "#0e303a";
            ctx.fill();
            ctx.strokeStyle = cmdBlocked ? "#ff3232" : "#00f0dc";
            ctx.lineWidth = 1.5;
            ctx.stroke();
          } else {
            ctx.fillStyle = "#101a26";
            ctx.fill();
            ctx.strokeStyle = "#1e324b";
            ctx.lineWidth = 1;
            ctx.stroke();
          }

          ctx.font = "bold 9px sans-serif";
          ctx.textAlign = "left";
          ctx.fillStyle = isSelected ? "#ffffff" : "#b4cde1";
          ctx.fillText(secNames[idx], bx + 5, by + 13.5);

          var sDist = dists[idx];
          var badgeX = bx + cardW - badgeW - 3.5;
          var badgeY = by + (cardH - badgeH) * 0.5;
          var badgeBg = "#232d37";
          var badgeFg = "#647382";
          var txtVal = "---";

          if (sDist > 0) {
            var sdCm = Math.round(sDist * 0.1);
            txtVal = sdCm + " cm";
            if (sDist <= 180) {
              badgeBg = "#dc2d2d";
              badgeFg = "#ffffff";
            } else if (sDist <= 300) {
              badgeBg = "#f0b400";
              badgeFg = "#000000";
            } else {
              badgeBg = "#00a078";
              badgeFg = "#ffffff";
            }
          }

          fillRoundRect(ctx, badgeX, badgeY, badgeW, badgeH, 3);
          ctx.fillStyle = badgeBg;
          ctx.fill();

          ctx.font = "bold 9px sans-serif";
          ctx.textAlign = "center";
          ctx.fillStyle = badgeFg;
          ctx.fillText(txtVal, badgeX + badgeW * 0.5, badgeY + 11.0);
        }
      }

      // 4. Statuszeile ganz unten (y: 213..228)
      var stCol = "#96b4cd";
      if (statusMode === "BLOCKED") stCol = "#ff4b4b";
      else if (statusMode === "SLOW" || statusMode === "PAUSED") stCol = "#f0b400";
      else if (statusMode === "DRIVE") stCol = "#00ffb4";
      else if (statusMode === "ROTATE") stCol = "#00e1ff";

      ctx.font = "bold 9px sans-serif";
      ctx.textAlign = "left";
      ctx.fillStyle = stCol;
      ctx.fillText(statusText, 8, 224);

      var minCol = "#f0b400";
      if (minOverallMm < 99999) {
        if (minOverallMm <= 180) minCol = "#dc2d2d";
        else if (minOverallMm <= 300) minCol = "#f0b400";
        else minCol = "#00e6c8";
      }
      ctx.textAlign = "right";
      ctx.fillStyle = minCol;
      ctx.fillText(minText, 232, 224);
    }
  }

  // Unsichtbare Touch-Ziele als direkte Kinder von TXTWindow (damit ftgui Klicks empfängt)
  TXTButton {
    id: txt_btn_drive
    x: 80; y: 20; width: 80; height: 80
    text: ""
    opacity: 0.0
    enabled: true
  }

  TXTButton {
    id: txt_btn_pause
    x: 4; y: 2; width: 64; height: 24
    text: ""
    opacity: 0.0
    enabled: true
  }

  TXTButton {
    id: txt_btn_rot
    x: 172; y: 2; width: 64; height: 24
    text: ""
    opacity: 0.0
    enabled: true
  }
}
