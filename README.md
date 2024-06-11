# rover-guitar
I made this just for fun because I found out you can use a software called [WiitarThing](https://github.com/Meowmaritus/WiitarThing) to connect a Wii Guitar to a PC (originally found for [Clone Hero](https://clonehero.net/)). It just decodes the Bluetooth msgs from the guitar (once connected using WiitarThing) and converts that to rover control UDP messages for the Sooner Rover Team Rover. 

## Controls
Strumming the guitar will increase the speed in the directions of the buttons held. Strumming faster increases the speed more, though there is an active dampening factor that will slowly stop the rover if strumming is stopped. This means the user must continue strumming to keep the rover moving. The multi-key color inputs are designed to mimmic real chords to make the guitar playing more realistic/challenging. The LEDs on the rover also glow according to what button input you give.

- Forward: GREEN + YELLOW + BLUE
- Reverse: RED + YELLOW + BLUE
- Arc Turn Left: GREEN + BLUE
- Arc Turn Right: GREEN + YELLOW
- Pivot Counter-Clockwise: RED + ORANGE
- Pivot Clockwise: GREEN + ORANGE
