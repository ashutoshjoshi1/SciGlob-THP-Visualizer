from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QPushButton, QHBoxLayout
import serial.tools.list_ports

from drivers.thp_sensor import read_thp_sensor_data

class THPController(QObject):
    status_signal = pyqtSignal(str)
    data_signal = pyqtSignal(dict)  # emits full sensor dict on each update

    def __init__(self, port=None, parent=None):
        super().__init__(parent)
        self.port = port
        self.connected = False
        self.groupbox = QGroupBox("THP Sensor")
        layout = QVBoxLayout()

        # Add connect button
        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_sensor)
        btn_layout.addWidget(self.connect_btn)
        layout.addLayout(btn_layout)

        self.temp_lbl = QLabel("Temp: -- °C")
        self.hum_lbl = QLabel("Humidity: -- %")
        self.pres_lbl = QLabel("Pressure: -- hPa")

        layout.addWidget(self.temp_lbl)
        layout.addWidget(self.hum_lbl)
        layout.addWidget(self.pres_lbl)

        self.groupbox.setLayout(layout)

        self.latest = {
            "temperature": 0.0,
            "humidity": 0.0,
            "pressure": 0.0
        }

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_data)
        
        # Auto-connect on initialization
        QTimer.singleShot(500, self.auto_connect)

    def auto_connect(self):
        """Automatically try to connect to the THP sensor"""
        if self.port:
            # Try the provided port first
            self.connect_sensor()
        else:
            # Try to auto-detect the port
            port = self._find_thp_port()
            if port:
                self.port = port
                self.connect_sensor()
            else:
                # If auto-detection fails, try COM10 directly
                self.port = "COM10"
                self.connect_sensor()

    def connect_sensor(self):
        if self.connected:
            self.timer.stop()
            self.connected = False
            self.connect_btn.setText("Connect")
            self.status_signal.emit("THP sensor disconnected")
            return

        # If no port specified, try to find it
        if not self.port:
            self.port = self._find_thp_port()
            if not self.port:
                self.port = "COM10"  # Default to COM10 if auto-detection fails
        
        # Test connection
        test_data = read_thp_sensor_data(self.port)
        if test_data:
            self.connected = True
            self.connect_btn.setText("Disconnect")
            self.timer.start(3000)
            self.status_signal.emit(f"THP sensor connected on {self.port}")
            self._update_data()  # Update immediately
        else:
            self.status_signal.emit(f"Failed to connect to THP sensor on {self.port}")

    def _find_thp_port(self):
        """Try to auto-detect the THP sensor port"""
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            try:
                test_data = read_thp_sensor_data(port.device)
                if test_data and test_data.get('temperature') is not None:
                    return port.device
            except:
                continue
        return None

    def _update_data(self):
        if not self.connected:
            # Show "---" when not connected
            self.temp_lbl.setText("Temp: --- °C")
            self.hum_lbl.setText("Humidity: --- %")
            self.pres_lbl.setText("Pressure: --- hPa")
            return
            
        data = read_thp_sensor_data(self.port)
        if data:
            self.latest = data
            self.temp_lbl.setText(f"Temp: {data['temperature']:.1f} °C")
            self.hum_lbl.setText(f"Humidity: {data['humidity']:.1f} %")
            self.pres_lbl.setText(f"Pressure: {data['pressure']:.1f} hPa")
            self.data_signal.emit(data)
        else:
            # Show "---" when read fails
            self.temp_lbl.setText("Temp: --- °C")
            self.hum_lbl.setText("Humidity: --- %")
            self.pres_lbl.setText("Pressure: --- hPa")
            self.status_signal.emit("THP sensor read failed.")

    def get_latest(self):
        return self.latest

    def is_connected(self):
        return self.connected
