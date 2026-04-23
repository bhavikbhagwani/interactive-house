//This is the main firmware code for the Arduino device. It listens for serial commands in the format "LED:<pin>:<state>" and controls the specified LED accordingly. Supported states are "ON" and "OFF". The firmware also sends back responses indicating success or error. HOWEVER THIS CAN ONLY BE COMPLIED IN PLATFORMIO WITH THE ARDUINO FRAMEWORK, NOT IN A STANDARD C++ ENVIRONMENT. :)
//Commands via Serial: LED:<pin>:<ON/OFF>, SERVO:<pin>:<angle>, DOOR:<pin>:<angle>, FAN:<pin>:<ON/OFF>
#include <Arduino.h>
#include <Servo.h>

//pins
const int ledPins[] = {13, 5};
const int ledCount = sizeof(ledPins) / sizeof(ledPins[0]);

const int servoPin = 10;  //Window
const int servoStartPos = 90;

const int doorServoPin = 9;  //Door
const int doorStartPos = 90;

const int fanPin = 6;
const bool fanActiveLow = true; //if someone dare try it false and flushes in platformIO >:) //i figured it out ;) < C

const int doorOpenAngle = 180;   
const int doorCloseAngle = 0;    
const int doorStopAngle = 90; 

// Sending motion sensor state
const int motionSensorPin = 2;
int lastMotionState = LOW;

//servo objects
Servo win;
Servo door;

//Variables
String inputBuffer = "";
int servoPos = servoStartPos;
int doorPos = doorStartPos;

//functions declarations
bool isSupportedPin(int pin);
bool isValidServoPin(int pin);
void handleCommand(const String& command);
void setFanState(bool on);
int fanSignalLevel(bool on);

int fanSignalLevel(bool on) {
  if (fanActiveLow) {
    return on ? LOW : HIGH;
  }
  return on ? HIGH : LOW;
}

void setFanState(bool on) {
  digitalWrite(fanPin, fanSignalLevel(on));
}

void setup() {
  // Motion Sensor
  pinMode(motionSensorPin, INPUT);

  //fan
  pinMode(fanPin, OUTPUT);
  setFanState(false);
  //digitalWrite(fanPin, LOW);
  
  for (int i = 0; i < ledCount; i++) {
    pinMode(ledPins[i], OUTPUT);
    digitalWrite(ledPins[i], LOW);
  }

  Serial.begin(9600);

  win.attach(servoPin);
  win.write(servoPos);

  //door
  door.attach(doorServoPin);
  door.write(doorStartPos);
}

void loop() {
  while (Serial.available() > 0) {
    char incoming = static_cast<char>(Serial.read());

    if (incoming == '\n') {
      inputBuffer.trim();
      if (inputBuffer.length() > 0) {
        handleCommand(inputBuffer);
      }
      inputBuffer = "";
    } else if (incoming != '\r') {
      inputBuffer += incoming;
    }
  }

  // Added Motion Sensor
  int motionState = digitalRead(motionSensorPin);

  if (motionState != lastMotionState) {
    lastMotionState = motionState;

    if (motionState == HIGH) {
      Serial.println("MOTION:1");
    } else {
      Serial.println("MOTION:0");
    }
  }

  delay(100);
}

bool isSupportedPin(int pin) {
  for (int i = 0; i < ledCount; i++) {
    if (ledPins[i] == pin) {
      return true;
    }
  }
  return false;
}

bool isValidServoPin(int pin) {
  return pin == servoPin;
}

void handleCommand(const String& command) {
  int firstColon = command.indexOf(':');
  int secondColon = command.indexOf(':', firstColon + 1);

  if (firstColon < 0 || secondColon < 0) {
    Serial.println("ERR:INVALID_FORMAT");
    return;
  }

  String deviceType = command.substring(0, firstColon);
  String pinText = command.substring(firstColon + 1, secondColon);
  String stateText = command.substring(secondColon + 1);

  int pin = pinText.toInt();

  if (deviceType == "LED") {
    if (!isSupportedPin(pin)) {
      Serial.println("ERR:UNSUPPORTED_PIN");
      return;
    }

    if (stateText == "ON") {
      digitalWrite(pin, HIGH);
      Serial.print("OK:");
      Serial.println(command);
      return;
    }

    if (stateText == "OFF") {
      digitalWrite(pin, LOW);
      Serial.print("OK:");
      Serial.println(command);
      return;
    }

    Serial.println("ERR:UNKNOWN_STATE");
    return;
  }

  if (deviceType == "SERVO") {
    if (!isValidServoPin(pin)) {
      Serial.println("ERR:UNSUPPORTED_PIN");
      return;
    }

    int angle = stateText.toInt();
    if (angle < 0 || angle > 180) {
      Serial.println("ERR:INVALID_ANGLE");
      return;
    }

    servoPos = angle;
    win.write(servoPos);
    Serial.print("OK:SERVO:");
    Serial.print(pin);
    Serial.print(":");
    Serial.println(servoPos);
    return;
  }

  if (deviceType == "FAN") {
    if (pin != fanPin) {
        Serial.println("ERR:UNSUPPORTED_PIN");
        return;
    }

    if (stateText == "ON") {
        setFanState(true);
        Serial.print("OK:");
        Serial.println(command);
        return;
    }

    if (stateText == "OFF") {
        setFanState(false);
        Serial.print("OK:");
        Serial.println(command);
        return;
    }

    Serial.println("ERR:UNKNOWN_STATE");
    return;
}

  if (deviceType == "DOOR") {
    if (pin != doorServoPin) {
        Serial.println("ERR:UNSUPPORTED_PIN");
        return;
    }
    // Continuous rotation mapping
    if (stateText == "OPEN") {
      door.write(doorOpenAngle);
    } else if (stateText == "CLOSE") {
      door.write(doorCloseAngle);
    } else if (stateText == "STOP") {
      door.write(doorStopAngle);
    } else {
        Serial.println("ERR:UNKNOWN_STATE");
        return;
    }

    Serial.print("OK:DOOR:");
    Serial.print(pin);
    Serial.print(":");
    Serial.println(stateText);
    return;
  }

  Serial.println("ERR:UNKNOWN_DEVICE");

}
