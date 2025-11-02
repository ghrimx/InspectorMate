import logging
from pathlib import Path
from utilities.config import config as msconf
import subprocess

logger = logging.getLogger(__name__)


def office2pdf(source: Path, output_dir: Path) -> Path | Exception:
    """Convert Microsoft Office document using Powershell and Interop ComObject"""
    
    ps1 = msconf.app_data_path.joinpath("MsOfficeConverter.ps1").as_posix()

    output_file = output_dir.joinpath("." + source.name).with_suffix(".pdf")

    # Check if a converted file already exist
    if output_file.is_file():
        return output_file

    try:
        process = subprocess.run(["powershell",
                                  "-File",
                                  ps1,
                                  source.as_posix(),
                                  output_file.as_posix()],
                                  shell=True,
                                  check=True,
                                  capture_output=True,
                                  text=True)
    except Exception as e:
        logger.error(f"Fail to execute script. Error={e}")
        return None
    else:
        if output_file.is_file():
            return output_file
        return None