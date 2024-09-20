from src.utilities import utils
import fitz

def test_image2hex():
    # image = r"C:\Users\debru\Documents\GitHub\InspectorMate\tests\files\tick.png"
    image = r"C:\Users\debru\Documents\GitHub\InspectorMate\src\resources\icons\clipboard-task.png"
    img_str, err = utils.image2hex(image)
    print(img_str)
    assert err == None



def test_queryFileID():
    fpath = r"C:\Users\debru\Documents\xyz pharma\Evidence\pre-inspection request\010\unassigned_file.xlsx"
    fileid = utils.queryFileID(fpath)
    print(fileid)

def test_queryFileNameByID():
    fileid = r"0x0000000000000000004500000000bef4"
    path = utils.queryFileNameByID(fileid)
    print(path)

def test_zipfile():
    fpath = r"C:\Users\debru\Downloads\Eudralink.zip"
    # fpath = r"C:\Users\debru\Downloads\pre-inspection request.zip"
    dest = r"C:\Users\debru\Documents\xyz_workspace\zipfolder"
    err = utils.unpackZip(fpath, dest)

    assert err == None


def test_unpackpdf():
    # filepath = "C:/Users/debru/Documents/xyz pharma/Evidence/001 PSMF_BBL_PV_04-Sep-2024 with attachements.pdf"
    filepath = "C:/Users/debru/Documents/xyz pharma/Evidence/pre-inspection request/001/PSMF.pdf"
    
    r = utils.unpackPDF(filepath)
    print(r)