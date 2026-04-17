#include <Wire.h>
#include <Adafruit_ADS1X15.h>

Adafruit_ADS1115 ads;

void setup() {
  Serial.begin(115200);
  
  // Initialize I2C on the ESP32-S3 (Default Stemma QT pins)
  if (!ads.begin()) {
    Serial.println("Failed to initialize ADS1115.");
    while (1);
  }

  // Set Gain to 16x to detect tiny millivolt signals
  // +/- 0.256V range | 1 bit = 0.0078125mV
  ads.setGain(GAIN_SIXTEEN);

  // Set data rate to highest speed (860 samples per second)
  ads.setDataRate(RATE_ADS1115_860SPS);
}

void loop() {
  // Read differential voltage between A0 and A1
  int16_t results = ads.readADC_Differential_0_1();

  // Convert to voltage if needed for analysis
  float voltage = ads.computeVolts(results);

  // Output to Serial Plotter for visual detection
  Serial.print("Raw:");
  Serial.print(results);
  Serial.print(",");
  Serial.print("Voltage:");
  Serial.println(voltage, 6);

  // Small delay to prevent saturating the serial buffer 
  // though 860SPS is well within ESP32-S3 limits
}