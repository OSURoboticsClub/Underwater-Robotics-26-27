import processing.serial.*;

import net.java.games.input.*;
import org.gamecontrolplus.*;
import org.gamecontrolplus.gui.*;

import cc.arduino.*;
import org.firmata.*;

//declare a lot of variables
ControlDevice cont;
ControlIO control;

Arduino ard0;


int dPad;
GamepadEx lStickYActivity = new GamepadEx(new Button(){boolean inputCode(){return Math.abs(cont.getSlider("lStickY").getValue())>0.05;}});
GamepadEx lStickXActivity = new GamepadEx(new Button(){boolean inputCode(){return Math.abs(cont.getSlider("lStickX").getValue())>0.05;}});
GamepadEx rStickYActivity = new GamepadEx(new Button(){boolean inputCode(){return Math.abs(cont.getSlider("rStickY").getValue())>0.05;}});
GamepadEx rStickXActivity = new GamepadEx(new Button(){boolean inputCode(){return Math.abs(cont.getSlider("rStickX").getValue())>0.05;}});

GamepadEx a = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("a").getValue()!=0;}});
GamepadEx b = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("b").getValue()!=0;}});
GamepadEx x = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("x").getValue()!=0;}});
GamepadEx y = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("y").getValue()!=0;}});

GamepadEx lStickB = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("lStickB").getValue()!=0;}});
GamepadEx rStickB = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("rStickB").getValue()!=0;}});

GamepadEx lT = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("lT").getValue()!=0;}});
GamepadEx rT = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("rT").getValue()!=0;}});
GamepadEx lB = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("lB").getValue()!=0;}});
GamepadEx rB = new GamepadEx(new Button(){boolean inputCode(){return cont.getButton("rB").getValue()!=0;}});

GamepadEx dPadLeft  = new GamepadEx(new Button(){boolean inputCode(){return dPad==1 || dPad==8 || dPad==7;}});
GamepadEx dPadRight = new GamepadEx(new Button(){boolean inputCode(){return dPad==3 || dPad==4 || dPad==5;}});
GamepadEx dPadUp    = new GamepadEx(new Button(){boolean inputCode(){return dPad==1 || dPad==2 || dPad==3;}});
GamepadEx dPadDown  = new GamepadEx(new Button(){boolean inputCode(){return dPad==5 || dPad==6 || dPad==7;}});




//Storing controller button values
float forward;
float strafe;
float yaw;

float lift;
float roll;
float pitch;
//float liftadj;

//Final lateral motor speed calculations
float mFL;  //Motor Front-Left
float mBL;  //Motor Back-Left
float mFR;  //Motor Front-Right
float mBR;  //Motor Back-Right

//Fore-Aft motor speed command
float mFLf; //Motor Front-Left fore-aft
float mBLf; //Motor Back-Left fore-aft
float mFRf; //Motor Front-Right fore-aft
float mBRf; //Motor Back-Right fore-aft

//Strafe motor speed command
float mFLs; //Motor Front-Left strafe
float mBLs; //Motor Back-Left strafe
float mFRs; //Motor Front-Right strafe
float mBRs; //Motor Back-Right strafe

//Yaw motor speed command
float mFLy; //Motor Front-Left yaw
float mBLy; //Motor Back-Left yaw
float mFRy; //Motor Front-Right yaw
float mBRy; //Motor Back-Right yaw

//Final vertical motor speed calculation
float vFL;  //z-axis Motor Front-Left
float vBL;  //z-axis Motor Back-Left
float vFR;  //z-axis Motor Front-Right
float vBR;  //z-axis Motor Back-Right

//Up-Down motor speed command
float vFLu; //Motor Front-Left up-down
float vBLu; //Motor Back-Left up-down
float vFRu; //Motor Front-Right up-down
float vBRu; //Motor Back-Right up-down

//Roll motor speed command
float vFLr; //Motor Front-Left roll
float vBLr; //Motor Back-Left roll
float vFRr; //Motor Front-Right roll
float vBRr; //Motor Back-Right roll

//Pitch motor speed command
float vFLp; //Motor Front-Left pitch
float vBLp; //Motor Back-Left pitch
float vFRp; //Motor Front-Right yaw
float vBRp; //Motor Back-Right yaw

//Toggle for whether or not motors are slow
int vSlow;//vertical slowdown
int lSlow;//lateral slowdown

//Actuator toggles
boolean mainac;
boolean sideac;

//Actuator inputs
boolean mainacpress = false;
boolean sideacpress = false;

//Motion of manipulators
int mainRot;
int mainTip;
int sidepos;

//Motion of camera
int camAng = 90;


/*
The ESCs and the servos take different PWM ranges. In order for this program to work properly,
go into the Firmata file that accompanies this and change the variables: 
  servo180_upper,  servo180_lower            pins: 44, 45, 46
  servo270_upper,  servo270_lower            pins: 2, 3, 4, 5
  esc_upper,  esc_lower                      pins: 6, 7, 8, 9, 10, 11, 12, 13
By modifying these variables, the code will automatically map the 0-180 degree range the 
servo.write() command in Processing uses to the proper PWM values. Not changing these would
make the devices move incorrectly. The code refers to pins on the Arduino Mega 2560 Rev3.

The PWM ranges on the pins are set in the Firmata program, and can be modified to accommodate
more of a type of device or an entirely new device being used.

More Pin Documentation:

  /‾‾‾‾/   Front   \‾‾‾‾\
 / 13 /             \ 12 \
/____/               \____\
|‾‾‾‾|               |‾‾‾‾|
| ## |               | ## |
|____|               |____|
  
|‾‾‾‾|               |‾‾‾‾|
| ## |               | ## |
|____|               |____|
\‾‾‾‾\               /‾‾‾‾/
 \ 9  \             / 8  /
  \____\    Back   /____/
*/

int frontLeftLateralThruster = 13;
int backLeftLateralThruster = 9;
int frontRightLateralThruster = 12;
int backRightLateralThruster = 8;

int frontLeftVerticalThruster = 0;
int backLeftVerticalThruster = 0;
int frontRightVerticalThruster = 0;
int backRightVerticalThruster = 0;

int camTip = 4;

PFont monospace;
PFont sansSerif;
PImage clawCl;
PImage clawOp;
PImage iso;
PImage side;
int lIndent = 25;
String[] wireFrame = {"  /‾‾‾‾‾‾/"," Front     ","\\‾‾‾‾‾‾\\\n",
                  " / 13 /","             ","\\ 12 \\\n",
                  "/____/","               ","\\____\\\n",
                  "\n","","",
                  "|‾‾‾‾‾‾|","               ","|‾‾‾‾‾‾|\n",
                  "| ## |","               ","| ## |\n",
                  "|____|","               ","|____|\n",
                  "\n","","",
                  "|‾‾‾‾‾‾|","               ","|‾‾‾‾‾‾|\n",
                  "| ## |","               ","| ## |\n",
                  "|____|","               ","|____|\n",
                  "\n","","",
                  "\\‾‾‾‾‾‾\\","               ","/‾‾‾‾‾‾/\n",
                  " \\ 09 \\","             ","/ 08 /\n",
                  "  \\____\\","    Back   ","/____/\n"
                };
int[] hex = new int[45];
int startx = 250;
int starty = 300;
int[] xs = new int[45];
int[] ys = new int[45];

/*
Unassigned PWM Pins:
  esc: 6, 7, 10, 11
  servo270: 2
  servo180: 44, 45, 46
  Other: 3, 5, 7, 15
*/

void setup () {
  
  //sets the size of the window that pops up when you press run
  
  /* Check the available fonts
  String[] a = PFont.list();
  for(String b: a) {
    println(b);
  }
  sans-serif
  Monospaced.plain
  Monotxt
  */
  size(600,600);
  textSize(25);
  monospace = createFont("Monospaced.plain",25);
  sansSerif = createFont("SansSerif",25);
  textFont(sansSerif);
  for(int i=0;i<hex.length;i++) {
    hex[i]=#ffffff;
  }
  for(int i=0;i<xs.length;i++) {
    switch(i%3) {
      case 0:
        xs[i]=startx;
        break;
      case 1:
        xs[i]=startx+wireFrame[i-1].length()*12;
        break;
      case 2:
      if(i==2||i==14||i==26||i==38) {
        xs[i]=startx+(wireFrame[i-2].length()-2)*12+wireFrame[i-1].length()*12;
      } else {
        xs[i]=startx+wireFrame[i-2].length()*12+wireFrame[i-1].length()*12;
      }
        break;
    }
  }
  for(int i=0;i<ys.length;i++) {
    ys[i]=starty+20*(i/3);
  }
  //loads the wireframe images to the variable names
  clawCl = loadImage("RobotWireframeClawClosed.PNG");
  clawOp = loadImage("RobotWireframeClawOpen.PNG");
  iso = loadImage("RobotWireframeIso.PNG");
  side = loadImage("RobotWireframeSide.PNG");
      
  //println(Arduino.list());    //Uncomment this to make the code print the COM ports available, then switch
                                //the information in the initialize line to the correct COM port list location
  
  //Initializes the Arduino
  ard0 = new Arduino(this, Arduino.list()[2], 57600);
  
  //Sets all the PWM pins to output PWM, this way it won't ever need to be changed later. 
  ard0.pinMode(camTip, Arduino.SERVO); 
  ard0.pinMode(backRightLateralThruster, Arduino.SERVO); 
  ard0.pinMode(backLeftLateralThruster, Arduino.SERVO); 
  ard0.pinMode(frontRightLateralThruster, Arduino.SERVO); 
  ard0.pinMode(frontLeftLateralThruster, Arduino.SERVO); 
  ard0.pinMode(frontLeftVerticalThruster, Arduino.SERVO); 
  ard0.pinMode(backLeftVerticalThruster, Arduino.SERVO); 
  ard0.pinMode(frontRightVerticalThruster, Arduino.SERVO); 
  ard0.pinMode(backRightVerticalThruster, Arduino.SERVO); 
 
  control = ControlIO.getInstance(this);
  
  //finds the controller map file
  cont = control.getMatchedDevice("lgcontrol");
  
  //sets the slowing variables to default to fast mode
  vSlow = 0;
  lSlow = 0;
  
  //sets the manipulators to default in the not actuated positions
  mainac = false;
  sideac = false;
  
  //Initializes a window for information
  //size(1366, 768); 
  //textSize(14);
  //fill(0, 100, 255);
  
}

//makes an entry in the window
void addEntry(String title, int info, int x, int y) {
  text(title + info, x, y);
}
 
 void addEntry(String title, boolean info, int x, int y) {
  text(title + info, x, y);
}
  
void addEntry(String title, float info, int x, int y) {
  text(title + info, x, y);
}

public void getUserInput() {
  dPad = (int) cont.getHat("d_Pad").getValue();
  GamepadExManager.updateAll();
  
  //toggles the lateral motion slowing
  if(lStickB.isToggled()) {
    lSlow = 44;
  } else {
    lSlow = 0;
  }
  
  //toggles the vertical motion slowing
  if(rStickB.isToggled()) {
    vSlow = 45;
  } else {
    vSlow = 0;
  }

  //gets the values of the controller's joystick positions
  
  //deadzone implementation
  if(lStickYActivity.isHeld()) {
    forward = cont.getSlider("lStickY").getValue();
  } else {
    forward = 0;
  }
  
  mFLf = forward;
  mBLf = forward;
  mFRf = forward;
  mBRf = forward;
  
  //deadzone implementation
  if(lStickXActivity.isHeld()) {
    strafe = cont.getSlider("lStickX").getValue();
  } else {
    strafe = 0;
  }
  
  mFLs = -strafe;
  mBLs = strafe;
  mFRs = strafe;
  mBRs = -strafe;
  
  //deadzone implementation
  if(rStickXActivity.isHeld()) {
    yaw = cont.getSlider("rStickX").getValue();
  } else {
    yaw = 0;
  }
  
  mFLy = -yaw;
  mBLy = -yaw;
  mFRy = yaw;
  mBRy = yaw;
  
  //sums the commands to each thruster to determine final direction command
  mFL = (mFLf + mFLs + mFLy);
  mBL = (mBLf + mBLs + mBLy);
  mFR = (mFRf + mFRs + mFRy);
  mBR = (mBRf + mBRs + mBRy);
  
  //lowers the commands to the correct range
  if (mFL > 1) {
    mFL = 1;
  }  else if (mFL < -1) {
    mFL = -1;
  }  
  
  if (mBL > 1) {
    mBL = 1;
  }  else if (mBL < -1) {
    mBL = -1;
  }  
  
  if (mFR > 1) {
    mFR = 1;
  }  else if (mFR < -1) {
    mFR = -1;
  }  
  
  if (mBR > 1) {
    mBR = 1;
  }  else if (mBR < -1) {
    mBR = -1;
  }  
  
  if(mFL<0) {
    hex[0]=#ff0000;
    hex[3]=#ff0000;
    hex[6]=#ff0000;
  } else if(mFL>0) {
    hex[0]=#00ff00;
    hex[3]=#00ff00;
    hex[6]=#00ff00;
  } else {
    hex[0]=#ffffff;
    hex[3]=#ffffff;
    hex[6]=#ffffff;
  }
  
  if(mBL<0) {
    hex[36]=#ff0000;
    hex[39]=#ff0000;
    hex[42]=#ff0000;
  } else if(mBL>0) {
    hex[36]=#00ff00;
    hex[39]=#00ff00;
    hex[42]=#00ff00;
  } else {
    hex[36]=#ffffff;
    hex[39]=#ffffff;
    hex[42]=#ffffff;
  }
  
  if(mFR<0) {
    hex[2]=#ff0000;
    hex[5]=#ff0000;
    hex[8]=#ff0000;
  } else if(mFR>0) {
    hex[2]=#00ff00;
    hex[5]=#00ff00;
    hex[8]=#00ff00;
  } else {
    hex[2]=#ffffff;
    hex[5]=#ffffff;
    hex[8]=#ffffff;
  }
  
  if(mBR<0) {
    hex[38]=#ff0000;
    hex[41]=#ff0000;
    hex[44]=#ff0000;
  } else if(mBR>0) {
    hex[38]=#00ff00;
    hex[41]=#00ff00;
    hex[44]=#00ff00;
  } else {
    hex[38]=#ffffff;
    hex[41]=#ffffff;
    hex[44]=#ffffff;
  }
  
  //maps the commands to servo angle values
  //detects if the lateral slow is toggled on or off, cuts speed 50%
  mFL = map(mFL, -1, 1, 0 + lSlow - lSlow/45, 179 - lSlow);
  mBL = map(mBL, -1, 1, 0 + lSlow - lSlow/45, 179 - lSlow);
  mFR = map(mFR, -1, 1, 0 + lSlow - lSlow/45, 179 - lSlow);
  mBR = map(mBR, -1, 1, 0 + lSlow - lSlow/45, 179 - lSlow);

  //checks to see if the activity level is high enough, if so it sets the lift motor power to the appropriate value and otherwise sets it to 0 power
  if (rStickYActivity.isHeld()) {  
    //detects if vertical slow is toggled on or off, cuts speed 50%
    lift = cont.getSlider("rStickY").getValue();
  }  else {
    lift = 0;
  }  
  
  vFLu = lift;
  vBLu = lift;
  vFRu = lift;
  vBRu = lift;
  
  //deadzone implementation
  boolean placeholder = false;
  if(placeholder) {
    roll = 1;
  } else if(placeholder) {
    roll = -1;
  } else {
    roll = 0;
  } 
  
  vFLr = roll;
  vBLr = roll;
  vFRr = -roll;
  vBRr = -roll;
  
  //deadzone implementation
  placeholder = false;
  if(placeholder) {
    pitch = 1;
  } else if(placeholder) {
    pitch = -1;
  } else {
    pitch = 0;
  }
  
  vFLp = -pitch;
  vBLp = pitch;
  vFRp = -pitch; //<>//
  vBRp = pitch;
  
  //sums the commands to each thruster to determine final direction command
  vFL = (vFLu + vFLr + vFLp);
  vBL = (vBLu + vBLr + vBLp);
  vFR = (vFRu + vFRr + vFRp);
  vBR = (vBRu + vBRr + vBRp);
  
  //lowers the commands to the correct range
  if (vFL > 1) {
    vFL = 1;
  }  else if (vFL < -1) {
    vFL = -1;
  }  
  
  if (vBL > 1) {
    vBL = 1;
  }  else if (vBL < -1) {
    vBL = -1;
  }  
  
  if (vFR > 1) {
    vFR = 1;
  }  else if (vFR < -1) {
    vFR = -1;
  }  
  
  if (vBR > 1) {
    vBR = 1;
  }  else if (vBR < -1) {
    vBR = -1;
  }  
  
  if(vFL<0) {
    hex[12]=#ff0000;
    hex[15]=#ff0000;
    hex[18]=#ff0000;
  } else if(vFL>0) {
    hex[12]=#00ff00;
    hex[15]=#00ff00;
    hex[18]=#00ff00;
  } else {
    hex[12]=#ffffff;
    hex[15]=#ffffff;
    hex[18]=#ffffff;
  }
  
  if(vBL<0) {
    hex[24]=#ff0000;
    hex[27]=#ff0000;
    hex[30]=#ff0000;
  } else if(vBL>0) {
    hex[24]=#00ff00;
    hex[27]=#00ff00;
    hex[30]=#00ff00;
  } else {
    hex[24]=#ffffff;
    hex[27]=#ffffff;
    hex[30]=#ffffff;
  }
  
  if(vFR<0) {
    hex[14]=#ff0000;
    hex[17]=#ff0000;
    hex[20]=#ff0000;
  } else if(vFR>0) {
    hex[14]=#00ff00;
    hex[17]=#00ff00;
    hex[20]=#00ff00;
  } else {
    hex[14]=#ffffff;
    hex[17]=#ffffff;
    hex[20]=#ffffff;
  }
  
  if(vBR<0) {
    hex[26]=#ff0000;
    hex[29]=#ff0000;
    hex[32]=#ff0000;
  } else if(vBR>0) {
    hex[26]=#00ff00;
    hex[29]=#00ff00;
    hex[32]=#00ff00;
  } else {
    hex[26]=#ffffff;
    hex[29]=#ffffff;
    hex[32]=#ffffff;
  }
  
  //maps the commands to servo angle values
  //detects if the lateral slow is toggled on or off, cuts speed 50%
  vFL = map(vFL, -1, 1, 0 + vSlow - vSlow/45, 179 - lSlow);
  vBL = map(vBL, -1, 1, 0 + vSlow - vSlow/45, 179 - lSlow);
  vFR = map(vFR, -1, 1, 0 + vSlow - vSlow/45, 179 - lSlow);
  vBR = map(vBR, -1, 1, 0 + vSlow - vSlow/45, 179 - lSlow);
  
  //Uses the dpad to get PH camera motion commands
  if (dPadUp.isHeld()) {
    if (camAng < 179) {
      camAng += 1;
    }
  }
  if (dPadDown.isHeld()) {
    if (camAng > 0) {
      camAng -= 1;
    }
  }
  if (dPadLeft.isPressed()) {
    camAng = 90;
  }
}

void draw() {
 
  getUserInput();
  
  //Writes the vertical motion command to the middle thrusters
  ard0.servoWrite(frontLeftVerticalThruster, (int)vFL);
  ard0.servoWrite(backLeftVerticalThruster, (int)vBL);
  ard0.servoWrite(frontRightVerticalThruster, (int)vFR);
  ard0.servoWrite(backRightVerticalThruster, (int)vBR);

  //Writes the lateral motion command to the corner thrusters
  ard0.servoWrite(frontLeftLateralThruster, (int)mFL);
  ard0.servoWrite(backLeftLateralThruster, (int)mBL);
  ard0.servoWrite(frontRightLateralThruster, (int)mFR);
  ard0.servoWrite(backRightLateralThruster, (int)mBR);
  
  //Writes the camera angle
  ard0.servoWrite(camTip, (int)camAng);
  
  //Populates the window with control information
    //color of the backround in rgb
  fill(#FFFFFF);
  textFont(sansSerif);
  textSize(25);
  strokeWeight(4);
  background(0, 0, 0);
  addEntry("Left stick Y values: ", forward, lIndent, 50);
  addEntry("Left stick X values: ", strafe, lIndent, 75);
  addEntry("Right stick Y values: ", lift, lIndent, 100);
  addEntry("Right stick X values: ", yaw, lIndent, 125);
  addEntry("Camera Angle: ", camAng, lIndent, 150);
  
  textFont(monospace);
  textSize(20);
  strokeWeight(6);
  for(int i=0;i<wireFrame.length;i++) {
    fill(hex[i]);
    text(wireFrame[i],xs[i],ys[i]);
  }
  //addEntry("Thruster _ Value: ", 5, lIndent, 125);
  //addEntry("Gyroscope: ", , lIndent, 100);
  
  //adds the wireframe images and applies them when applicable
  //if(int(time%4) == 0){
  //    image(side, 50, 175);
  //  }else if(int(time%5) == 0) {
  //    image(clawOp,50, 175);
  //  }else if(int(time%6) == 0){
  //    image(clawCl, 50, 175);
  //  }else{
  //    image(iso,50,175);
  //  }
    
  //background(141, 76, 34);
  ////println("Hello world!");
  //print(camAng);
  //print("   ");
  //print(lStickYActivity.isHeld());
  //print("   ");
  //print(rStickXActivity.isHeld());
  //print("   ");
  //print(rStickYActivity.isHeld());
  //print("   ");
  //println(millis());
} 
