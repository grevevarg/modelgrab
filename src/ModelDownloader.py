import tomllib as toml
import os
import httpx
import dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from alive_progress import alive_bar
from rich.progress import Progress
from .HtxRequest import HtxRequest
from .ModelInfo import ModelInfo
from .CliHelpers import CliHelpers
from pathlib import Path

CONFIG_PATH = f"{__file__}/../config.toml" #uggo hack i hate paths
dotenv.load_dotenv()

API_KEY = os.getenv("API_KEY")

class ModelDownloader:
    def __init__(self, config_file: str):
        with open(config_file, 'rb') as f:
            self.config = toml.load(f)
        self.paths = self.get_folder_paths()
        self.cli_helpers = CliHelpers()
        self.final_file_paths = {}  # Store final paths for models
        self.api_key = os.getenv("API_KEY")  # Get API key for downloads

    def get_folder_paths(self) -> dict:
        if self.config["Override"]["override"]:
            # If 'override' is true, return paths directly from the 'Override' section.
            return {key: self.config["Override"][key] for key in self.config["Override"] if key != "override"}
        else:
            # If 'override' is false, construct paths using the base path and a list of subfolders.
            base_path = self.config["ComfyUI"]["comfyui_models_path"]
            subfolders = [
                "checkpoints",
                "clip",
                "clip_vision",
                "controlnet",
                "diffusers",
                "diffusion_models",
                "embeddings",
                "gligen",
                "hypernetworks",
                "loras",
                "photomaker",
                "style_models",
                "text_encoders",
                "unet",
                "upscale_models",
                "vae",
                "vae_approx",
            ]
            return {f"{folder}_path": f"{base_path}/{folder}" for folder in subfolders}


    def set_download_path(self, model_info: ModelInfo, force_folder: str = None):
        """
        Set the download path for a model. If force_folder is specified, use that folder.
        For OTHER type models, prompt user for folder choice if not specified.
        """
        # If a specific folder is forced, use it
        if force_folder:
            if force_folder == "temp":
                base_path = Path(self.config["ComfyUI"]["comfyui_models_path"]) / "temp"
            else:
                folder_path_key = f"{force_folder}_path"
                if folder_path_key in self.paths:
                    base_path = Path(self.paths[folder_path_key])
                else:
                    base_path = Path(self.config["ComfyUI"]["comfyui_models_path"]) / force_folder
        else:
            # Normal folder detection logic
            model_type_str = model_info.type.value.lower()
            matching_subfolder = None
            for path_key, full_path in self.paths.items():
                # Extract subfolder name from path_key (remove "_path" suffix)
                subfolder = path_key.replace('_path', '')
                if model_type_str in subfolder.lower() or subfolder.lower() in model_type_str:
                    matching_subfolder = subfolder
                    break
            
            # no match found, create and use temp folder
            if matching_subfolder is None:
                print(f"No matching subfolder found for model type {model_type_str}, using temp folder at comfyui models path")
                Path(self.config["ComfyUI"]["comfyui_models_path"]).mkdir(parents=True, exist_ok=True)
                temp_path = Path(self.config["ComfyUI"]["comfyui_models_path"]) / "temp"
                temp_path.mkdir(parents=True, exist_ok=True)
                matching_subfolder = 'temp'
            
            path_key = f"{matching_subfolder}_path"
            if path_key in self.paths:
                base_path = Path(self.paths[path_key])
            else:
                base_path = Path(self.config["ComfyUI"]["comfyui_models_path"]) / matching_subfolder
        
        # Ensure the base path directory exists
        base_path.mkdir(parents=True, exist_ok=True)
        
        safe_name = model_info.name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        
        # Get the file extension from the model version
        file_extension = model_info.get_latest_file_extension()
        if file_extension:
            safe_name = f"{safe_name}.{file_extension}"
        
        download_path = Path(base_path) / safe_name
        
        # Store the final path for this model
        self.final_file_paths[model_info.id] = download_path
        
        return download_path

    def prompt_for_other_type_folder(self, model_info: ModelInfo) -> str:
        """Prompt user for folder choice for OTHER type models and return chosen folder"""
        print(f"\nModel '{model_info.name}' is type 'OTHER'.")
        print(f"Model url: {model_info.url}")
        print("Please choose where to place this model:")
        
        # Get available folders from config
        available_folders = []
        for path_key, full_path in self.paths.items():
            if path_key != "temp_path":  # Exclude temp folder
                folder_name = path_key.replace('_path', '')
                available_folders.append(folder_name)
        
        # Add option to keep in temp
        available_folders.append("temp")
        
        # Let user choose folder
        chosen_folder = self.cli_helpers.choose_dl_folder(available_folders)
        
        return chosen_folder

    def download_model(self, model_info, progress: Progress):
        """Download a model to its appropriate folder"""
        download_url = model_info.get_latest_download_url()
        if not download_url:
            print(f"No download URL found for model: {model_info.name}")
            return False

        # Get the download path
        download_path = self.final_file_paths.get(model_info.id)
        if download_path is None:
            print(f"Error: Download path not set for {model_info.name}. Call set_download_path first.")
            return False

        download_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            print(f"Downloading {model_info.name} to {download_path}")
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "CivitAI-CLI-Downloader/1.0"
            }

            with httpx.stream("GET", download_url, headers=headers, timeout=30.0, follow_redirects=True) as response:
                response.raise_for_status()
                total_size = int(response.headers.get("content-length", 0))

                task_id = progress.add_task(f"[cyan]Downloading {model_info.name}", total=total_size)

                with open(download_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
                        progress.update(task_id, advance=len(chunk))

            print(f"Downloaded {model_info.name} successfully to {download_path}")
            return True

        except httpx.HTTPStatusError as e:
            print(f"HTTP error downloading {model_info.name}: {e}")
            return False
        except httpx.RequestError as e:
            print(f"Request error downloading {model_info.name}: {e}")
            return False
        except Exception as e:
            print(f"Error downloading {model_info.name}: {e}")
            return False

    def download_concurrently(self, model_list: list[ModelInfo], concurrent_limit: int = 5):
        """Download multiple models concurrently with virus scan checks and user confirmation"""
        if not model_list:
            print("No models to download")
            return
        
        safe_models, unsafe_models = [], []
        for model in model_list:
            if model.check_virus_scan_passed():
                safe_models.append(model)
            else:
                latest_version = model.get_latest_version()
                if latest_version and latest_version.get("files"):
                    scan_result = latest_version["files"][0].get("virusScanResult", "Unknown")
                    unsafe_models.append((model, scan_result))
                else:
                    print(f"Skipping {model.name} - no virus scan information available")

        if unsafe_models:
            confirmed_unsafe = self.cli_helpers.confirm_multiple_unsafe_models(unsafe_models)
            unsafe_to_download = [model for model, _ in confirmed_unsafe]
            all_models_to_download = safe_models + unsafe_to_download
        else:
            all_models_to_download = safe_models

        if not all_models_to_download:
            print("No models to download after virus scan checks and user confirmation")
            return

        for model in all_models_to_download:
            if model.type.value == "OTHER":
                chosen_folder = self.prompt_for_other_type_folder(model)
                self.set_download_path(model, force_folder=chosen_folder)
            else:
                self.set_download_path(model)

        print(f"Downloading {len(all_models_to_download)} models concurrently (limit: {concurrent_limit})")

        successful_downloads = 0
        failed_downloads = 0

        with Progress() as progress:
            with ThreadPoolExecutor(max_workers=concurrent_limit) as executor:
                future_to_model = {
                    executor.submit(self.download_model, model, progress): model
                    for model in all_models_to_download
                }

                for future in as_completed(future_to_model):
                    model = future_to_model[future]
                    try:
                        success = future.result()
                        if success:
                            successful_downloads += 1
                        else:
                            failed_downloads += 1
                    except Exception as e:
                        print(f"Error downloading {model.name}: {e}")
                        failed_downloads += 1

        print(f"\nDownload summary: {successful_downloads} successful, {failed_downloads} failed")

    def download_single_model(self, model_info: ModelInfo) -> bool:
        """Download a single model with virus scan confirmation if needed"""
        if model_info.check_virus_scan_passed():
            if model_info.type.value == "OTHER":
                chosen_folder = self.prompt_for_other_type_folder(model_info)
                self.set_download_path(model_info, force_folder=chosen_folder)
            else:
                self.set_download_path(model_info)
            
            return self.download_model(model_info)
        else:
            # ask user if virus scan failed
            latest_version = model_info.get_latest_version()
            if latest_version and latest_version.get("files"):
                scan_result = latest_version["files"][0].get("virusScanResult", "Unknown")
                if self.cli_helpers.confirm_unsafe_model(model_info.name, scan_result):
    
                    if model_info.type.value == "OTHER":
                        chosen_folder = self.prompt_for_other_type_folder(model_info)
    
                        self.set_download_path(model_info, force_folder=chosen_folder)
                    else:
    
                        self.set_download_path(model_info)
                    
                    return self.download_model(model_info)
                else:
                    print(f"Skipping {model_info.name} - user declined unsafe model")
                    return False
            else:
                print(f"Skipping {model_info.name} - no virus scan information available")
                return False