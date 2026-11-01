import QtQuick 2.2
import QtQuick.Window 2.0
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Extras 1.4

TXTWindow {
  Rectangle {
    id: bg
    color: "#0c1017"
    anchors.fill: parent
  }

  // Status Badge (y: 6..30)
  Rectangle {
    x: 20; y: 6; width: 200; height: 24; radius: 12
    color: "#0f2e1e"; border.color: "#1a5938"
    Text {
      id: txt_badge
      anchors.centerIn: parent
      text: "● WEBSERVER AKTIV"
      color: "#00ff88"
      font.pixelSize: 11
      font.bold: true
    }
  }

  // URL Card (y: 34..84)
  Rectangle {
    x: 15; y: 34; width: 210; height: 50; radius: 6
    color: "#162232"; border.color: "#253b54"
    Text {
      x: 10; y: 5
      text: "Im Webbrowser öffnen:"
      color: "#8fa5bf"
      font.pixelSize: 10
    }
    Text {
      id: txt_url
      x: 10; y: 22
      width: 190
      text: "http://192.168.86.138:8088"
      color: "#00e5ff"
      font.pixelSize: 12
      font.bold: true
      wrapMode: Text.WrapAnywhere
    }
  }

  // Stats Card (y: 88..144)
  Rectangle {
    x: 15; y: 88; width: 210; height: 56; radius: 6
    color: "#121a24"; border.color: "#1c2b3d"
    Text {
      id: txt_rate
      x: 12; y: 6
      text: "Scanrate: 0 Pkt/s"
      color: "#ffffff"
      font.pixelSize: 11
    }
    Text {
      id: txt_pts
      x: 12; y: 22
      text: "Punktwolke: 0 Pkt"
      color: "#8fa5bf"
      font.pixelSize: 11
    }
    Text {
      id: txt_near
      x: 12; y: 38
      text: "Nächstes Objekt: --"
      color: "#ffcc00"
      font.pixelSize: 11
      font.bold: true
    }
  }

  // Info text (y: 148..168)
  Text {
    x: 10; y: 148; width: 220
    text: "Live 360° Radar auf Smartphone/PC"
    color: "#6b829e"
    font.pixelSize: 10
    horizontalAlignment: Text.AlignHCenter
  }

  // Stop Button (y: 174..216, direct child of TXTWindow!)
  TXTButton {
    id: txt_btn_exit
    x: 35; y: 174; width: 170; height: 42
    text: "Server Stoppen"
    font.pixelSize: 14
    enabled: true
  }
}
