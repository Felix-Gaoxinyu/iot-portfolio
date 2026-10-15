/*
 * Sensors and Actuators (Sensorik und Aktorik) - HSBI
 * Module 0 pre-study mini-exercise: analog in -> digital -> analog out
 *
 * Wokwi: ESP32 (C++/Arduino). Signal chain shown:
 *   pot wiper voltage -> ESP32 SAR ADC -> integer code -> 8-bit PWM duty -> LED brightness
 *
 * Change ADC_BITS between 8, 10 and 12 and watch the code range in the Serial Monitor.
 */

const int PIN_POT = 34;   // ADC1_CH6 - input-only pin, safe on ESP32
const int PIN_LED = 25;   // LEDC-capable output pin

const int ADC_BITS = __ADC_BITS__;  // 8, 10 or 12  <-- change this and watch the range

// Extension: a deliberately coarse threshold, to make the output "jump"
const bool USE_COARSE_THRESHOLD = __COARSE__;
const int  COARSE_LEVELS = 4;   // only 4 brightness levels instead of 256

int adcMax = (1 << ADC_BITS) - 1;

void setup() {
  Serial.begin(115200);

  // ESP32 note: 9..12 change the hardware resolution; any other value is
  // produced by shifting the 12-bit result in software.
  analogReadResolution(ADC_BITS);

  // Documented measurable window with 11 dB attenuation: 150 mV .. 3100 mV.
  analogSetAttenuation(ADC_11db);

  pinMode(PIN_LED, OUTPUT);

  Serial.println();
  Serial.println("=== Sensors and Actuators - Module 0 pre-study ===");
  Serial.printf("ADC resolution %d bit -> codes 0..%d (%d discrete steps)\n",
                ADC_BITS, adcMax, adcMax + 1);
  Serial.println("Potentiometer on GPIO34, LED on GPIO25");
  Serial.println("-----------------------------------------------");
}

void loop() {
  int raw = analogRead(PIN_POT);            // 0 .. adcMax
  int mv  = analogReadMilliVolts(PIN_POT);  // calibrated millivolts

  int brightness;
  if (USE_COARSE_THRESHOLD) {
    int bucket = (raw * COARSE_LEVELS) / (adcMax + 1);     // 0..3
    brightness = map(bucket, 0, COARSE_LEVELS - 1, 0, 255);
  } else {
    brightness = (int)((long)raw * 255L / adcMax);
  }

  analogWrite(PIN_LED, brightness);         // LEDC, 8-bit duty on ESP32

  Serial.printf("raw=%4d/%4d  %4d mV  duty=%3d  %5.1f%%\n",
                raw, adcMax, mv, brightness, brightness * 100.0 / 255.0);

  delay(400);   // slow enough to read in the Serial Monitor
}
