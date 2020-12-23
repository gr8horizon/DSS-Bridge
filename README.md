# DSS Bridge
 DSS Bridge

A Mac OSX statusbar application that communicates with Audium Digital Speaker Switch (DSS) boards and facilitates Open Sound Control (OSC) message translation to the Arduino Nano Every board on each DSS.

DSS Bridge will automatically scan USB ports for "tty.usbmodem" devices and request the single character DSS_ID of each board. If no boards are found, the "DSS" statusbar title will read "DSS?"