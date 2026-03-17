Plover Mousemaster
==================

A native Plover plugin offering keyboard-driven mouse control using a transparent overlay, heavily inspired by the original Java-based `Mousemaster`.

Instead of running continuous loops or separate Java applications, this plugin runs entirely within Plover's GUI thread, offering a seamless and responsive mouse-navigation experience directly via Steno strokes.

Features
--------
1. **Grid Navigation:** Split your screen geometrically to quickly hone in on any point.
2. **UI Hint Targets:** Automatically discover clickable UI elements (buttons, links, inputs) in the active application and generate 1-2 letter Hint Labels to instantly click them. 
3. **Multi-Monitor Support:** Overlays and cursor commands fluidly cross monitor boundaries seamlessly.
4. **Scrolling & Clicking:** Native Windows scrolling and clicking commands.

Requirements
------------
1. Plover (5.1.0 or later recommended as it natively packages PySide6).
2. Windows OS (relies on `pywinauto` and native `user32`/`ctypes` system calls for performance).

Installation
------------
1. Open the Plover Plugin Manager.
2. Click the configuration/gear icon to install from a repository.
3. Install using your repository URL (e.g. ``git+https://github.com/liampos/Plover_mouse_continuous.git``).
4. Restart Plover.
5. In Plover's main window, go to the **Tools** menu and click **Mouse Overlay** to initialize the transparent window. 

Commands available
------------------
Map these commands to your Plover dictionary:

- ``{plover:mm_grid}`` - Open the grid selection overlay on the active monitor.
- ``{plover:mm_grid:left}``, ``{plover:mm_grid:right}``, ``{plover:mm_grid:up}``, ``{plover:mm_grid:down}`` - Drill down into sectors of the grid.
- ``{plover:mm_grid:close}`` - Close the grid.

- ``{plover:mm_hint:start}`` - Scan the active application and taskbar for clickable UI targets and show letter hints over them.
- ``{plover:mm_hint:close}`` - Close the hint selection overlay.
  *(Note: When hints are active, naturally typing the visible 1-2 letter label via Plover will jump the mouse to the target and automatically exact the click!)*

- ``{plover:mm_screen}`` - Cycle your mouse cursor sequentially to the dead-center of all connected monitors.

- ``{plover:mm_scroll:up}``, ``{plover:mm_scroll:down}``, ``{plover:mm_scroll:left}``, ``{plover:mm_scroll:right}`` - Native scroll wheel actuation.
  *Optional: add a `,X` or `:X` amount to change the scroll chunk (e.g., `{plover:mm_scroll:down,5}`)*.

- ``{plover:mm_click}`` / ``{plover:mm_left_click}`` - Standard Left click. Also automatically closes active grids.
- ``{plover:mm_right_click}`` - Right click.
- ``{plover:mm_toggle_click}`` - Hold/release left click for click-and-drag.

- ``{plover:mm_move:X,Y}`` / ``{plover:mm_nudge:X,Y}`` - Nudge the mouse instantly by the specified geometric pixels. (e.g., `{plover:mm_move:-10,0}`)

How hints work
--------------
Plover Mousemaster will use UI Automation (`pywinauto`) to find any elements presenting a clickable interact pattern to the OS under the active/foreground window. The overlay will generate single letter labels mapping sequentially downward (e.g. `a, b, c`) up to 26 elements. If there are more than 26 on screen, it upgrades to a uniform 2-letter layout (`aa, ab, ac`) to ensure there are no frustrating prefix overlaps. 

When you trigger a Plover stroke that generates a text letter, the overlay safely consumes that letter via backspace injection and narrows the active highlights. Upon a unique match, the mouse is moved immediately to that UI Element's Cartesian center and clicked!
