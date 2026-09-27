#include <ESP32Servo.h>

Servo myServo;
int servoPin = 23;
void setup() {
  // put your setup code here, to run once:
  myServo.attach(servoPin);
  Serial.begin(115200);
}
void loop() {
  // put your main code here, to run repeatedly:
  if(Serial.available()){
    int angle = Serial.parseInt();
    myServo.write(angle);
  }
  delay(20);
}
