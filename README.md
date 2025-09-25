# civtai-cli-dl

A CLI tool for downloading models from CivitAI into ComfyUI.

## Overview

This tool currently only supports ComfyUI, though you can set `config.toml` with overrides to specific model paths.

**Note:** This tool doesn't resolve symlinks or relative paths. Use `realpath` to get the folder path if you're unsure.

## Installation

1. Clone the repository
2. Set up a virtual environment
3. Install requirements

The tool is designed for `uv` but `pip` should also work.

### Configuration

Edit the model path in `config.toml` to the realpath of your model folder. It assumes the default ComfyUI model structure:

```toml
[ComfyUI]
comfyui_models_path = '/home/user/ComfyUI/models'
```

## Usage

### Basic Command

```bash
uv run main.py [options]
```

### Command Line Arguments

#### Model Selection
- `--model`: Model URL(s) - accepts multiple URLs
- `--file`: Path to file containing model URLs separated by newline. Defaults to `models.txt` in project root

#### Download Options
- `--mode`: Download mode (default: "concurrent")
  - `concurrent` or `c`: Download multiple models simultaneously
  - `iterative` or `i`: Download models one at a time
- `--list-versions`: List all versions of models and prompt for selection

### Examples

```bash
# Download a single model
uv run main.py --model "https://civitai.com/models/MODELID"

# Download multiple models
uv run main.py --model "https://civitai.com/models/MODELID" "https://civitai.com/models/ANOTHERMODELID"

# Download from a file
uv run main.py --file models.txt

# Download iteratively with version selection
uv run main.py --mode iterative --list-versions --file models.txt
```

## Notes

- **Concurrency**: Limited to 5 models at once to avoid overwhelming servers. This isn't a limit on the amount of models you can pass in, just a limit on how many will be downloaded at the same time.
- **Rate Limiting**: 5-second pause between requests because Civitai doesn't have publically documented rate limits
- **Frequent asks for model placement**: Simply a civitai API limitation. Their docs are very outdated + a lot of models that on the webui show a specific type just have their type reported as "OTHER" via the API. 

## Future expansion

Add webscraping functionality for a better effort automatic folder placement.<br>
Support models being added into subfolders (chars/loras/poses or resolution factor for upscale models and so on)<br>
Support OpenModelDB downloads<br>
Support Huggingface downloads<br>