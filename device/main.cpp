//This is the main firmware code for the Arduino device. It listens for serial commands in the format "LED:<pin>:<state>" and controls the specified LED accordingly. Supported states are "ON" and "OFF". The firmware also sends back responses indicating success or error. HOWEVER THIS CAN ONLY BE COMPLIED IN PLATFORMIO WITH THE ARDUINO FRAMEWORK, NOT IN A STANDARD C++ ENVIRONMENT. :)
//Commands via Serial: LED:<pin>:<ON/OFF>, SERVO:<pin>:<angle>, DOOR:<pin>:<angle>, FAN:<pin>:<ON/OFF>
#include <Arduino.h>
#include <Servo.h>

//pins
const int ledPins[] = {13, 5};
const int ledCount = sizeof(ledPins) / sizeof(ledPins[0]);

const int servoPin = 10;  //Window
const int servoStartPos = 90;

const int doorServoPin = 9;  //Revolving door
int doorPos = 0;

const int fanPin = 6;

//servo objects
Servo win;
Servo door;

//Variables
String inputBuffer = "";
int servoPos = servoStartPos;

//functions declarations
bool isSupportedPin(int pin);
bool isValidServoPin(int pin);
void handleCommand(const String& command);

void setup() {
  //fan
  pinMode(fanPin, OUTPUT);
  digitalWrite(fanPin, LOW);
  
  for (int i = 0; i < ledCount; i++) {
    pinMode(ledPins[i], OUTPUT);
    digitalWrite(ledPins[i], LOW);
  }

  Serial.begin(9600);

  win.attach(servoPin);
  win.write(servoPos);

  //door
  door.attach(doorServoPin);
  door.write(doorPos);
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
  return pin == servoPin || pin == doorServoPin;
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
        digitalWrite(fanPin, HIGH);
        Serial.print("OK:");
        Serial.println(command);
        return;
    }

    if (stateText == "OFF") {
        digitalWrite(fanPin, LOW);
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

      int angle = stateText.toInt();
      if (angle < 0 || angle > 180) {
          Serial.println("ERR:INVALID_ANGLE");
          return;
      }

      doorPos = angle;
      door.write(doorPos);
      Serial.print("OK:DOOR:");
      Serial.print(pin);
      Serial.print(":");
      Serial.println(doorPos);
      return;
  }

  Serial.println("ERR:UNKNOWN_DEVICE");
}