String inBytes;

void setup() {
  // put your setup code here, to run once:
Serial.begin(9600);
pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  // put your main code here, to run repeatedly:
  if(Serial.available()>0) {
    inBytes = Serial.readStringUntil('\n');
    if (inBytes == "on") {
      digitalWrite(LED_BUILTIN, HIGH);
      Serial.print("Led on");
    } 
    if (inBytes == "on") {
      digitalWrite(LED_BUILTIN, LOW);
      Serial.print("Led off");
    } else {
      Serial.print("invalid input");
    }
  }
}
