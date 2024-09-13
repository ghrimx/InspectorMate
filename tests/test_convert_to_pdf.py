from os import path, remove
# from src.utilities.utils import convert_to_pdf
from src.utilities.msoffice2pdf import convert
from pathlib import Path

def test_soffice():
    src = "TestPresentation.pptx"
    # src = "C:/Users/debru/Documents/xyz_workspace/Attachments/Document request/Test_document.docx"
    dst = "C:/Users/debru/Documents/xyz_workspace/Attachments/Document request/"
    # r = convert_to_pdf(src, dst)
    # r = convert_to_pdf_libreoffice(src, dst)
    r = convert(Path(src), Path(src).parent)
    print(r)


def replace_suffix(src):
    return Path(src).with_suffix('.pdf')


def convert_to_pdf_libreoffice(source, output_dir, timeout=None) -> str:
    from subprocess import run, PIPE
    from re import search
    from shutil import copy2
    from datetime import datetime
    """Convert MS Office files to PDF using LibreOffice."""
    # soffice = "C:/Users/debru/Documents/GitHub/InspectorMate/src/data/LibreOfficePortable/App/libreoffice/program/soffice.com"
    soffice = "C:/Users/debru/AppData/Roaming/.inspectormate/LibreOfficePortable/App/libreoffice/program/soffice.com"
    output = None
    temp_filename = path.join(output_dir, datetime.now().strftime("%Y%m%d%H%M%S%f") + path.basename(source))
    copy2(source, temp_filename)

    try:
        process = run([soffice, '--headless', '--convert-to', 'pdf', '--outdir', output_dir, temp_filename],
                      stdout=PIPE, stderr=PIPE, timeout=timeout, check=True)
        filename = search(r'-> (.*?) using filter', process.stdout.decode("latin-1"))
        remove_files([temp_filename])
        output = filename.group(1).replace("\\", "/") if filename else None
    except Exception as e:
        return f"Error converting with LibreOffice: {e}"

    return output

def remove_files(temp_files_attach):
    """Remove temporary files."""
    for file_temp in temp_files_attach:
        if path.isfile(file_temp):
            remove(file_temp)

