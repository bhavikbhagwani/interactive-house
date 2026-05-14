
/* Smart Home Firmware , so we change in the future if needed */
#include <Servo.h>

const int LED1_PIN = 13;
const int LED2_PIN = 5;
const int FAN_INA_PIN = 7;
const int FAN_INB_PIN = 6;
const int DOOR_PIN = 9;
const int WINDOW_PIN = 10;
const int MOTION_PIN = 2;
const int SMOKE_PIN = A0;
const int TEMP_PIN = A3;
const int ALARM_PIN = 3;

Servo doorServo;
Servo windowServo;
bool alarmActive = false;
int alarmFrequency = 1000;

void handleLED(String cmd);
void handleFan(String cmd);
void handleServo(String cmd);
void handleDoor(String cmd);
void handleAlarm(String cmd);
void handleReadAnalog(String cmd);
void handleReadDigital(String cmd);
void processCommand(String cmd);

void setup() {
  Serial.begin(9600);
  pinMode(LED1_PIN, OUTPUT);
  pinMode(LED2_PIN, OUTPUT);
  pinMode(FAN_INA_PIN, OUTPUT);
  pinMode(FAN_INB_PIN, OUTPUT);
  pinMode(ALARM_PIN, OUTPUT);
  pinMode(MOTION_PIN, INPUT);
  doorServo.attach(DOOR_PIN);
  windowServo.attach(WINDOW_PIN);
  digitalWrite(LED1_PIN, LOW);
  digitalWrite(LED2_PIN, LOW);
  digitalWrite(FAN_INA_PIN, LOW);
  digitalWrite(FAN_INB_PIN, LOW);
  noTone(ALARM_PIN);
  doorServo.write(0);
  windowServo.write(0);
  Serial.println("READY");
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    processCommand(command);
  }
  if (alarmActive) {
    tone(ALARM_PIN, alarmFrequency);
  }
}

void processCommand(String cmd) {
  if (cmd.startsWith("LED:")) handleLED(cmd);
  else if (cmd.startsWith("FAN:")) handleFan(cmd);
  else if (cmd.startsWith("SERVO:")) handleServo(cmd);
  else if (cmd.startsWith("DOOR:")) handleDoor(cmd);
  else if (cmd.startsWith("ALARM:")) handleAlarm(cmd);
  else if (cmd.startsWith("READ_ANALOG:")) handleReadAnalog(cmd);
  else if (cmd.startsWith("READ_DIGITAL:")) handleReadDigital(cmd);
  else if (cmd == "PING") Serial.println("PONG");
  else Serial.println("ERROR:UNKNOWN_CMD");
}

void handleLED(String cmd) {
  int firstColon = cmd.indexOf(':');
  int secondColon = cmd.indexOf(':', firstColon + 1);
  int pin = cmd.substring(firstColon + 1, secondColon).toInt();
  String action = cmd.substring(secondColon + 1);
  if (action == "ON") {
    digitalWrite(pin, HIGH);
    Serial.println("OK:LED:" + String(pin) + ":ON");
  } else if (action == "OFF") {
    digitalWrite(pin, LOW);
    Serial.println("OK:LED:" + String(pin) + ":OFF");
  } else if (action.startsWith("PWM:")) {
    int value = action.substring(4).toInt();
    analogWrite(pin, constrain(value, 0, 255));
    Serial.println("OK:LED:" + String(pin) + ":PWM:" + String(value));
  }
}

void handleFan(String cmd) {
  int firstColon = cmd.indexOf(':');
  String action = cmd.substring(firstColon + 1);
  if (action == "ON") {
    digitalWrite(FAN_INA_PIN, HIGH);
    digitalWrite(FAN_INB_PIN, LOW);
    Serial.println("OK:FAN:ON");
  } else if (action == "OFF") {
    digitalWrite(FAN_INA_PIN, LOW);
    digitalWrite(FAN_INB_PIN, LOW);
    Serial.println("OK:FAN:OFF");
  } else if (action.startsWith("SPEED:")) {
    int value = action.substring(6).toInt();
    analogWrite(FAN_INA_PIN, constrain(value, 0, 255));
    digitalWrite(FAN_INB_PIN, LOW);
    Serial.println("OK:FAN:SPEED:" + String(value));
  }
}

void handleServo(String cmd) {
  int firstColon = cmd.indexOf(':');
  int secondColon = cmd.indexOf(':', firstColon + 1);
  int pin = cmd.substring(firstColon + 1, secondColon).toInt();
  int angle = cmd.substring(secondColon + 1).toInt();
  angle = constrain(angle, 0, 180);
  if (pin == DOOR_PIN) doorServo.write(angle);
  else if (pin == WINDOW_PIN) windowServo.write(angle);
  Serial.println("OK:SERVO:" + String(pin) + ":" + String(angle));
}

void handleDoor(String cmd) {
  int firstColon = cmd.indexOf(':');
  int secondColon = cmd.indexOf(':', firstColon + 1);
  int pin = cmd.substring(firstColon + 1, secondColon).toInt();
  String action = cmd.substring(secondColon + 1);
  if (action == "OPEN") {
    if (pin == DOOR_PIN) doorServo.write(90);
    else if (pin == WINDOW_PIN) windowServo.write(90);
    Serial.println("OK:DOOR:" + String(pin) + ":OPEN");
  } else if (action == "CLOSE") {
    if (pin == DOOR_PIN) doorServo.write(0);
    else if (pin == WINDOW_PIN) windowServo.write(0);
    Serial.println("OK:DOOR:" + String(pin) + ":CLOSE");
  }
}

void handleAlarm(String cmd) {
  int firstColon = cmd.indexOf(':');
  int secondColon = cmd.indexOf(':', firstColon + 1);
  int thirdColon = cmd.indexOf(':', secondColon + 1);
  int pin = cmd.substring(firstColon + 1, secondColon).toInt();
  String action;
  if (thirdColon > 0) {
    action = cmd.substring(secondColon + 1, thirdColon);
  } else {
    action = cmd.substring(secondColon + 1);
  }
  if (action == "ON") {
    if (thirdColon > 0) alarmFrequency = cmd.substring(thirdColon + 1).toInt();
    alarmActive = true;
    tone(pin, alarmFrequency);
    Serial.println("OK:ALARM:" + String(pin) + ":ON:" + String(alarmFrequency));
  } else if (action == "OFF") {
    alarmActive = false;
    noTone(pin);
    Serial.println("OK:ALARM:" + String(pin) + ":OFF");
  } else if (action == "TEST") {
    tone(pin, 1000, 200);
    Serial.println("OK:ALARM:" + String(pin) + ":TEST");
  }
}

void handleReadAnalog(String cmd) {
  int colon = cmd.indexOf(':');
  String pinText = cmd.substring(colon + 1);
  pinText.trim();

  int pin;

  if (pinText == "A0") {
    pin = A0;
  } else if (pinText == "A1") {
    pin = A1;
  } else if (pinText == "A2") {
    pin = A2;
  } else if (pinText == "A3") {
    pin = A3;
  } else if (pinText == "A4") {
    pin = A4;
  } else if (pinText == "A5") {
    pin = A5;
  } else {
    pin = pinText.toInt();
  }

  int value = analogRead(pin);
  Serial.println("VALUE:" + pinText + ":" + String(value));
}

void handleReadDigital(String cmd) {
  int colon = cmd.indexOf(':');
  int pin = cmd.substring(colon + 1).toInt();
  int value = digitalRead(pin);
  Serial.println("VALUE:" + String(pin) + ":" + String(value));
}