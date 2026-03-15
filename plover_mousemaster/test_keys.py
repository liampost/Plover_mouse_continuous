from plover.oslayer.windows.keyboardcontrol import KeyboardEmulation
import time

print("Waiting 3 seconds...")
time.sleep(3)
em = KeyboardEmulation()
print("Sending alt(e)...")
em.send_key_combination("alt(e)")
print("Done.")
