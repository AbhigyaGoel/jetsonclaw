---
name: weather
description: current weather via wttr.in
triggers:
  - weather
  - is it raining
  - how (hot|cold) is it
action:
  command: curl -sf "wttr.in/?format=%C, %t, feels like %f" || echo "Weather service unreachable."
requires:
  bins: [curl]
---
Install: copy this directory to ~/.remy/skills/weather/
Set a city with wttr.in/CityName in the command if auto-detection guesses wrong.
