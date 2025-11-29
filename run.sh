#!/bin/bash

# Bu script FastAPI app ni ishga tushiradi

# 1. Virtual environment (agar ishlatayotgan bo‘lsang)
# source /yo‘ling/venv/bin/activate

# 2. FastAPI app ni ishga tushirish
uvicorn web.app:app --reload --host 0.0.0.0 --port 8000
