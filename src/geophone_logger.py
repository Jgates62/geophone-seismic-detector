import serial
import csv
from datetime import datetime, timezone
import keyboard
import sys

# Configuration
SERIAL_PORT = 'COM4'
BAUD_RATE = 115200

# Generate safe filename with date and time (colons replaced with hyphens)
timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename = f"seismic_data_{timestamp_str}.csv"

def main():
    try:
        # Initialize serial connection
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
    except serial.SerialException as e:
        print(f"Error opening serial port {SERIAL_PORT}: {e}")
        sys.exit(1)

    print(f"Logging data to {filename}...")
    print("Hold 'SHIFT' to record an event. Press 'Ctrl+C' in this window to stop and save.")

    # Open CSV file for writing
    with open(filename, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        
        # Write headers
        writer.writerow(['UTC_Timestamp', 'Raw_Value', 'Voltage', 'Filtered', 'Event_Flag'])

        try:
            # Flush any incomplete data currently in the serial buffer
            ser.reset_input_buffer() 
            
            while True:
                if ser.in_waiting > 0:
                    # Read and decode the serial line
                    line = ser.readline().decode('utf-8').strip()
                    
                    # Generate the current UTC timestamp
                    utc_now = datetime.now(timezone.utc).isoformat()
                    
                    # Detect if the shift key is actively being held down
                    event_flag = 1 if keyboard.is_pressed('shift') else 0

                    # Parse the "Raw:XXXX,Voltage:YYYY" string into separate columns
                    try:
                        parts = line.split(',')
                        raw_val = parts[0].split(':')[1]
                        voltage_val = parts[1].split(':')[1]
                        filtered_val = parts[2].split(':')[1]
                        
                        writer.writerow([utc_now, raw_val, voltage_val, filtered_val, event_flag])
                        
                    except IndexError:
                        # Fallback if the serial line is garbled or booting up
                        writer.writerow([utc_now, line, '', '', event_flag])

        except KeyboardInterrupt:
            print("\nLogging stopped by user.")
        finally:
            ser.close()
            print(f"Serial port closed. Data saved to {filename}.")

if __name__ == "__main__":
    main()