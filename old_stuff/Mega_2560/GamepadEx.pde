//this class is used to manage the different GamepadEx objects and update them all from one location
public static class GamepadExManager {
  private static Runnable[] buttons = new Runnable[0];
  
  public static void addButton(Runnable button) {
    Runnable[] temp = new Runnable[buttons.length+1];
    for(int i = 0; i < buttons.length; i++) {
      temp[i] = buttons[i];
    }
    temp[buttons.length] = button;
    buttons = temp;
  }
  
  /*call this method once in your main loop to update all buttons. Ex:
    GamepadExManager.updateAll();
  */
  public static void updateAll() {
    for(Runnable button: buttons) {
      button.run();
    }
  }
}

public class GamepadEx {
  //declares the internal variables
  private boolean gamepadInput;
  private boolean wasPressed;
  private boolean isToggled;
  private boolean pressedOnce;
 
  /*This is the constructor. It can be rather confusing to use. 
  When you create a GamepadEx object, you need to give it a Button object as an argument. This is so that the code used to obtain the input can be stored and called later by the GamePadExManager.
  The proper syntax to create an object will be given in the following example. Things wrapped in *s are where you insert your code.
  
  GamepadEx *objectName* = new GamepadEx(new Button(){boolean inputCode(){return *Your boolean you want the GamepadEx to use. Normally the input from a button*;}});
  
  */
  public GamepadEx(Button input) {
    wasPressed = false;
    isToggled = false;
    GamepadExManager.addButton(new Runnable(){
      public void run(){
        GamepadEx.this.updateButton(input.inputCode());
      }
    });
  }
  
  //this function is called from the GamepadExManager
  //it updates the values stored inside the GamepadEx objects
  private void updateButton(boolean gamepadInput) {
    this.gamepadInput = gamepadInput;
    if(gamepadInput && !wasPressed) {
      wasPressed = true;
      pressedOnce = true;
      isToggled = !isToggled;
    } else if(!gamepadInput && wasPressed) {
      wasPressed = false;
      pressedOnce = false;
    }
  }
 
  //Use if you need something to occur for the duration that a button is held
  //returns the raw button input. 
  public boolean isHeld() {
    return gamepadInput;
  }
  
  //Use if you want something to happen once only when a button is pressed.
  //returns true the first time it is called while a button is pressed. Is false on subsequent presses while still being held. 
  public boolean isPressed() {
    boolean wasPressedOnce = pressedOnce;
    pressedOnce = false;
    return wasPressedOnce;
  }
 
  //Use if you want the state of something to change upon a button press and remain changed afterwards
  //returns the value of the toggle. The toggle changes once every time the button is pressed. 
  public boolean isToggled() {
    return isToggled;
  } 
 
  //Use if you want to set a starting value for the toggle
  //sets the toggle to the given value
  public void setToggle(boolean newToggleValue) {
    this.isToggled = newToggleValue;
  }
}

//the interface necessary to store the code for inputs
private interface Button {
  public boolean inputCode();
}
