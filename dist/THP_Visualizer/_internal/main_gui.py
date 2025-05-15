import sys
import os
import csv
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QStatusBar, QPushButton, QFileDialog, QLabel,
                            QDateTimeEdit, QGroupBox, QToolTip, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QPalette, QColor, QFont
from datetime import datetime, timedelta
import pyqtgraph as pg
import pkg_resources

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
        
        # Set minimum window size to ensure all elements are visible
        self.setMinimumSize(800, 600)
        
        # Update stylesheet with better spacing and visibility for headings
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background-color: {DARK_BLUE}; }}
            QGroupBox {{ 
                background-color: {MEDIUM_BLUE}; 
                color: {TEXT_COLOR}; 
                border-radius: 5px;
                font-weight: bold;
                font-size: 12pt;
                padding-top: 16px;
                margin-top: 8px;
            }}
            QPushButton {{ 
                background-color: {ROYAL_BLUE}; 
                color: {TEXT_COLOR}; 
                border-radius: 3px;
                padding: 6px;
                font-size: 10pt;
                min-height: 25px;
            }}
            QPushButton:hover {{ background-color: #5A7CC2; }}
            QLabel {{ 
                color: {TEXT_COLOR}; 
                font-size: 10pt;
            }}
            QDateTimeEdit {{ 
                color: {TEXT_COLOR}; 
                background-color: {MEDIUM_BLUE};
                font-size: 10pt;
                padding: 4px;
                min-height: 22px;
            }}
            QStatusBar {{ 
                color: {TEXT_COLOR}; 
                font-size: 9pt;
            }}
        """)
        
        # Central widget with margins
        central = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)  # Reduced margins
        main_layout.setSpacing(8)  # Reduced spacing
        central.setLayout(main_layout)
        self.setCentralWidget(central)
        
        # Status bar with better visibility
        self.status = QStatusBar()
        self.status.setStyleSheet(f"background-color: {DARK_BLUE}; color: {TEXT_COLOR}; padding: 3px;")
        self.setStatusBar(self.status)

        # Connection indicator with better spacing
        indicator_layout = QHBoxLayout()
        indicator_layout.setContentsMargins(3, 3, 3, 5)  # Reduced margins
        self.connection_indicator = QLabel()
        self.connection_indicator.setFixedSize(16, 16)  # Smaller indicator
        self.connection_indicator.setStyleSheet(f"background-color: {RED}; border-radius: 8px;")
        indicator_label = QLabel("THP Sensor Connection")
        indicator_label.setStyleSheet(f"font-weight: bold; font-size: 11pt; color: {TEXT_COLOR};")
        indicator_layout.addWidget(self.connection_indicator)
        indicator_layout.addWidget(indicator_label)
        indicator_layout.addStretch()
        main_layout.addLayout(indicator_layout)

        # Add date/time filter controls with better spacing
        filter_box = QGroupBox("Data Filter")
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(6, 16, 6, 6)  # Reduced internal margins
        filter_layout.setSpacing(6)  # Reduced spacing
        
        # Start datetime
        start_label = QLabel("Start:")
        start_label.setStyleSheet(f"font-weight: bold; color: {TEXT_COLOR};")
        self.start_dt = QDateTimeEdit(QDateTime.currentDateTime().addDays(-1))
        self.start_dt.setCalendarPopup(True)
        self.start_dt.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.start_dt.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # End datetime
        end_label = QLabel("End:")
        end_label.setStyleSheet(f"font-weight: bold; color: {TEXT_COLOR};")
        self.end_dt = QDateTimeEdit(QDateTime.currentDateTime())
        self.end_dt.setCalendarPopup(True)
        self.end_dt.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.end_dt.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Filter button
        self.filter_btn = QPushButton("Apply Filter")
        self.filter_btn.clicked.connect(self.apply_filter)
        self.filter_btn.setMinimumWidth(80)  # Reduced width
        
        # Go Live button
        self.live_btn = QPushButton("Go Live")
        self.live_btn.clicked.connect(self.go_live)
        self.live_btn.setMinimumWidth(80)  # Reduced width
        
        filter_layout.addWidget(start_label)
        filter_layout.addWidget(self.start_dt)
        filter_layout.addWidget(end_label)
        filter_layout.addWidget(self.end_dt)
        filter_layout.addWidget(self.filter_btn)
        filter_layout.addWidget(self.live_btn)
        
        filter_box.setLayout(filter_layout)
        main_layout.addWidget(filter_box)

        # Controllers
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setContentsMargins(0, 5, 0, 5)  # Reduced vertical spacing

        # THP controller with improved styling
        self.thp_ctrl = THPController(parent=self)
        self.thp_ctrl.groupbox.setMinimumHeight(120)  # Reduced height
        self.thp_ctrl.groupbox.setStyleSheet(f"""
            QGroupBox {{
                background-color: {MEDIUM_BLUE};
                color: {TEXT_COLOR};
                border-radius: 6px;
                font-weight: bold;
                font-size: 12pt;
                padding-top: 20px;
                margin-top: 10px;
            }}
            QLabel {{
                color: {TEXT_COLOR};
                font-size: 10pt;
                margin: 3px;
                padding: 3px;
            }}
            QPushButton {{
                background-color: {ROYAL_BLUE};
                color: {TEXT_COLOR};
                border-radius: 4px;
                padding: 6px;
                font-size: 10pt;
                min-height: 25px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: #5A7CC2;
            }}
        """)
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

        # 3 divisions with better spacing
        self.thp_layout = pg.GraphicsLayoutWidget()
        self.thp_layout.setBackground(DARK_BLUE)
        self.thp_layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins
        main_layout.addWidget(self.thp_layout, 1)  # Give plots more space with stretch factor

        # Temperature plot with better title
        self.thp_temp_plot = self.thp_layout.addPlot(row=0, col=0, title="Temperature (°C)", axisItems={'bottom': date_axis_temp})
        self.thp_temp_plot.getAxis('left').setWidth(60)  # Reduced space for axis labels
        self.thp_temp_plot.getAxis('bottom').setHeight(30)  # Reduced space for axis labels
        self.thp_temp_plot.setTitle("Temperature (°C)", size="10pt", color=TEXT_COLOR)  # Smaller title
        self.thp_temp_plot.setLabel('left', 'Temperature', units='°C', **{'font-size': '9pt', 'color': TEXT_COLOR})
        self.thp_temp_plot.addLegend(size=(80, 20), offset=(-10, 10))
        self.thp_temp_curve = self.thp_temp_plot.plot(name="Temp", pen=pg.mkPen(RED, width=2))  # Thinner line
        # Add grid to temperature plot
        self.thp_temp_plot.showGrid(x=True, y=True)
        
        # Add crosshair and data point inspection to temperature plot
        self.temp_vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', width=1))
        self.temp_hLine = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('w', width=1))
        self.thp_temp_plot.addItem(self.temp_vLine, ignoreBounds=True)
        self.thp_temp_plot.addItem(self.temp_hLine, ignoreBounds=True)
        self.temp_label = pg.TextItem(text="", color=TEXT_COLOR, anchor=(0, 0))
        self.temp_label.setFont(QFont("Arial", 8))
        self.thp_temp_plot.addItem(self.temp_label)

        # Humidity plot with better title
        self.hum_plot = self.thp_layout.addPlot(row=1, col=0, title="Humidity (%)", axisItems={'bottom': date_axis_hum})
        self.hum_plot.getAxis('left').setWidth(60)  # Reduced space for axis labels
        self.hum_plot.getAxis('bottom').setHeight(30)  # Reduced space for axis labels
        self.hum_plot.setTitle("Humidity (%)", size="10pt", color=TEXT_COLOR)  # Smaller title
        self.hum_plot.setLabel('left', 'Humidity', units='%', **{'font-size': '9pt', 'color': TEXT_COLOR})
        self.hum_plot.addLegend(size=(80, 20), offset=(-10, 10))
        self.hum_curve = self.hum_plot.plot(name="Humidity", pen=pg.mkPen(LIGHT_BLUE, width=2))  # Thinner line
        # Add grid to humidity plot
        self.hum_plot.showGrid(x=True, y=True)
        
        # Add crosshair and data point inspection to humidity plot
        self.hum_vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', width=1))
        self.hum_hLine = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('w', width=1))
        self.hum_plot.addItem(self.hum_vLine, ignoreBounds=True)
        self.hum_plot.addItem(self.hum_hLine, ignoreBounds=True)
        self.hum_label = pg.TextItem(text="", color=TEXT_COLOR, anchor=(0, 0))
        self.hum_label.setFont(QFont("Arial", 8))
        self.hum_plot.addItem(self.hum_label)

        # Pressure plot with better title
        self.pres_plot = self.thp_layout.addPlot(row=2, col=0, title="Pressure (hPa)", axisItems={'bottom': date_axis_pres})
        self.pres_plot.getAxis('left').setWidth(60)  # Reduced space for axis labels
        self.pres_plot.getAxis('bottom').setHeight(30)  # Reduced space for axis labels
        self.pres_plot.setTitle("Pressure (hPa)", size="10pt", color=TEXT_COLOR)  # Smaller title
        self.pres_plot.setLabel('left', 'Pressure', units='hPa', **{'font-size': '9pt', 'color': TEXT_COLOR})
        self.pres_plot.addLegend(size=(80, 20), offset=(-10, 10))
        self.pres_curve = self.pres_plot.plot(name="Pressure", pen=pg.mkPen(GREEN, width=2))  # Thinner line
        # Add grid to pressure plot
        self.pres_plot.showGrid(x=True, y=True)

        # Add crosshair and data point inspection to pressure plot
        self.pres_vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', width=1))
        self.pres_hLine = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('w', width=1))
        self.pres_plot.addItem(self.pres_vLine, ignoreBounds=True)
        self.pres_plot.addItem(self.pres_hLine, ignoreBounds=True)
        self.pres_label = pg.TextItem(text="", color=TEXT_COLOR, anchor=(0, 0))
        self.pres_label.setFont(QFont("Arial", 8))
        self.pres_plot.addItem(self.pres_label)

        # Set axis colors to white
        self.thp_temp_plot.getAxis('left').setPen(pg.mkPen(color=TEXT_COLOR))
        self.thp_temp_plot.getAxis('left').setTextPen(pg.mkPen(color=TEXT_COLOR))
        self.thp_temp_plot.getAxis('bottom').setPen(pg.mkPen(color=TEXT_COLOR))
        self.thp_temp_plot.getAxis('bottom').setTextPen(pg.mkPen(color=TEXT_COLOR))

        self.hum_plot.getAxis('left').setPen(pg.mkPen(color=TEXT_COLOR))
        self.hum_plot.getAxis('left').setTextPen(pg.mkPen(color=TEXT_COLOR))
        self.hum_plot.getAxis('bottom').setPen(pg.mkPen(color=TEXT_COLOR))
        self.hum_plot.getAxis('bottom').setTextPen(pg.mkPen(color=TEXT_COLOR))

        self.pres_plot.getAxis('left').setPen(pg.mkPen(color=TEXT_COLOR))
        self.pres_plot.getAxis('left').setTextPen(pg.mkPen(color=TEXT_COLOR))
        self.pres_plot.getAxis('bottom').setPen(pg.mkPen(color=TEXT_COLOR))
        self.pres_plot.getAxis('bottom').setTextPen(pg.mkPen(color=TEXT_COLOR))

        # Link x-axes
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
        self.update_timer.setInterval(1000)  # Set fixed interval
        self.live_mode = True
        self.update_timer.start(1000)
        
        # Store all data for filtering
        self.all_timestamps = []
        self.all_temps = []
        self.all_hums = []
        self.all_pressures = []

        # Connect mouse move events
        self.thp_temp_plot.scene().sigMouseMoved.connect(self.mouse_moved_temp)
        self.hum_plot.scene().sigMouseMoved.connect(self.mouse_moved_hum)
        self.pres_plot.scene().sigMouseMoved.connect(self.mouse_moved_pres)
        
        # Hide crosshairs initially
        self.hide_crosshairs()
        
        # Make sure the window resizes properly
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Connect window resize event to update plot layouts
        self.resized = False
        QTimer.singleShot(100, self.delayed_resize)
    
    def delayed_resize(self):
        """Perform a delayed resize to ensure plots are properly laid out"""
        if not self.resized:
            self.resized = True
            self.thp_layout.ci.setSpacing(3)  # Reduce spacing between plots
            # Update plot ranges
            self.thp_temp_plot.autoRange()
            self.hum_plot.autoRange()
            self.pres_plot.autoRange()
    
    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        # Update plot layouts when window is resized
        QTimer.singleShot(100, self.update_plot_layout)
    
    def update_plot_layout(self):
        """Update plot layouts after resize"""
        # Adjust font sizes based on window width
        width = self.width()
        if width < 800:
            font_size = "8pt"
            title_size = "9pt"
        elif width < 1024:
            font_size = "9pt"
            title_size = "10pt"
        else:
            font_size = "10pt"
            title_size = "12pt"
        
        # Update plot titles and labels
        self.thp_temp_plot.setTitle("Temperature (°C)", size=title_size, color=TEXT_COLOR)
        self.thp_temp_plot.setLabel('left', 'Temperature', units='°C', **{'font-size': font_size, 'color': TEXT_COLOR})
        
        self.hum_plot.setTitle("Humidity (%)", size=title_size, color=TEXT_COLOR)
        self.hum_plot.setLabel('left', 'Humidity', units='%', **{'font-size': font_size, 'color': TEXT_COLOR})
        
        self.pres_plot.setTitle("Pressure (hPa)", size=title_size, color=TEXT_COLOR)
        self.pres_plot.setLabel('left', 'Pressure', units='hPa', **{'font-size': font_size, 'color': TEXT_COLOR})
        
        # Update plot ranges
        self.thp_temp_plot.autoRange()
        self.hum_plot.autoRange()
        self.pres_plot.autoRange()

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

        # Store in all-data arrays for filtering
        self.all_timestamps.append(timestamp)
        self.all_temps.append(thpt)
        self.all_hums.append(hum)
        self.all_pressures.append(pres)
        
        # Only update live view if in live mode
        if self.live_mode:
            self.timestamps.append(timestamp)
            self.thp_temps.append(thpt)
            self.hums.append(hum)
            self.pressures.append(pres)
            
            # Limit the number of points shown in live mode to prevent performance issues
            max_points = 3600  # Show at most 1 hour of data at 1 point per second
            if len(self.timestamps) > max_points:
                self.timestamps = self.timestamps[-max_points:]
                self.thp_temps = self.thp_temps[-max_points:]
                self.hums = self.hums[-max_points:]
                self.pressures = self.pressures[-max_points:]
            
            # Update the plots with new data
            self.thp_temp_curve.setData(self.timestamps, self.thp_temps)
            self.hum_curve.setData(self.timestamps, self.hums)
            self.pres_curve.setData(self.timestamps, self.pressures)
            
            # Ensure the timer is running
            if not self.update_timer.isActive():
                self.update_timer.start(1000)

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

    def apply_filter(self):
        """Apply date/time filter to the plots"""
        # Set live mode to False and stop the timer
        self.live_mode = False
        if self.update_timer.isActive():
            self.update_timer.stop()
        
        # Get filter timestamps
        start_ts = self.start_dt.dateTime().toSecsSinceEpoch()
        end_ts = self.end_dt.dateTime().toSecsSinceEpoch()
        
        # Debug message
        self.status.showMessage(f"Filtering data from {datetime.fromtimestamp(start_ts)} to {datetime.fromtimestamp(end_ts)}")
        
        # First check if we have the data in memory
        filtered_data = [(t, temp, h, p) for t, temp, h, p in 
                         zip(self.all_timestamps, self.all_temps, self.all_hums, self.all_pressures) 
                         if start_ts <= t <= end_ts]
        
        # If not enough data in memory, read from CSV file
        if len(filtered_data) < 10:  # Arbitrary threshold
            self.status.showMessage("Reading historical data from CSV file...")
            csv_data = self.read_historical_data(start_ts, end_ts)
            
            if csv_data:
                # Combine with in-memory data
                filtered_data.extend(csv_data)
                # Sort by timestamp
                filtered_data.sort(key=lambda x: x[0])
        
        if not filtered_data:
            self.status.showMessage("No data found in selected range")
            return
        
        # Unpack filtered data
        timestamps, temps, hums, pressures = zip(*filtered_data)
        
        # Update plots with filtered data
        self.timestamps = list(timestamps)
        self.thp_temps = list(temps)
        self.hums = list(hums)
        self.pressures = list(pressures)
        
        # Force update the plots
        self.thp_temp_curve.setData(self.timestamps, self.thp_temps)
        self.hum_curve.setData(self.timestamps, self.hums)
        self.pres_curve.setData(self.timestamps, self.pressures)
        
        # Reset view to show all data
        self.thp_temp_plot.autoRange()
        self.hum_plot.autoRange()
        self.pres_plot.autoRange()
        
        # Hide crosshairs and labels
        self.hide_crosshairs()
        
        self.status.showMessage(f"Showing {len(self.timestamps)} data points from {datetime.fromtimestamp(start_ts)} to {datetime.fromtimestamp(end_ts)}")

    def read_historical_data(self, start_ts, end_ts):
        """Read historical data from CSV file based on timestamp range"""
        data = []
        try:
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
            csv_path = os.path.join(log_dir, "THP_data.csv")
            
            if not os.path.exists(csv_path):
                self.status.showMessage(f"CSV file not found: {csv_path}")
                return data
            
            with open(csv_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        # Skip rows with "None" values
                        if row["thp_temp"] == "None" or row["timestamp"] == "None":
                            continue
                        
                        # Parse timestamp
                        ts_str = row["timestamp"]
                        ts = datetime.fromisoformat(ts_str).timestamp()
                        
                        # Check if in range
                        if start_ts <= ts <= end_ts:
                            temp = float(row["thp_temp"])
                            hum = float(row["humidity"])
                            pres = float(row["pressure"])
                            data.append((ts, temp, hum, pres))
                    except (ValueError, KeyError) as e:
                        # Skip invalid rows
                        continue
                        
            self.status.showMessage(f"Loaded {len(data)} historical data points from CSV")
        except Exception as e:
            self.status.showMessage(f"Error reading CSV: {str(e)}")
        
        return data

    def go_live(self):
        """Switch back to live data mode"""
        self.live_mode = True
        
        # Reset to show only recent data (last hour)
        current_time = datetime.now().timestamp()
        one_hour_ago = current_time - 3600  # 1 hour in seconds
        
        # Filter for recent data
        recent_data = [(t, temp, h, p) for t, temp, h, p in 
                      zip(self.all_timestamps, self.all_temps, self.all_hums, self.all_pressures) 
                      if t >= one_hour_ago]
        
        if recent_data:
            # Unpack recent data
            timestamps, temps, hums, pressures = zip(*recent_data)
            
            # Update plots with recent data
            self.timestamps = list(timestamps)
            self.thp_temps = list(temps)
            self.hums = list(hums)
            self.pressures = list(pressures)
        else:
            # If no recent data, just clear the plots
            self.timestamps = []
            self.thp_temps = []
            self.hums = []
            self.pressures = []
        
        # Update plots
        self.thp_temp_curve.setData(self.timestamps, self.thp_temps)
        self.hum_curve.setData(self.timestamps, self.hums)
        self.pres_curve.setData(self.timestamps, self.pressures)
        
        # Reset view to home position
        self.thp_temp_plot.autoRange()
        self.hum_plot.autoRange()
        self.pres_plot.autoRange()
        
        # Hide crosshairs and labels
        self.hide_crosshairs()
        
        # Stop any existing timer and restart it
        if self.update_timer.isActive():
            self.update_timer.stop()
        
        self.update_timer.start(1000)
        self.status.showMessage("Live mode activated - showing recent data")

    def hide_crosshairs(self):
        """Hide all crosshairs and data labels"""
        # Hide temperature crosshairs and label
        self.temp_vLine.hide()
        self.temp_hLine.hide()
        self.temp_label.hide()
        
        # Hide humidity crosshairs and label
        self.hum_vLine.hide()
        self.hum_hLine.hide()
        self.hum_label.hide()
        
        # Hide pressure crosshairs and label
        self.pres_vLine.hide()
        self.pres_hLine.hide()
        self.pres_label.hide()
    def mouse_moved_temp(self, evt):
        """Handle mouse movement over temperature plot"""
        if self.thp_temp_plot.sceneBoundingRect().contains(evt):
            mouse_point = self.thp_temp_plot.vb.mapSceneToView(evt)
            x = mouse_point.x()
            y = mouse_point.y()
            
            # Update crosshair position
            self.temp_vLine.setPos(x)
            self.temp_hLine.setPos(y)
            self.temp_vLine.show()
            self.temp_hLine.show()
            
            # Find closest data point
            if len(self.timestamps) > 0:
                idx = self.find_closest_point(x, self.timestamps)
                if idx is not None:
                    timestamp = self.timestamps[idx]
                    temp = self.thp_temps[idx]
                    
                    # Format timestamp as readable date
                    date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Update label with data point info
                    self.temp_label.setText(f"Time: {date_str}\nTemp: {temp:.1f}°C")
                    self.temp_label.setPos(x, y)
                    self.temp_label.show()
                else:
                    self.temp_label.hide()
            else:
                self.temp_label.hide()
        else:
            self.temp_vLine.hide()
            self.temp_hLine.hide()
            self.temp_label.hide()

    def mouse_moved_hum(self, evt):
        """Handle mouse movement over humidity plot"""
        if self.hum_plot.sceneBoundingRect().contains(evt):
            mouse_point = self.hum_plot.vb.mapSceneToView(evt)
            x = mouse_point.x()
            y = mouse_point.y()
            
            # Update crosshair position
            self.hum_vLine.setPos(x)
            self.hum_hLine.setPos(y)
            self.hum_vLine.show()
            self.hum_hLine.show()
            
            # Find closest data point
            if len(self.timestamps) > 0:
                idx = self.find_closest_point(x, self.timestamps)
                if idx is not None:
                    timestamp = self.timestamps[idx]
                    hum = self.hums[idx]
                    
                    # Format timestamp as readable date
                    date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Update label with data point info
                    self.hum_label.setText(f"Time: {date_str}\nHumidity: {hum:.1f}%")
                    self.hum_label.setPos(x, y)
                    self.hum_label.show()
                else:
                    self.hum_label.hide()
            else:
                self.hum_label.hide()
        else:
            self.hum_vLine.hide()
            self.hum_hLine.hide()
            self.hum_label.hide()

    def mouse_moved_pres(self, evt):
        """Handle mouse movement over pressure plot"""
        if self.pres_plot.sceneBoundingRect().contains(evt):
            mouse_point = self.pres_plot.vb.mapSceneToView(evt)
            x = mouse_point.x()
            y = mouse_point.y()
            
            # Update crosshair position
            self.pres_vLine.setPos(x)
            self.pres_hLine.setPos(y)
            self.pres_vLine.show()
            self.pres_hLine.show()
            
            # Find closest data point
            if len(self.timestamps) > 0:
                idx = self.find_closest_point(x, self.timestamps)
                if idx is not None:
                    timestamp = self.timestamps[idx]
                    pres = self.pressures[idx]
                    
                    # Format timestamp as readable date
                    date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Update label with data point info
                    self.pres_label.setText(f"Time: {date_str}\nPressure: {pres:.1f} hPa")
                    self.pres_label.setPos(x, y)
                    self.pres_label.show()
                else:
                    self.pres_label.hide()
            else:
                self.pres_label.hide()
        else:
            self.pres_vLine.hide()
            self.pres_hLine.hide()
            self.pres_label.hide()

    def find_closest_point(self, x, x_data):
        """Find the index of the closest point in x_data to the given x value"""
        if not x_data:
            return None
        
        # Convert to numpy array for faster operations if available
        try:
            import numpy as np
            x_array = np.array(x_data)
            idx = (np.abs(x_array - x)).argmin()
            return idx
        except ImportError:
            # Fallback to pure Python
            return min(range(len(x_data)), key=lambda i: abs(x_data[i] - x))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(1200, 900)
    win.show()
    sys.exit(app.exec_())
