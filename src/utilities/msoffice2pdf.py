import logging
from pathlib import Path, WindowsPath
from win32com import client
from utilities.config import config as msconf
import subprocess

logger = logging.getLogger(__name__)

def word2pdf(source: Path, output_dir: Path):
    """Convert .doc/.docx files to PDF using MS Office."""
    app: client.CDispatch = client.Dispatch("Word.Application")
    wdFormatPDF = 17

    output = output_dir.joinpath("." + source.name).with_suffix(".pdf")

    try:
        doc = app.Documents.Open(str(source))
        doc.ExportAsFixedFormat(str(output), wdFormatPDF, Item=7, CreateBookmarks=1)
        doc.Close()
    except Exception as e:
        logger.error(f"Error converting Word document {source} to {output}: \nError: {e}")
        return None
    finally:
        app.Quit()

    return output

def excel2pdf(source: Path, output_dir: Path):
    """Convert .xls/.xlsx files to PDF using MS Office."""
    app: client.CDispatch = client.Dispatch("Excel.Application")

    output = output_dir.joinpath("." + source.name).with_suffix(".pdf")

    try:
        sheets = app.Workbooks.Open(str(source))
        sheets.ExportAsFixedFormat(0, str(output))
        sheets.Close()
    except Exception as e:
        logger.error(f"Error converting Excel document {source} to {output}: \nError: {e}")
        return None
    finally:
        app.Quit()

    return output


def ppt2pdf(source: Path, output_dir: Path):
    """Convert .ppt/.pptx files to PDF using MS Office."""
    app: client.CDispatch = client.Dispatch("PowerPoint.Application")
    ppFixedFormatTypePDF = 2

    output = output_dir.joinpath("." + source.name).with_suffix(".pdf")

    try:
        presentation = app.Presentations.Open(str(source), ReadOnly=True, WithWindow=False)
        presentation.ExportAsFixedFormat(str(output), ppFixedFormatTypePDF, PrintRange=None)
        presentation.Close()
    except Exception as e:
        logger.error(f"Error converting PowerPoint document {source} to {output}: \nError: {e}")
        return None
    finally:
        app.Quit()

    return output


def convert2pdf(source: Path, output_dir: Path) -> Path | Exception:
    """Convert files to PDF using MS Office based on their extension."""

    source = WindowsPath(source)
    output_dir = WindowsPath(output_dir)

    output = output_dir.joinpath("." + source.name).with_suffix(".pdf")

    # Check if a converted file already exist
    if output.exists():
        return output

    file_extension = source.suffix
    if file_extension in [".doc", ".docx", ".txt", ".xml"]:
        return word2pdf(source, output_dir)
    elif file_extension in [".xls", ".xlsx"]:
        return excel2pdf(source, output_dir)
    elif file_extension in [".ppt", ".pptx"]:
        return ppt2pdf(source, output_dir)
    else:
        return NotImplementedError("File extension not supported")


def office2pdf(source: Path, output_dir: Path) -> Path | Exception:
    """Convert Microsoft Office document using Powershell and Interop ComObject"""
    
    ps1 = msconf.app_data_path.joinpath("MsOfficeConverter.ps1").as_posix()

    output_file = output_dir.joinpath("." + source.name).with_suffix(".pdf")

    # Check if a converted file already exist
    if output_file.exists():
        return output_file

    try:
        process = subprocess.run(["powershell", "-File", ps1, source.as_posix(), output_file.as_posix()], shell=True, check=True, capture_output=True, text=True)
    except Exception as e:
        logger.error(f"Fail to execute script. Error={e}")
        return
    else:
        return output_file