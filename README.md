# SeeWhatISee

SeeWhatISee is a Windows-first desktop assistant that captures the current screen and lets you ask a vision-capable AI model what is visible.

## Phase 1

- PySide6 desktop interface
- Primary-monitor screenshot capture
- Screenshot preview
- Question input and AI response display
- Environment-based API key configuration
- Friendly capture, configuration, and network error handling
- No screenshots or credentials are persisted by the application

## Installation

Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set `OPENAI_API_KEY`. You can optionally change `SEEWHATISEE_MODEL`.

## Running

```powershell
python -m seewhatisee
```

The application opens with an empty workspace. Select **Capture screen**, enter a question, and select **Ask AI**. The screenshot is sent to the configured OpenAI vision model only when you request an answer.

## Privacy

Screenshots are held in memory for the current session and are not written to disk. When you ask a question, the current screenshot and question are sent to the configured AI provider. Do not capture sensitive content unless you are comfortable sharing it with that provider.

## Project structure

```text
src/seewhatisee/
  ai/          Vision provider integration
  capture/     Screen capture and image preparation
  config/      Environment configuration
  ui/          PySide6 application window
  main.py      Application entry point
tests/         Phase 1 unit tests
```

## Testing

```powershell
python -m unittest discover -s tests -v
```

## Future phases

Global hotkeys, quick actions, conversation context, OCR, region selection, settings, history, packaging, and broader test coverage are intentionally reserved for later phases.

