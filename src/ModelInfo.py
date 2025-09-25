import json
from typing import List, Optional
from enum import Enum

class ModelType(Enum):
    LORA = "LORA"
    CHECKPOINT = "CHECKPOINT"
    TEXTUAL_INVERSION = "TEXTUAL_INVERSION"
    HYPERNETWORK = "HYPERNETWORK"
    AESTHETIC_GRADIENT = "AESTHETIC_GRADIENT"
    CONTROLNET = "CONTROLNET"
    POSE = "POSE"
    OTHER = "OTHER"

class ModelInfo:
    
    def __init__(self, model_info: dict) -> None:
        self.raw_response = model_info
        self.id = str(model_info.get("id", ""))
        self.url = f"https://civitai.com/models/{self.id}"
        self.name = model_info.get("name", "")
        self.type = self._parse_model_type(model_info.get("type", ""))
        self.nsfw = model_info.get("nsfw", False)
        self.creator_username = model_info.get("creator", {}).get("username", "")
        self.tags = model_info.get("tags", [])
        
        self.model_versions = sorted(
            model_info.get("modelVersions", []),
            key=lambda x: x.get("createdAt", ""),
            reverse=True
        ) # newest first
    
    def _parse_model_type(self, type_str: str) -> ModelType:
        """Parse the model type string into an enum value"""
        try:
            return ModelType(type_str)
        except ValueError:
            return ModelType.OTHER
    
    def list_all_versions(self) -> List[dict]:
        """Get all model versions"""
        version_list = []
        for i, model_version in enumerate(self.model_versions):
            version_list.append({
                "id": model_version.get("id"),
                "createdAt": model_version.get("createdAt"),
                "downloadUrl": model_version.get("downloadUrl"),
                "virusScanResult": model_version.get("files")[0].get("virusScanResult"),
                "index": i
            })
        print(version_list) # maybe? feels ugly. i'll figure it out once i use the tool more
        return version_list

    def get_latest_version(self) -> Optional[dict]:
        """Get the latest (newest) model version"""
        return self.model_versions[0] if self.model_versions else None
    
    def get_version_by_id(self, version_id: str) -> Optional[dict]:
        """Get a specific model version by ID"""
        for version in self.model_versions:
            if str(version.get("id")) == str(version_id):
                return version
        return None
    
    def get_latest_download_url(self) -> Optional[str]:
        """Get the download URL for the latest version"""
        latest = self.get_latest_version()
        return latest.get("downloadUrl") if latest else None
    
    def get_version_download_url(self, version_id: str) -> Optional[str]:
        """Get the download URL for a specific version"""
        version = self.get_version_by_id(version_id)
        return version.get("downloadUrl") if version else None
    
    def get_latest_trained_words(self) -> List[str]:
        """Get the trained words for the latest version"""
        latest = self.get_latest_version()
        if latest:
            return latest.get("trainedWords", [])
        return []
    
    def get_version_trained_words(self, version_id: str) -> List[str]:
        """Get the trained words for a specific version"""
        version = self.get_version_by_id(version_id)
        if version:
            return version.get("trainedWords", [])
        return []
    
    def get_latest_version_id(self) -> Optional[str]:
        """Get the ID of the latest version"""
        latest = self.get_latest_version()
        return str(latest.get("id")) if latest else None
    
    def get_latest_file_extension(self) -> Optional[str]:
        """Get the file extension from the latest version file"""
        latest = self.get_latest_version()
        if latest and latest.get("files"):
            file_name = latest["files"][0].get("name", "")
            if file_name:
                if "." in file_name:
                    return file_name.split(".")[-1]
        return None
    
    def get_version_file_extension(self, version_id: str) -> Optional[str]:
        """Get the file extension from a specific version file"""
        version = self.get_version_by_id(version_id)
        if version and version.get("files"):
            file_name = version["files"][0].get("name", "")
            if file_name:
                if "." in file_name:
                    return file_name.split(".")[-1]
        return None
    
    def to_dict(self) -> dict:
        """Convert the ModelInfo object back to a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "nsfw": self.nsfw,
            "creator_username": self.creator_username,
            "tags": self.tags,
            "model_versions": self.model_versions
        }

    def check_virus_scan_passed(self, version_index: int = 0) -> bool:
        """Check if the virus scan passed for a specific version (defaults to latest)"""
        if version_index >= len(self.model_versions):
            print(f"Warning: Version index {version_index} out of range")
            return False
        
        version = self.model_versions[version_index]
        if not version.get("files"):
            print(f"Warning: No files found for version {version_index}")
            return False
        
        scan_result = version["files"][0].get("virusScanResult")
        
        if scan_result == "Success":
            return True
        elif scan_result == "Pending":
            print(f"Warning: Virus scan still pending for {self.name}")
            return False
        elif scan_result == "Failed":
            print(f"Warning: Virus scan failed for {self.name}")
            return False
        elif scan_result == "Error":
            print(f"Warning: Virus scan error for {self.name}")
            return False
        else:
            print(f"Warning: Unknown virus scan result '{scan_result}' for {self.name}")
            return False

    def __str__(self) -> str:
        return f"ModelInfo(id={self.id}, name='{self.name}', type={self.type.value})"
    
    def __repr__(self) -> str:
        return self.__str__()