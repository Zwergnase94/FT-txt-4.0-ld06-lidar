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

  // Header (y: 2..22)
  Rectangle {
    x: 10; y: 2; width: 220; height: 20; radius: 3
    color: "#16202c"
    Text {
      anchors.centerIn: parent
      text: "LD06 LiDAR - 8 Zonen"
      color: "#00e5ff"
      font.pixelSize: 12
      font.bold: true
    }
  }

  // Vorne (top center, y: 24..42)
  Rectangle {
    x: 50; y: 24; width: 140; height: 18; radius: 4; color: "#1c2b3d"
    Text { id: txt_v; anchors.centerIn: parent; text: "V: -- cm"; color: "#ffffff"; font.pixelSize: 11; font.bold: true }
  }
  // Vorne-Links / Vorne-Rechts (y: 44..62)
  Rectangle {
    x: 15; y: 44; width: 100; height: 18; radius: 4; color: "#1c2b3d"
    Text { id: txt_vl; anchors.centerIn: parent; text: "VL: -- cm"; color: "#ffffff"; font.pixelSize: 10; font.bold: true }
  }
  Rectangle {
    x: 125; y: 44; width: 100; height: 18; radius: 4; color: "#1c2b3d"
    Text { id: txt_vr; anchors.centerIn: parent; text: "VR: -- cm"; color: "#ffffff"; font.pixelSize: 10; font.bold: true }
  }

  // Links / Rechts (y: 64..82)
  Rectangle {
    x: 15; y: 64; width: 100; height: 18; radius: 4; color: "#1c2b3d"
    Text { id: txt_l; anchors.centerIn: parent; text: "L: -- cm"; color: "#ffffff"; font.pixelSize: 10; font.bold: true }
  }
  Rectangle {
    x: 125; y: 64; width: 100; height: 18; radius: 4; color: "#1c2b3d"
    Text { id: txt_r; anchors.centerIn: parent; text: "R: -- cm"; color: "#ffffff"; font.pixelSize: 10; font.bold: true }
  }

  // Hinten-Links / Hinten-Rechts (y: 84..102)
  Rectangle {
    x: 15; y: 84; width: 100; height: 18; radius: 4; color: "#1c2b3d"
    Text { id: txt_hl; anchors.centerIn: parent; text: "HL: -- cm"; color: "#ffffff"; font.pixelSize: 10; font.bold: true }
  }
  Rectangle {
    x: 125; y: 84; width: 100; height: 18; radius: 4; color: "#1c2b3d"
    Text { id: txt_hr; anchors.centerIn: parent; text: "HR: -- cm"; color: "#ffffff"; font.pixelSize: 10; font.bold: true }
  }

  // Hinten (bottom center, y: 104..122)
  Rectangle {
    x: 50; y: 104; width: 140; height: 18; radius: 4; color: "#1c2b3d"
    Text { id: txt_h; anchors.centerIn: parent; text: "H: -- cm"; color: "#ffffff"; font.pixelSize: 11; font.bold: true }
  }

  // Min Distance Card (y: 124..148)
  Rectangle {
    id: box_min
    x: 15; y: 124; width: 210; height: 24; radius: 4; color: "#162230"
    border.color: "#22354a"
    Text {
      id: txt_min
      anchors.centerIn: parent
      text: "Min: -- cm"
      color: "#ffcc00"
      font.pixelSize: 11
      font.bold: true
    }
  }

  // Rate / Sensor Status Card (y: 150..168)
  Rectangle {
    x: 15; y: 150; width: 210; height: 18; radius: 3; color: "#121a24"
    Text {
      id: txt_status
      anchors.centerIn: parent
      text: "Sensor: 0 Pkt/s"
      color: "#00e5ff"
      font.pixelSize: 10
    }
  }

  // Exit Button (y: 174..216, direct child of TXTWindow!)
  TXTButton {
    id: txt_btn_exit
    x: 40; y: 174; width: 160; height: 42
    text: "Beenden"
    font.pixelSize: 14
    enabled: true
  }
}
