from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QPushButton, QHBoxLayout
import serial.tools.list_ports
import time

from drivers.thp_sensor import read_thp_sensor_data

class THPController(QObject):
    status_signal = pyqtSignal(str)
    data_signal = pyqtSignal(dict)

    def __init__(self, port=None, parent=None):
        super().__init__(parent)
        self.port = port
        self.connected = False
        self.groupbox = QGroupBox("THP Sensor")
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 25, 15, 15)  # Add internal margins
        layout.setSpacing(15)  # Increase spacing between elements

        # Add connect button
        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setMinimumHeight(40)  # Taller button
        self.connect_btn.clicked.connect(self.connect_sensor)
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addStretch()  # Push button to the left
        layout.addLayout(btn_layout)

        # Sensor readings with larger font and better spacing
        self.temp_lbl = QLabel("Temperature: -- °C")
        self.temp_lbl.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.hum_lbl = QLabel("Humidity: -- %")
        self.hum_lbl.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.pres_lbl = QLabel("Pressure: -- hPa")
        self.pres_lbl.setStyleSheet("font-size: 14pt; font-weight: bold;")

        # Add some spacing between elements
        layout.addSpacing(10)
        layout.addWidget(self.temp_lbl)
        layout.addWidget(self.hum_lbl)
        layout.addWidget(self.pres_lbl)
        layout.addStretch()  # Push everything to the top

        self.groupbox.setLayout(layout)

        self.latest = {
            "temperature": 0.0,
            "humidity": 0.0,
            "pressure": 0.0
        }

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_data)
        
        QTimer.singleShot(500, self.auto_connect)

    def auto_connect(self):
        if self.port:
            # Try
            self.connect_sensor()
        else:
            # auto-detect
            port = self._find_thp_port()
            if port:
                self.port = port
                self.connect_sensor()
            else:
                #COM10 directly
                self.port = "COM10"
                self.connect_sensor()

    def connect_sensor(self):
        if self.connected:
            self.timer.stop()
            self.connected = False
            self.connect_btn.setText("Connect")
            self.status_signal.emit("THP sensor disconnected")
            return

        # If no port
        if not self.port:
            self.port = self._find_thp_port()
            if not self.port:
                self.port = "COM10"  # Default
        
        # Test connection
        self.status_signal.emit(f"Connecting to THP sensor on {self.port}...")
        test_data = read_thp_sensor_data(self.port)
        if test_data:
            self.connected = True
            self.connect_btn.setText("Disconnect")
            self.timer.start(3000)
            self.status_signal.emit(f"THP sensor connected on {self.port}")
            self._update_data()
        else:
            self.status_signal.emit(f"Failed to connect to THP sensor on {self.port}")

    def _find_thp_port(self):
        """Try to auto-detect the THP sensor port by sending simple commands"""
        self.status_signal.emit("Scanning COM ports...")
        ports = list(serial.tools.list_ports.comports())
        
        for port in ports:
            try:
                self.status_signal.emit(f"Trying {port.device}...")
                ser = serial.Serial(port.device, 9600, timeout=1)
                time.sleep(0.5)  # delay
                
                ser.reset_input_buffer()
                
                ser.write(b'p\r\n')
                
                response = ""
                start_time = time.time()
                while time.time() - start_time < 1:  # 1 sec timeout
                    if ser.in_waiting > 0:
                        line = ser.readline().decode('utf-8', errors='ignore').strip()
                        response += line
                        
                        # Check JSON
                        if '{' in response and 'Sensors' in response:
                            ser.close()
                            self.status_signal.emit(f"Found THP sensor on {port.device}")
                            return port.device
                
                # v cmd
                ser.reset_input_buffer()
                ser.write(b'v\r\n')
                
                response = ""
                start_time = time.time()
                while time.time() - start_time < 1:
                    if ser.in_waiting > 0:
                        line = ser.readline().decode('utf-8', errors='ignore').strip()
                        response += line
                       
                        if 'version' in response.lower() or 'bme280' in response.lower():
                            ser.close()
                            self.status_signal.emit(f"Found THP sensor on {port.device}")
                            return port.device
                
                ser.close()
            except Exception as e:
                self.status_signal.emit(f"Error with {port.device}: {str(e)}")
                continue
        
        self.status_signal.emit("No THP sensor found. Will try COM10.")
        return None

    def _update_data(self):
        if not self.connected:
            self.temp_lbl.setText("Temperature: --- °C")
            self.hum_lbl.setText("Humidity: --- %")
            self.pres_lbl.setText("Pressure: --- hPa")
            return
        
        data = read_thp_sensor_data(self.port)
        if data:
            self.latest = data
            self.temp_lbl.setText(f"Temperature: {data['temperature']:.1f} °C")
            self.hum_lbl.setText(f"Humidity: {data['humidity']:.1f} %")
            self.pres_lbl.setText(f"Pressure: {data['pressure']:.1f} hPa")
            self.data_signal.emit(data)
        else:
            self.temp_lbl.setText("Temperature: --- °C")
            self.hum_lbl.setText("Humidity: --- %")
            self.pres_lbl.setText("Pressure: --- hPa")
            self.status_signal.emit("THP sensor read failed.")

    def get_latest(self):
        return self.latest

    def is_connected(self):
        return self.connected
