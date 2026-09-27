#include <Servo.h>

// Number of motors
const int numMotors = 8;
Servo motors[numMotors];

// GPIO pins for each servo (adjust as needed)
int servoPins[numMotors] = {2, 4, 5, 12, 13, 14, 15, 16};  

void setup() {
  Serial.begin(115200);

  // Attach all servos
  for (int i = 0; i < numMotors; i++) {
    motors[i].attach(servoPins[i]);
    motors[i].writeMicroseconds(1500); // Start all servos at neutral position
  }

  Serial.println("Enter pulse width (1000 - 2000) to move all motors.");
}

void loop() {
  if (Serial.available() > 0) {
    int pulseWidth = Serial.parseInt();

    if (pulseWidth >= 1000 && pulseWidth <= 2000) {
      // Apply pulse width to all motors
      for (int i = 0; i < numMotors; i++) {
        motors[i].writeMicroseconds(pulseWidth);
        delay(2); // Small delay for stability
        yield();  // Reset watchdog timer (prevents WDT reset)
      }
      Serial.print("All motors set to: ");
      Serial.println(pulseWidth);
    }
  }
  delay(10); // Prevent watchdog reset
  yield();   // Allow ESP8266 background tasks to run
}
