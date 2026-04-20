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

// Low-Pass + High-Pass filter constants
float lowPass = 0.0;
float highPass = 0.0;
const float alphaLP = 0.15; // 0.15 = 24.1Hz, 0.25 = 45Hz
const float alphaHP = 0.05; // 0.05 = 7.2Hz, 0.08 = 12Hz

void loop() {
  // Read differential voltage between A0 and A1
  int16_t results = ads.readADC_Differential_0_1();

  // Convert to voltage if needed for analysis
  float voltage = ads.computeVolts(results);

  // High-Pass Filter (Removes DC drift/slow ground sway)
  highPass = alphaHP * (highPass + voltage - lowPass); 
  
  // Low-Pass Filter (Removes high-frequency electronic hiss)
  lowPass = lowPass + alphaLP * (voltage - lowPass);

  // The "Filtered" signal is the difference or the band-limited result
  float filteredSignal = lowPass - highPass;

  // Output to Serial Plotter for visual detection
  Serial.print("Raw:");
  Serial.print(results);
  Serial.print(",Voltage:");
  Serial.print(voltage, 6);
  Serial.print(",Filtered:");
  Serial.println(filteredSignal, 6);

}