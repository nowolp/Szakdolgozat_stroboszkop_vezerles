#include <SPI.h>
#include <Wire.h>
#include <Adafruit_MAX31855.h>
#include <Adafruit_ADS1X15.h>

// infra homero
const float SHUNT_RESISTOR = 154.0; // precizios meroellenallas
const float IR_TEMP_MIN    = 0.0;   // homerseklet 4mA
const float IR_TEMP_MAX    = 500.0; // homerseklet 20 mA

//K types senzorok gpiok
#define MAXDO   19
#define MAXCLK  18
#define CS1     5
#define CS2     17
#define CS3     16

Adafruit_MAX31855 t1(MAXCLK, CS1, MAXDO);
Adafruit_MAX31855 t2(MAXCLK, CS2, MAXDO);
Adafruit_MAX31855 t3(MAXCLK, CS3, MAXDO);

Adafruit_ADS1115 ads; 

//tovabbi gpiok
#define TRIGGER_PIN 27 
#define FAN_PIN     26 
#define OPTO_PIN    25 

unsigned long lastMillis = 0;
const int timer100ms = 100;

// Stroboszkop beallitasok
bool strobeActive = false;
int targetFlashes = 0;
long targetInterval = 0;
int targetCycles = 0;

int currentCycles = 0;
unsigned long lastSequenceTime = 0;
bool inSequenceDelay = false;

volatile bool optoTriggered = false;

void IRAM_ATTR optoISR() {
  optoTriggered = true;
}

void setup() {
  Serial.begin(115200);
  
  pinMode(TRIGGER_PIN, OUTPUT);
  pinMode(FAN_PIN, OUTPUT);
  digitalWrite(TRIGGER_PIN, LOW);
  digitalWrite(FAN_PIN, LOW);
  
  pinMode(OPTO_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(OPTO_PIN), optoISR, FALLING); 

  t1.begin();
  t2.begin();
  t3.begin();
  
  ads.begin(); 
}

void loop() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    
    if (cmd == "F1") {
      digitalWrite(FAN_PIN, HIGH); 
    } else if (cmd == "F0") {
      digitalWrite(FAN_PIN, LOW);  
    } else if (cmd.startsWith("S")) {
      sscanf(cmd.c_str(), "S%d,%ld,%d", &targetFlashes, &targetInterval, &targetCycles);
      strobeActive = true;
      currentCycles = 0;
      inSequenceDelay = false;
    } else if (cmd == "X") {
      strobeActive = false;
      digitalWrite(TRIGGER_PIN, LOW);
    }
  }

  // stroboszkop vezerles
  if (strobeActive) {
    if (!inSequenceDelay) {
      for (int i = 0; i < targetFlashes; i++) {
        if (!strobeActive) break; 
        
        digitalWrite(TRIGGER_PIN, HIGH);
        delayMicroseconds(100); 
        digitalWrite(TRIGGER_PIN, LOW);
        
        if (i < targetFlashes - 1) {
          delay(50); 
        }
      }
      
      currentCycles++;
      if (currentCycles >= targetCycles) {
        strobeActive = false; 
      } else {
        inSequenceDelay = true;
        lastSequenceTime = millis();
      }
    } else {
      if (millis() - lastSequenceTime >= (unsigned long)targetInterval) {
        inSequenceDelay = false;
      }
    }
  }

  //adatok olvasasa
  if (millis() - lastMillis >= timer100ms) {
    lastMillis = millis();

    float temp1 = t1.readCelsius();
    float temp2 = t2.readCelsius();
    float temp3 = t3.readCelsius();
    
    int16_t adc0 = ads.readADC_SingleEnded(0); 
    
    float voltage = (adc0 * 0.1875) / 1000.0; 
    float current_mA = (voltage / SHUNT_RESISTOR) * 1000.0; 
    
    // T_min + (Aktuális_mA - 4mA) * ((T_max - T_min) / (20mA - 4mA))
    float temp4 = IR_TEMP_MIN + (current_mA - 4.0) * ((IR_TEMP_MAX - IR_TEMP_MIN) / 16.0);
    // ---------------------------------
    
    int optoStatus = optoTriggered ? 1 : 0;
    optoTriggered = false; 

    // adatok kuldese
    Serial.print(millis()); Serial.print(",");
    Serial.print(isnan(temp1) ? "Error" : String(temp1)); Serial.print(",");
    Serial.print(isnan(temp2) ? "Error" : String(temp2)); Serial.print(",");
    Serial.print(isnan(temp3) ? "Error" : String(temp3)); Serial.print(",");
    Serial.print(temp4, 2); Serial.print(",");
    Serial.println(optoStatus);
  }
}