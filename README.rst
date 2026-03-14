Plover mouse
============

Control the mouse with Plover.

Commands
--------

``{PLOVER:mouse_move:x,y}``: Move the mouse cursor relative to its current position.

``{PLOVER:mouse_position:x,y}``: Move the mouse cursor to absolute coordinates x, y. Coordinates can be omitted, e.g. ``{PLOVER:mouse_position:,1000}``.

``{PLOVER:mouse_scroll:x,y}``: Perform a mouse scroll.

``{PLOVER:mouse_click:button,clicks}``: Click a mouse button a number of times. Button can be ``left``, ``right``, or ``middle``.

``{PLOVER:mouse_press:button}``: Press and hold a mouse button. Button can be ``left``, ``right``, or ``middle``.

``{PLOVER:mouse_release:button}``: Release a mouse button. Button can be ``left``, ``right``, or ``middle``.

Example dictionary
------------------

.. code:: json

	{
	"SKPR-R": "{PLOVER:mouse_move:-10}",
	"SKPR-P": "{PLOVER:mouse_move:,-10}",
	"SKPR-B": "{PLOVER:mouse_move:,10}",
	"SKPR-G": "{PLOVER:mouse_move:10}",
	"SKPR-RP": "{PLOVER:mouse_move:-10,-10}",
	"SKPR-RB": "{PLOVER:mouse_move:-10,10}",
	"SKPR-PG": "{PLOVER:mouse_move:10,-10}",
	"SKPR-BG": "{PLOVER:mouse_move:10,10}",
	"SKPR-F": "{PLOVER:mouse_click:}",
	"SKPR*F": "{PLOVER:mouse_click:,2}",
	"SKPR-L": "{PLOVER:mouse_click:right}",
	"SKPR-T": "{PLOVER:mouse_press:left}",
	"SKPR-S": "{PLOVER:mouse_release:left}",
	"SKPR-D": "{PLOVER:mouse_position:1000}",
	"SKPR-Z": "{PLOVER:mouse_position:,1000}",
	"SKPROR": "{PLOVER:mouse_scroll:-1}",
	"SKPROP": "{PLOVER:mouse_scroll:,1}",
	"SKPROB": "{PLOVER:mouse_scroll:,-1}",
	"SKPROG": "{PLOVER:mouse_scroll:1}",
	"SKPRORP": "{PLOVER:mouse_scroll:-1,1}",
	"SKPRORB": "{PLOVER:mouse_scroll:-1,-1}",
	"SKPROPG": "{PLOVER:mouse_scroll:1,1}",
	"SKPROBG": "{PLOVER:mouse_scroll:1,-1}"
	}

