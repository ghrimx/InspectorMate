import unittest
import xml.etree.ElementTree as ET
from src.utils import pyonenote

on = pyonenote.OneNote()

class TestOneNote(unittest.TestCase):
    """Unit test case of pyonenote"""
    process = pyonenote.OEProcess()

    tree = ET.parse('tests\onenote_page.xml')
    root = tree.getroot()

    def return_exception(self, x):
        try:
            print(100/x)
            return None
        except Exception as e:
            version = 15
            err_solution = """
                (Office 2013) This COM object can not automate the makepy process - please run makepy manually for this object

                To work around this, run regedit.exe, and navigate to

                HKEY_CLASSES_ROOT\TypeLib\{0EA692EE-BB50-4E3C-AEF0-356D91732725}

                There should only be one subfolder in this class called 1.1. 
                If you see 1.0 or any other folders, you'll need to delete them. 
                The final hierarchy should look like this:

                |- {0EA692EE-BB50-4E3C-AEF0-356D91732725}
                |     |- 1.1
                |         |-0
                |         | |- win32
                |         |- FLAGDS
                |         |- HELPDIR

                """
            msg = f"Error starting ontenote: {version} \n{e}\n {err_solution}"
            return RuntimeError(msg)
        
    def test_return_exception_postivecase(self):
        err = self.return_exception(x=2)
        if isinstance(err, Exception):
            print(err)
        elif err == None: 
            print('OK!')

    def test_return_exception_negativecase(self):
        err = self.return_exception(x=0)
        if isinstance(err, Exception):
            print(err)
        elif err == None: 
            print('OK!')
    
    def test_get_tags(self):
        tags = self.process.get_tags(self.root)
        for tag in tags:
            print(tag)

if __name__ == '__main__':
    unittest.main()