import sys
import os
import csv
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QStatusBar, QPushButton, QFileDialog)
from PyQt5.QtCore import Qt, QTimer
from datetime import datetime
import pyqtgraph as pg

# Remove unused imports
from controllers.thp_controller import THPController

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("THP Live Monitor")  # Updated title
        # Central layout
        central = QWidget()
        main_layout = QVBoxLayout()
        central.setLayout(main_layout)
        self.setCentralWidget(central)

        # Status bar - create this before controllers
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # Controllers
        ctrl_layout = QHBoxLayout()

        # THP controller - don't specify port to enable auto-detection
        self.thp_ctrl = THPController(parent=self)
        ctrl_layout.addWidget(self.thp_ctrl.groupbox)

        # Wire status signals
        self.thp_ctrl.status_signal.connect(self.status.showMessage)
        # Connect to the data signal to know when sensor is connected
        self.thp_ctrl.data_signal.connect(self.on_thp_data)

        main_layout.addLayout(ctrl_layout)

        # Create date axis items for THP plots
        date_axis_temp = pg.DateAxisItem(orientation='bottom')
        date_axis_hum = pg.DateAxisItem(orientation='bottom')
        date_axis_pres = pg.DateAxisItem(orientation='bottom')

        # THP Sensor - create a GraphicsLayoutWidget to hold 3 separate plots
        self.thp_layout = pg.GraphicsLayoutWidget()
        main_layout.addWidget(self.thp_layout)

        # Create three separate plots for THP with date axes
        self.thp_temp_plot = self.thp_layout.addPlot(row=0, col=0, title="Temperature (°C)", axisItems={'bottom': date_axis_temp})
        self.thp_temp_plot.addLegend()
        self.thp_temp_plot.setLabel('left', 'Temperature', units='°C')
        self.thp_temp_curve = self.thp_temp_plot.plot(name="Temp", pen=pg.mkPen('r', width=2))

        self.hum_plot = self.thp_layout.addPlot(row=1, col=0, title="Humidity (%)", axisItems={'bottom': date_axis_hum})
        self.hum_plot.addLegend()
        self.hum_plot.setLabel('left', 'Humidity', units='%')
        self.hum_curve = self.hum_plot.plot(name="Humidity", pen=pg.mkPen('b', width=2))

        self.pres_plot = self.thp_layout.addPlot(row=2, col=0, title="Pressure (hPa)", axisItems={'bottom': date_axis_pres})
        self.pres_plot.addLegend()
        self.pres_plot.setLabel('left', 'Pressure', units='hPa')
        self.pres_curve = self.pres_plot.plot(name="Pressure", pen=pg.mkPen('g', width=2))

        # Link X axes of all THP plots so they zoom/pan together
        self.hum_plot.setXLink(self.thp_temp_plot)
        self.pres_plot.setXLink(self.thp_temp_plot)

        # Data storage - don't limit the size
        self.timestamps = []
        self.thp_temps  = []
        self.hums       = []
        self.pressures  = []
        
        # Setup automatic CSV logging
        self.csv_file = None
        self.setup_csv_logging()

        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(1000) 
        
    def update_data(self):
        now = datetime.now()
        timestamp = now.timestamp()  # Unix timestamp in seconds
        
        # Check if THP sensor is connected
        if not self.thp_ctrl.is_connected():
            # Update labels to show "---" when not connected
            self.thp_temp_plot.setTitle("Temperature (°C) - Not Connected")
            self.hum_plot.setTitle("Humidity (%) - Not Connected")
            self.pres_plot.setTitle("Pressure (hPa) - Not Connected")
            
            # Write to CSV with None values when not connected
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
        
        # Reset titles when connected
        self.thp_temp_plot.setTitle("Temperature (°C)")
        self.hum_plot.setTitle("Humidity (%)")
        self.pres_plot.setTitle("Pressure (hPa)")
        
        # THP values only
        thp = self.thp_ctrl.get_latest()
        thpt = thp["temperature"]
        hum = thp["humidity"]
        pres = thp["pressure"]

        # store all values without truncation
        self.timestamps.append(timestamp)
        self.thp_temps.append(thpt)
        self.hums.append(hum)
        self.pressures.append(pres)
        
        # Update the three separate THP plots with all data points
        self.thp_temp_curve.setData(self.timestamps, self.thp_temps)
        self.hum_curve.setData(self.timestamps, self.hums)
        self.pres_curve.setData(self.timestamps, self.pressures)

        # Write to log when connected
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
        """Called when new THP data is received"""
        # This method handles data signals from the THP controller
        # We can use it to update status or perform actions when data is received
        self.status.showMessage(f"THP data received: T={data['temperature']:.1f}°C, H={data['humidity']:.1f}%, P={data['pressure']:.1f}hPa")

    def setup_csv_logging(self):
        """Setup automatic CSV logging to THP_data.csv"""
        try:
            # Create directory if it doesn't exist
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
            os.makedirs(log_dir, exist_ok=True)
            
            # Create or open the CSV file
            csv_path = os.path.join(log_dir, "THP_data.csv")
            file_exists = os.path.isfile(csv_path)
            
            self.csv_file = open(csv_path, "a", newline="")
            self.csv_writer = csv.DictWriter(
                self.csv_file,
                fieldnames=["timestamp", "thp_temp", "humidity", "pressure"]
            )
            
            # Write header only if file is new
            if not file_exists:
                self.csv_writer.writeheader()
                
            self.status.showMessage(f"Auto-logging to {csv_path}")
        except Exception as e:
            self.status.showMessage(f"Error setting up logging: {str(e)}")
            self.csv_file = None

    def closeEvent(self, event):
        """Handle application close event"""
        if self.csv_file:
            self.csv_file.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(900, 600)
    win.show()
    sys.exit(app.exec_())
