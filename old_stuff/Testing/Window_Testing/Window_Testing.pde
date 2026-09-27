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

  //background is in rgb or hex
  float time;
  int hReadings;
  PImage clawCl;
  PImage clawOp;
  PImage iso;
  PImage side;
  void setup(){
    size(600,600);
    textSize(45);
    //background(100, 200, 255);
    //println(Arduino.list());    //Uncomment this to make the code print the COM ports available, then switch
                                //the information in the initialize line to the correct COM port list location
  
  //Initializes the Arduino
  ard0 = new Arduino(this, Arduino.list()[2], 57600);
  
    ard0.pinMode(0, Arduino.INPUT); 
      clawCl = loadImage("RobotWireframeClawClosed.PNG");
      clawOp = loadImage("RobotWireframeClawOpen.PNG");
      iso = loadImage("RobotWireframeIso.PNG");
      side = loadImage("RobotWireframeSide.PNG");
  }
  
   void addEntry(String title, int info, int x, int y) {
    text(title + info, x, y);
  }

   
  void draw(){
    time = ((float) millis()) /1000;
    hReadings = ard0.analogRead(0);
    //a2
    //background(100, 200, 255);
    //text("Hello World", 100.0, 100.0); //string, x value, y value
    //delay(1000);
    background(100, 200, 255);
    addEntry("Time since start: ", int(time), 50, 100);
    addEntry("Spinny sensor readings: ", hReadings, 50, 150);
    //println(hReadings);
    if(int(time%4) == 0){
      image(side, 50, 175);
    }else if(int(time)!=20 & int(time%5) == 0) {
      image(clawOp,50, 175);
    }else if(int(time)!= 24 & int(time%6) == 0){
      image(clawCl, 50, 175);
    }else{
      image(iso,50,175);
    }
  }
  
