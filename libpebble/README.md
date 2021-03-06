libpebble
=========

Interact with your Pebble from any device.

Getting started
---------------

I've only tested this on OS X 10.8. Things will be a little different on other platforms. Firstly make sure you have Python and PySerial installed.

Next, pair your Pebble to your computer and make sure it's setup as a serial port. For me, it gets exposed as /dev/tty.Pebble402F-SerialPortSe. If this is different for you, you'll need to edit pebble.py. The 402F bit is my Pebble's ID. You can just run pebble.py with your ID as an argument if the rest of that path matches.

Once you're paired and the serial port is setup, try running pebble.py. You should get a notification on your Pebble to test that it works properly.

Join #pebble on Freenode IRC to let me know how you get on and share your creations!

Status
------

The following are currently supported:

* Pinging device
* Resetting device
* Setting/getting time
* Sending notifications
* Setting the currently playing track
* Listing installed apps
* Installing apps
* Deleting apps
* Getting the installed firmware versions
* Getting device data (serial, BT MAC etc)

Thanks
------

* Pebble for making an awesome watch.
* RaYmAn for helping me figure out how the PutBytesClient worked.
* Overv for helping me pick apart the Android different message factories in the Android app.
