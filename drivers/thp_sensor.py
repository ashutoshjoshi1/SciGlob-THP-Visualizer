import serial
import json
import time

def read_thp_sensor_data(port_name, baud_rate=9600, timeout=1):
    try:
        ser = serial.Serial(port_name, baud_rate, timeout=timeout)
        time.sleep(1)
        ser.write(b'p\r\n')

        response = ""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                response += line
                # Try to find JSON data in the response
                try:
                    # Find the start of JSON data (first '{')
                    json_start = response.find('{')
                    if json_start >= 0:
                        json_data = response[json_start:]
                        data = json.loads(json_data)
                        ser.close()
                        sensors = data.get('Sensors', [])
                        if sensors:
                            s = sensors[0]
                            return {
                                'sensor_id': s.get('ID'),
                                'temperature': s.get('Temperature'),
                                'humidity': s.get('Humidity'),
                                'pressure': s.get('Pressure')
                            }
                except json.JSONDecodeError:
                    # Continue collecting more data
                    continue
        
        # If we get here, we timed out without valid JSON
        ser.close()
        print(f"No valid response from THP sensor. Raw response: {response}")
        return None
    except Exception as e:
        print(f"THP sensor error: {e}")
        return None
