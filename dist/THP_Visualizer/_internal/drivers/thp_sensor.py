import serial
import json
import time

def read_thp_sensor_data(port_name, baud_rate=9600, timeout=1):
    try:
        ser = serial.Serial(port_name, baud_rate, timeout=timeout)
        time.sleep(0.5)  # delay
        
        ser.reset_input_buffer()
        
        ser.write(b'p\r\n')

        response = ""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                response += line
                
                # find json
                try:
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
                    continue
        
        # If no JSON
        ser.close()
        print(f"No valid response from THP sensor on {port_name}. Raw response: {response}")
        return None
    except Exception as e:
        print(f"Error connecting to {port_name}: {e}")
        return None
