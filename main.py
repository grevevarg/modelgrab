#!/usr/bin/env python3
"""
CivitAI CLI Downloader - Main application
"""

import os
import sys
from pathlib import Path
from src.ModelInfo import ModelInfo
from src.ModelDownloader import ModelDownloader
from src.HtxRequest import HtxRequest
from src.CliHelpers import CliHelpers

def main():
    """Main CLI application loop"""
    cli = CliHelpers()
    args = cli.main_args()
    
    try:
        config_path = Path(__file__).parent / "config.toml"
        downloader = ModelDownloader(str(config_path))
        htx = HtxRequest(os.getenv("API_KEY"))
    except Exception as e:
        print(f"Error initializing components: {e}")
        return 1
    
    models_to_download = []
    
    if args.model:
        if isinstance(args.model, list):
            # multiple models
            for model_url in args.model:
                try:
                    model_id = htx.parse_url(model_url)
                    model_data = htx.get_model(str(model_id))
                    model_info = ModelInfo(model_data)
                    models_to_download.append(model_info)
                    print(f"Added model: {model_info.name}")
                except Exception as e:
                    print(f"Error getting model from URL {model_url}: {e}")
                    continue
        else:
            # single model
            try:
                model_id = htx.parse_url(args.model)
                model_data = htx.get_model(str(model_id))
                model_info = ModelInfo(model_data)
                models_to_download.append(model_info)
                print(f"Added model: {model_info.name}")
            except Exception as e:
                print(f"Error getting model from URL {args.model}: {e}")
                return 1
    
    elif args.file:
        # batch download from file
        try:
            model_data_list = htx.get_models_by_list_file(args.file)
            for model_data in model_data_list:
                model_info = ModelInfo(model_data)
                models_to_download.append(model_info)
                print(f"Added model: {model_info.name}")
        except Exception as e:
            print(f"Error reading models from file {args.file}: {e}")
            return 1
    
    else:
        # interactive mode
        print("Interactive mode - enter model URLs (one per line, empty line to finish):")
        while True:
            url = input("Model URL (or empty to finish): ").strip()
            if not url:
                break
            
            try:
                model_id = htx.parse_url(url)
                model_data = htx.get_model(str(model_id))
                model_info = ModelInfo(model_data)
                models_to_download.append(model_info)
                print(f"Added model: {model_info.name}")
            except Exception as e:
                print(f"Error with URL {url}: {e}")
                continue
    
    if not models_to_download:
        print("No models to download. Exiting.")
        return 0
    
    print(f"\nTotal models to process: {len(models_to_download)}")
    
    if args.file or (args.model and isinstance(args.model, list) and len(args.model) > 1):
        if not args.mode:
            print("Error: --mode is required when reading from file or specifying multiple models")
            print("Use --mode concurrent or --mode iterative (or --mode c / --mode i)")
            return 1
    
    # show model information and handle version selection if requested
    if args.list_versions:
        print("\nModel versions:")
        for i, model in enumerate(models_to_download):
            print(f"\n{i+1}. {model.name}")
            versions = model.list_all_versions()
            if versions:
                selected_index = cli.choose_model_version(versions)
                print(f"Selected version {selected_index + 1} for {model.name}")
    
    # download mode
    mode = args.mode.lower()
    
    if mode == "c":
        mode = "concurrent"
    elif mode == "i":
        mode = "iterative"
    
    if mode not in ["concurrent", "iterative"]:
        print(f"Invalid mode: {args.mode}. Must be 'concurrent', 'iterative', 'c', or 'i'")
        return 1
    
    if mode == "concurrent":
        print(f"\nDownloading {len(models_to_download)} models concurrently")
        downloader.download_concurrently(models_to_download)
    elif mode == "iterative":
        print(f"\nDownloading {len(models_to_download)} models iteratively")
        downloader.download_iteratively(models_to_download)
    
    print("\nDownload process completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())