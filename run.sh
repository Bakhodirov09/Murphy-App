#!/bin/bash

# Run Web
uvicorn web.app:app --port 7000 &

# Save ran web's pid
WEB_PID=$!

# Run bot
python3 app.py

# If the bot stops unexpectedly, web will stop automatically.
kill $WEB_PID
