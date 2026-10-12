# SeeWhatISee

SeeWhatISee is a small Windows desktop app that lets you ask questions about what is on your screen.

It can capture the screen, send the image to a vision model, and return a useful answer. I built it to make screen understanding quick instead of switching between screenshots, notes, and an AI chat window.

## What it can do

- Capture the primary screen and show a preview
- Ask a custom question about the captured screen
- Explain what is visible
- Extract visible text
- Summarize the screen
- Look for errors or warnings
- Format answers in readable Markdown
- Copy an answer with one click
- Capture from anywhere with a global keyboard shortcut
- Stay available from the Windows system tray
- Keep screenshots in memory instead of saving them to disk

## Tech used

- Python 3.10+
- PySide6 for the desktop interface
- Ollama Cloud for the default vision model
- OpenAI-compatible chat completions API
- `unittest` for tests

## Download the project

Clone the repository from GitHub:

```powershell
git clone https://github.com/pulkit0811/SeeWhatIsee.git
cd SeeWhatIsee
```

You can also download the repository as a ZIP from GitHub and open a PowerShell window in the extracted folder.

## Setup

Create a virtual environment and install the project:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

If PowerShell blocks virtual environment activation, you can skip activation and use the virtual environment's Python directly as shown below.

## Add an Ollama API key

The default setup uses Ollama Cloud, so you do not need to download a model to your computer.

1. Sign in at [ollama.com](https://ollama.com/).
2. Create an API key at [ollama.com/settings/keys](https://ollama.com/settings/keys).
3. Copy the example environment file:

```powershell
Copy-Item .env.example .env
notepad .env
```

4. Put your key in `.env`:

```env
AI_PROVIDER=ollama
OLLAMA_API_KEY=your_ollama_api_key_here
OLLAMA_BASE_URL=https://ollama.com/v1
SEEWHATISEE_MODEL=gemma4
```

Do not commit `.env` or share the API key. The file is ignored by Git.

## Run the app

If the virtual environment is activated:

```powershell
python -m seewhatisee
```

Or run it with one command from the project folder:

```powershell
$env:PYTHONPATH="$PWD\src"; .\.venv\Scripts\python.exe -m seewhatisee
```

The app opens with an empty workspace. Capture the screen, type a question, and click **Ask AI**. You can also use one of the quick actions below the question field.

## Keyboard shortcut and tray mode

When SeeWhatISee is running, press:

```text
Ctrl + Win + Space
```

This captures the primary screen and brings the app forward. If Windows reserves that shortcut on your machine, use:

```text
Ctrl + Alt + Space
```

Closing the window keeps the app running in the system tray. From the tray menu you can show the app, capture the screen, or quit completely.

## Use OpenAI instead

Ollama is the default, but OpenAI can also be used by changing `.env`:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
SEEWHATISEE_MODEL=gpt-4o-mini
```

## Run the tests

```powershell
python -m unittest discover -s tests -v
```

If the virtual environment is not activated:

```powershell
$env:PYTHONPATH="$PWD\src"; .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Privacy note

Screenshots are kept in memory during the current session and are not written to disk by the app. When you ask a question, the current screenshot and your question are sent to the configured AI provider. Avoid capturing passwords, private messages, or other sensitive information.

## Project structure

```text
src/seewhatisee/
  ai/          AI and vision provider integration
  capture/     Screen capture and PNG preparation
  config/      Environment configuration
  ui/          Desktop window, tray mode, and global shortcut
  main.py      Application entry point
tests/         Automated tests
```

## Current limitations

- Capture currently uses the primary monitor.
- Region selection is not implemented yet.
- The global shortcut works while the application process is running.
- Cloud usage depends on the limits and credits of the selected provider.
