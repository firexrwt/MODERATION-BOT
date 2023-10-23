# MODERATION-BOT

## Description
This is local-based discord bot for moderation. It has some commands for moderation and some commands for fun. It is still in development and will be updated soon.

## How to set up
1. Download the code
2. Install the requirements with ```pip install -r requirements.txt```
3. Create ```config.json``` file, that looks something like this:
```json
{
    "token": "your token",
}
```
4. Change all the values in ```main.py``` **to your own**
5. Create a bat file and write something like this:
```bat
@echo off
"Path where your Python.exe is stored\python.exe" "Path where bot is stored\main.py"
pause
```
6. Run the bat file
7. Enjoy!

## Goals
- [x] Add moderation commands
- [x] Connect bot to database
- [ ] Connect bot to web
- [ ] Add fun commands