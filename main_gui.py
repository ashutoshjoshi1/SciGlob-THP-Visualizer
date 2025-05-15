import sys
import os
import csv
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QStatusBar, QPushButton, QFileDialog, QLabel)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPalette, QColor
from datetime import datetime
import pyqtgraph as pg

from controllers.thp_controller import THPController

# Define color scheme
ROYAL_BLUE = "#4169E1"
DARK_BLUE = "#1A2B47"  # Darker blue for background
MEDIUM_BLUE = "#2A3F5F"  # Medium blue for elements
LIGHT_BLUE = "#B0C4DE"  # For accents
TEXT_COLOR = "#FFFFFF"
GREEN = "#00FF00"
RED = "#FF0000"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("THP Live Monitor")
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background-color: {DARK_BLUE}; }}
            QGroupBox {{ 
                background-color: {MEDIUM_BLUE}; 
                color: {TEXT_COLOR}; 
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton {{ 
                background-color: {ROYAL_BLUE}; 
                color: {TEXT_COLOR}; 
                border-radius: 3px;
                padding: 5px;
            }}
            QPushButton:hover {{ background-color: #5A7CC2; }}
            QLabel {{ color: {TEXT_COLOR}; }}
        """)
        
        # Central 
        central = QWidget()
        main_layout = QVBoxLayout()
        central.setLayout(main_layout)
        self.setCentralWidget(central)

        # Status bar
        self.status = QStatusBar()
        self.status.setStyleSheet(f"background-color: {DARK_BLUE}; color: {TEXT_COLOR};")
        self.setStatusBar(self.status)

        # Connection indicator
        indicator_layout = QHBoxLayout()
        self.connection_indicator = QLabel()
        self.connection_indicator.setFixedSize(20, 20)
        self.connection_indicator.setStyleSheet(f"background-color: {RED}; border-radius: 10px;")
        indicator_label = QLabel("THP Sensor Connection")
        indicator_layout.addWidget(self.connection_indicator)
        indicator_layout.addWidget(indicator_label)
        indicator_layout.addStretch()
        main_layout.addLayout(indicator_layout)

        # Controllers
        ctrl_layout = QHBoxLayout()

        # THP controller
        self.thp_ctrl = THPController(parent=self)
        ctrl_layout.addWidget(self.thp_ctrl.groupbox)

        # Wire signals
        self.thp_ctrl.status_signal.connect(self.status.showMessage)

        self.thp_ctrl.data_signal.connect(self.on_thp_data)

        main_layout.addLayout(ctrl_layout)

        # plots
        date_axis_temp = pg.DateAxisItem(orientation='bottom')
        date_axis_hum = pg.DateAxisItem(orientation='bottom')
        date_axis_pres = pg.DateAxisItem(orientation='bottom')

        # Set plot background colors
        pg.setConfigOption('background', DARK_BLUE)
        pg.setConfigOption('foreground', TEXT_COLOR)

        # 3 divisons
        self.thp_layout = pg.GraphicsLayoutWidget()
        self.thp_layout.setBackground(DARK_BLUE)
        main_layout.addWidget(self.thp_layout)

        self.thp_temp_plot = self.thp_layout.addPlot(row=0, col=0, title="Temperature (°C)", axisItems={'bottom': date_axis_temp})
        self.thp_temp_plot.addLegend()
        self.thp_temp_plot.setLabel('left', 'Temperature', units='°C')
        self.thp_temp_curve = self.thp_temp_plot.plot(name="Temp", pen=pg.mkPen(ROYAL_BLUE, width=2))

        self.hum_plot = self.thp_layout.addPlot(row=1, col=0, title="Humidity (%)", axisItems={'bottom': date_axis_hum})
        self.hum_plot.addLegend()
        self.hum_plot.setLabel('left', 'Humidity', units='%')
        self.hum_curve = self.hum_plot.plot(name="Humidity", pen=pg.mkPen(LIGHT_BLUE, width=2))

        self.pres_plot = self.thp_layout.addPlot(row=2, col=0, title="Pressure (hPa)", axisItems={'bottom': date_axis_pres})
        self.pres_plot.addLegend()
        self.pres_plot.setLabel('left', 'Pressure', units='hPa')
        self.pres_curve = self.pres_plot.plot(name="Pressure", pen=pg.mkPen('#1E90FF', width=2))

        self.hum_plot.setXLink(self.thp_temp_plot)
        self.pres_plot.setXLink(self.thp_temp_plot)

        # CSV creationg
        self.timestamps = []
        self.thp_temps  = []
        self.hums       = []
        self.pressures  = []
        
        self.csv_file = None
        self.setup_csv_logging()

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(1000) 
        
    def update_data(self):
        now = datetime.now()
        timestamp = now.timestamp()
        
        if not self.thp_ctrl.is_connected():
            self.thp_temp_plot.setTitle("Temperature (°C) - Not Connected")
            self.hum_plot.setTitle("Humidity (%) - Not Connected")
            self.pres_plot.setTitle("Pressure (hPa) - Not Connected")
            self.connection_indicator.setStyleSheet(f"background-color: {RED}; border-radius: 10px;")
            
            # Write csv
            if self.csv_file:
                try:
                    self.csv_writer.writerow({
                        "timestamp": "None",
                        "thp_temp": "None",
                        "humidity": "None",
                        "pressure": "None"
                    })
                    self.csv_file.flush()
                except Exception as e:
                    self.status.showMessage(f"Logging error: {str(e)}")
            return
        
        # Reset titles
        self.thp_temp_plot.setTitle("Temperature (°C)")
        self.hum_plot.setTitle("Humidity (%)")
        self.pres_plot.setTitle("Pressure (hPa)")
        self.connection_indicator.setStyleSheet(f"background-color: {GREEN}; border-radius: 10px;")
        
        thp = self.thp_ctrl.get_latest()
        thpt = thp["temperature"]
        hum = thp["humidity"]
        pres = thp["pressure"]

        self.timestamps.append(timestamp)
        self.thp_temps.append(thpt)
        self.hums.append(hum)
        self.pressures.append(pres)
        
        self.thp_temp_curve.setData(self.timestamps, self.thp_temps)
        self.hum_curve.setData(self.timestamps, self.hums)
        self.pres_curve.setData(self.timestamps, self.pressures)

        if self.csv_file:
            try:
                self.csv_writer.writerow({
                    "timestamp": now.isoformat(),
                    "thp_temp": thpt,
                    "humidity": hum,
                    "pressure": pres
                })
                self.csv_file.flush()
            except Exception as e:
                self.status.showMessage(f"Logging error: {str(e)}")

    def on_thp_data(self, data):
        self.status.showMessage(f"THP data received: T={data['temperature']:.1f}°C, H={data['humidity']:.1f}%, P={data['pressure']:.1f}hPa")
        self.connection_indicator.setStyleSheet(f"background-color: {GREEN}; border-radius: 10px;")
    def setup_csv_logging(self):
        try:
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
            os.makedirs(log_dir, exist_ok=True)

            csv_path = os.path.join(log_dir, "THP_data.csv")
            file_exists = os.path.isfile(csv_path)
            
            self.csv_file = open(csv_path, "a", newline="")
            self.csv_writer = csv.DictWriter(
                self.csv_file,
                fieldnames=["timestamp", "thp_temp", "humidity", "pressure"]
            )
            
            if not file_exists:
                self.csv_writer.writeheader()
                
            self.status.showMessage(f"Auto-logging to {csv_path}")
        except Exception as e:
            self.status.showMessage(f"Error setting up logging: {str(e)}")
            self.csv_file = None

    def closeEvent(self, event):
        if self.csv_file:
            self.csv_file.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(900, 600)
    win.show()
    sys.exit(app.exec_())
