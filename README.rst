Plover Continuous Mouse
=======================

A true "hold-to-move" continuous mouse movement plugin for Plover. 

Unlike standard Plover command dictionaries which only execute once per stroke release, this plugin functions as an **Extension** that intercepts your raw keyboard events (NKRO) to provide smooth, continuous mouse pointer movement and scrolling *while* keys are being held down.

Requirements
------------
1. Plover (4.0.0.dev or later)
2. An **NKRO Keyboard** or a split keyboard operating as a standard "Keyboard" machine in Plover's configuration. 
*(Note: Serial Steno protocols like TX Bolt or Gemini PR that only output strokes upon key release are physically incompatible with true hold-to-move).*

Installation
------------
1. Open the Plover Plugin Manager.
2. Click the advanced/gear icon to install from a URL.
3. Use your GitHub URL: ``git+https://github.com/liampost/Plover_mouse_continuous.git``
4. **Enable the Extension:** Go to `Plover Configuration` -> `Plugins`, and check the box next to `plover_mouse`.

Configuration
-------------
Because this plugin intercepts raw keys before Plover translates them, it **cannot** be configured via standard Plover dictionaries (like `{PLOVER:mouse_move}`).

Instead, movement is configured in a file named ``mouse_config.json`` which is generated automatically in the plugin folder when you first enable it.

The default configuration maps movement to standard QWERTY keys (which your Steno machine is simulating when you press its physical keys):

.. code:: json

    {
        "e": [0, -5, 0],   // Up
        "d": [0, 5, 0],    // Down
        "s": [-5, 0, 0],   // Left
        "f": [5, 0, 0],    // Right
        "r": [0, 0, 1],    // Scroll Up
        "v": [0, 0, -1]    // Scroll Down
    }

The format is ``"qwerty_key": [delta_x, delta_y, scroll_delta]``. 
You can edit ``mouse_config.json`` to map these movements to whichever physical keys on your split keyboard you prefer to use for mouse operations. You can combine keys (e.g. holding 'e' and 's' moves diagonally up-left).


