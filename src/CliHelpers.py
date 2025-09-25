import argparse
from pathlib import Path


class CliHelpers:
    def __init__(self):
        pass

    def main_args(self):
        parser = argparse.ArgumentParser(description="Download models from Civitai")
        
        # mutually exclusive group
        model_group = parser.add_mutually_exclusive_group()
        model_group.add_argument("--model", type=str, help="Model url(s)", nargs="*")
        model_group.add_argument("--file", type=str, help="path of file with model urls", nargs='?', const=Path(__file__).resolve().parent.parent / "models.txt", default=None)
        
        parser.add_argument("--mode", type=str, help="download mode", required=False, default="concurrent", choices=["concurrent", "iterative", "c", "i"])
        parser.add_argument("--list-versions", action="store_true", help="list all versions of models and choose which one to download when prompted")
        
        args = parser.parse_args()
        
        if not args.model and not args.file:
            parser.error("Either --model or --file must be specified. Use --help for more information.")
        
        return args

    def choose_dl_folder(self, folders: list[str]) -> str:
        '''print name of all dl folders prepended by index, listen for input, return folder name based on index'''
        print("\nAvailable download folders:")
        for i, folder in enumerate(folders, 1):
            print(f"  {i}. {folder}")
        
        while True:
            try:
                choice = input(f"\nSelect folder (1-{len(folders)}): ").strip()
                index = int(choice) - 1
                if 0 <= index < len(folders):
                    return folders[index]
                else:
                    print(f"Please enter a number between 1 and {len(folders)}")
            except ValueError:
                print("Please enter a valid number")

    def choose_model_version(self, versions: list[dict]) -> int:
        '''print name of all model versions prepended by index, listen for input, return version index based on input'''
        print("\nAvailable model versions:")
        for i, version in enumerate(versions):
            created_at = version.get("createdAt", "Unknown date")
            scan_result = version.get("virusScanResult", "Unknown")
            print(f"  {i+1}. Created: {created_at}, Virus Scan: {scan_result}")
        
        while True:
            try:
                choice = input(f"\nSelect version (1-{len(versions)}): ").strip()
                index = int(choice) - 1
                if 0 <= index < len(versions):
                    return index
                else:
                    print(f"Please enter a number between 1 and {len(versions)}")
            except ValueError:
                print("Please enter a valid number")

    def confirm_unsafe_model(self, model_name: str, scan_result: str) -> bool:
        '''for models that failed the virus check, take bool to confirm if user still wants to download model'''
        print(f"\nWARNING: Model '{model_name}' failed virus scan!\n")
        print(f"Virus scan result: {scan_result}")
        
        while True:
            response = input("Do you still want to download this model? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no', '']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no")

    def confirm_multiple_unsafe_models(self, unsafe_models: list[tuple]) -> list[tuple]:
        '''for multiple models that failed virus checks, handle batch confirmation with exclusions'''
        if not unsafe_models:
            return []
        
        print(f"\nWARNING: {len(unsafe_models)} models failed virus scans!\n")
        
        for i, (model_name, scan_result) in enumerate(unsafe_models, 1):
            print(f"  {i}. {model_name} - Virus Scan: {scan_result}")
        
        print("\nOptions:")
        print("  a - Download all unsafe models")
        print("  n - Download none (skip all)")
        print("  s - Select specific models to download")
        print("  q - Quit")
        
        while True:
            choice = input("\nChoose option (a/n/s/q): ").strip().lower()
            
            if choice == 'a':
                return unsafe_models
            elif choice == 'n':
                return []
            elif choice == 'q':
                print("Exiting...")
                exit(0)
            elif choice == 's':
                return self._select_specific_unsafe_models(unsafe_models)
            else:
                print("Invalid option. Please enter 'a', 'n', 's', or 'q'")

    def _select_specific_unsafe_models(self, unsafe_models: list[tuple]) -> list[tuple]:
        '''Helper function to select specific unsafe models'''
        print("\nEnter model numbers to download (comma-separated, e.g., 1,3,5)")
        print("Or enter 'all' for all models, 'none' to skip all")
        
        while True:
            choice = input("Selection: ").strip().lower()
            
            if choice == 'all':
                return unsafe_models
            elif choice == 'none':
                return []
            
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(',')]
                selected_models = []
                
                for index in indices:
                    if 0 <= index < len(unsafe_models):
                        selected_models.append(unsafe_models[index])
                    else:
                        print(f"Invalid index: {index + 1}")
                
                if selected_models:
                    return selected_models
                else:
                    print("No valid models selected. Please try again.")
            except ValueError:
                print("Invalid input. Please enter numbers separated by commas.")