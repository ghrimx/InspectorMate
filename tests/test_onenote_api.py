import pytest
from src.utils.onenote_api import OneNote, Hierarchy, Page, PageContent
from xml.etree import ElementTree as ET
from utils.utils import find_match

def test_onenote_api():
    onenote = OneNote.connect()
    assert not isinstance(onenote, RuntimeError)

def test_onenote_singleton():
    oe1 = OneNote.connect()
    oe2 = OneNote.connect()
    print(oe1 == oe2)
    assert oe1 == oe2


def test_get_hierarchy():
    onenote = OneNote.connect()
    element_tree = ET.fromstring(onenote.get_hierarchy("",4))

    hierarchy = Hierarchy(element_tree)

    for notebook in hierarchy:
            for section in notebook:
                print(section.name)
                for page in section:
                     print(f'\t page: {page.name}')

def test_get_page_content():
    onenote = OneNote.connect()
    page_content_xml = ET.fromstring(onenote.get_page_content(page_id='{52649BB7-986D-453A-BBC0-99E2E9339D2C}{1}{E1956754159043189007021956982225985552137391}'))
    page_content = PageContent(page_content_xml)
    for oe in page_content:
        for i in oe:
            print(i)

def test_get_tags():
    onenote = OneNote.connect()
    page_content_xml = ET.fromstring(onenote.get_page_content(page_id='{52649BB7-986D-453A-BBC0-99E2E9339D2C}{1}{E1956754159043189007021956982225985552137391}'))
    tags = onenote.get_tags(page_content_xml)
    for tag in tags:
        print(f"{tag.object_id} \n\t {tag.text}" )

    assert len(tags) != 0

def test_process_all_pages_of_section():
    section_id = "{52649BB7-986D-453A-BBC0-99E2E9339D2C}{1}{B0}"
    onenote = OneNote.connect()
    element_tree = ET.fromstring(onenote.get_hierarchy(section_id,4))
    hierarchy = Hierarchy(element_tree)
    all_tags = []
    for page in hierarchy:
        page_tree = ET.fromstring(onenote.get_page_content(page_id=page.id))
        tags = onenote.get_tags(page_id=page.id, page_tree=page_tree)
        all_tags.extend(tags)
    for tag in all_tags:
        print(f"{find_match(tag.text)}: {tag.link}")

         

        


