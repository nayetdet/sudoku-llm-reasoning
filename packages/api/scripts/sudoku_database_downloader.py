import requests
from github import Github
from github.Repository import Repository
from pathlib import Path
from tqdm import tqdm
from api.config import Config

class SudokuDatabaseDownloader:
    def __init__(self, repository: str) -> None:
        self.__github: Github = Github()
        self.__repository: Repository = self.__github.get_repo(repository)

    def download(self, output_path: Path) -> None:
        for asset in self.__repository.get_latest_release().get_assets():
            if not asset.name.endswith(".db"):
                continue

            output_file: Path = output_path / asset.name
            if output_file.exists():
                print(f"File '{output_file}' already exists, skipping download")
                return

            with requests.get(asset.browser_download_url, stream=True) as response:
                response.raise_for_status()
                chunk_size: int = 65536 # 64 KB
                total_size: int = int(response.headers.get("Content-Length", 0))
                with tqdm(desc=f"Downloading {asset.name}", total=total_size, unit="B", unit_divisor=1024, unit_scale=True) as progress:
                    with open(output_file, "wb") as file:
                        for chunk in response.iter_content(chunk_size=chunk_size):
                            if chunk:
                                file.write(chunk)
                                progress.update(len(chunk))

            print(f"Successfully downloaded '{asset.name}' to {output_file}")
            return

        raise FileNotFoundError("Could not find any database asset for this repository")

def main() -> None:
    sudoku_database_downloader: SudokuDatabaseDownloader = SudokuDatabaseDownloader(repository="nayetdet/sudoku-llm-reasoning")
    sudoku_database_downloader.download(output_path=Config.Paths.DATA)

if __name__ == "__main__":
    main()
