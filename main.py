import sys
import os
import csv
import json
import time
from datetime import datetime, timedelta

import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QMessageBox, QDateEdit
)
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from pyqtgraph import DateAxisItem


def read_thp_sensor_data(port_name, baud_rate=9600, timeout=1):
    """Send 'p' to the sensor and parse its JSON response."""
    try:
        ser = serial.Serial(port_name, baud_rate, timeout=timeout)
        time.sleep(1)
        ser.reset_input_buffer()
        ser.write(b'p\r\n')

        response = ""
        start = time.time()
        while time.time() - start < timeout:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                response += line
                try:
                    data = json.loads(response)
                    break
                except json.JSONDecodeError:
                    continue

        ser.close()
        if not response:
            print(f"No response from {port_name}")
            return None

        data = json.loads(response)
        sensors = data.get('Sensors', [])
        if not sensors:
            print(f"Malformed data: {response}")
            return None

        s = sensors[0]
        return {
            'sensor_id':   s.get('ID'),
            'temperature': s.get('Temperature'),
            'humidity':    s.get('Humidity'),
            'pressure':    s.get('Pressure')
        }
    except Exception as e:
        print(f"Sensor read error: {e}")
        return None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("THP Sensor Monitor")
        self.resize(900, 700)

        # --- CSV setup ---
        self.csv_path = "sensor_data.csv"
        if not os.path.isfile(self.csv_path):
            with open(self.csv_path, 'w', newline='') as f:
                w = csv.writer(f)
                w.writerow(["timestamp", "sensor_id", "temperature", "humidity", "pressure"])

        # Buffer of last 24 h
        self.readings = []

        # --- Top controls: Port, Baud, Connect, Date selector, Show Date, Live ---
        port_label = QLabel("Port:")
        self.port_combo = QComboBox()
        for p in serial.tools.list_ports.comports():
            self.port_combo.addItem(p.device)

        baud_label = QLabel("Baud:")
        self.baud_combo = QComboBox()
        for b in ["9600", "19200", "38400", "57600", "115200"]:
            self.baud_combo.addItem(b)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_sensor)

        date_label = QLabel("Date:")
        self.date_edit = QDateEdit(datetime.now().date())
        self.date_edit.setCalendarPopup(True)

        self.show_date_btn = QPushButton("Show Date")
        self.show_date_btn.clicked.connect(self.show_date)

        self.live_btn = QPushButton("Live")
        self.live_btn.clicked.connect(self.show_live)
        self.live_btn.setEnabled(False)  # already in live on start

        top_layout = QHBoxLayout()
        for w in (port_label, self.port_combo, baud_label, self.baud_combo,
                  self.connect_btn, date_label, self.date_edit,
                  self.show_date_btn, self.live_btn):
            top_layout.addWidget(w)

        # --- Plots ---
        self.temp_plot = pg.PlotWidget(
            axisItems={'bottom': DateAxisItem(orientation='bottom')},
            title="Temperature (°C)"
        )
        self.hum_plot  = pg.PlotWidget(
            axisItems={'bottom': DateAxisItem(orientation='bottom')},
            title="Humidity (%)"
        )
        self.pres_plot = pg.PlotWidget(
            axisItems={'bottom': DateAxisItem(orientation='bottom')},
            title="Pressure (hPa)"
        )

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.temp_plot)
        layout.addWidget(self.hum_plot)
        layout.addWidget(self.pres_plot)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Timer for live polling
        self.timer = QTimer()
        self.timer.setInterval(30_000)  # 30 s
        self.timer.timeout.connect(self.update_data)

        # Mode: 'live' or 'history'
        self.mode = 'live'

    def connect_sensor(self):
        self.port = self.port_combo.currentText()
        self.baud = int(self.baud_combo.currentText())
        if not self.port:
            QMessageBox.warning(self, "Error", "Please select a serial port.")
            return

        # disable selectors
        self.port_combo.setEnabled(False)
        self.baud_combo.setEnabled(False)
        self.connect_btn.setEnabled(False)

        self.timer.start()
        # initial live plot
        self.update_data()

    def update_data(self):
        data = read_thp_sensor_data(self.port, self.baud, timeout=2)
        if data is None:
            return

        now = datetime.now()
        entry = {
            "timestamp":   now,
            "sensor_id":   data["sensor_id"],
            "temperature": data["temperature"],
            "humidity":    data["humidity"],
            "pressure":    data["pressure"]
        }

        # append to CSV
        with open(self.csv_path, 'a', newline='') as f:
            w = csv.writer(f)
            w.writerow([
                now.isoformat(),
                entry["sensor_id"],
                entry["temperature"],
                entry["humidity"],
                entry["pressure"]
            ])

        # update buffer (last 24 h)
        self.readings.append(entry)
        cutoff = now - timedelta(hours=24)
        self.readings = [r for r in self.readings if r["timestamp"] >= cutoff]

        if self.mode == 'live':
            self.update_live_plots()

    def update_live_plots(self):
        if not self.readings:
            return
        times = [r["timestamp"].timestamp() for r in self.readings]
        temps = [r["temperature"] for r in self.readings]
        hums  = [r["humidity"]    for r in self.readings]
        pres  = [r["pressure"]    for r in self.readings]

        self.temp_plot.clear()
        self.temp_plot.plot(times, temps, pen='r')
        self.hum_plot.clear()
        self.hum_plot.plot(times, hums, pen='g')
        self.pres_plot.clear()
        self.pres_plot.plot(times, pres, pen='b')

    def show_date(self):
        sel_date = self.date_edit.date().toPyDate()
        self.mode = 'history'
        self.show_date_btn.setEnabled(False)
        self.live_btn.setEnabled(True)
        self.plot_history(sel_date)

    def show_live(self):
        self.mode = 'live'
        self.show_date_btn.setEnabled(True)
        self.live_btn.setEnabled(False)
        self.update_live_plots()

    def plot_history(self, date):
        start = datetime.combine(date, datetime.min.time())
        end   = start + timedelta(days=1)

        times, temps, hums, pres = [], [], [], []
        with open(self.csv_path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ts = datetime.fromisoformat(row['timestamp'])
                if start <= ts <= end:
                    times.append(ts.timestamp())
                    temps.append(float(row['temperature']))
                    hums.append(float(row['humidity']))
                    pres.append(float(row['pressure']))

        self.temp_plot.clear()
        self.temp_plot.plot(times, temps, pen='r')
        self.hum_plot.clear()
        self.hum_plot.plot(times, hums, pen='g')
        self.pres_plot.clear()
        self.pres_plot.plot(times, pres, pen='b')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
