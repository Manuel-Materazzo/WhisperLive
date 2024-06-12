#!/bin/sh
cloudflared tunnel --url http://localhost:9090 &
python run_server.py
