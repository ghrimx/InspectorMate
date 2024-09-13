# Refactoring of https://github.com/varunsrin/one-py/

import os
import logging
from xml.etree import ElementTree as ET
import win32com.client
import pywintypes as pwt
from dataclasses import dataclass, field

from qtpy import QtWidgets

logger = logging.getLogger(__name__)

if win32com.client.gencache.is_readonly == True:
    win32com.client.gencache.is_readonly = False
    win32com.client.gencache.Rebuild()

# Check for the existing of ON_COM32_VERSION environment variable,
# Default value is set to 15
# Existing value 14 may be used
ON_COM32_VERSION = os.environ.get("ON_COM32_VERSION", 15)
ON15_APP_ID = 'OneNote.Application.15'
ON15_SCHEMA = "{http://schemas.microsoft.com/office/onenote/2013/onenote}"
ON14_APP_ID = 'OneNote.Application.14'
ON14_SCHEMA = "{http://schemas.microsoft.com/office/onenote/2010/onenote}"
ON_APP = 'OneNote.Application'

err_soluce_1 = f"(Office 2013) This COM object can not automate the makepy process - please run makepy manually for this object\n\nTo work around this, run regedit.exe, and navigate to\nHKEY_CLASSES_ROOT\\TypeLib\\{{0EA692EE-BB50-4E3C-AEF0-356D91732725}}\n\nThere should only be one subfolder in this class called 1.1.\nIf you see 1.0 or any other folders, you'll need to delete them.\n\nThe final hierarchy should look like this:\n|- {{0EA692EE-BB50-4E3C-AEF0-356D91732725}}\n|     |- 1.1\n|         |-0\n|         | |- win32\n|         |- FLAGS\n|         |- HELPDIR"
err_soluce_2 = "Clear contents of C:\\Users\\<username>\\AppData\\Local\\Temp\\gen_py"

namespace = ""

def logAndDisplayError(msg):
    logger.error(msg)
    QtWidgets.QMessageBox.critical(None,
                                   "Error with Onenote API",
                                   f"{msg}",
                                   buttons=QtWidgets.QMessageBox.StandardButton.Ok)


@dataclass
class Tag():
    object_id: str
    lastModifiedTime: str
    index: str
    text: str = ""
    type: str = ""
    link: str = ""
    creationTime: str = ""
    cdata: list = field(default_factory=list)

    def cdata_to_text(self):
        delim = "\n"
        self.text = delim.join([str(item) for item in self.cdata])

class Hierarchy():

    def __init__(self, xml: ET.Element = None):
        self._children = []
        if (xml != None): 
            self.__deserialize_from_xml(xml)

    def __deserialize_from_xml(self, xml):
        self._children = [Notebook(n) for n in xml]
                
    def __iter__(self):
        for c in self._children:
            yield c

class HierarchyNode():

    def __init__(self, parent=None):
        self.name = ""
        self.path = ""
        self.id = ""
        self.type = ""
        self.last_modified_time = ""
        self.synchronized = ""

    def deserialize_from_xml(self, xml: ET.Element):
        self.name = xml.get("name")
        self.path = xml.get("path")
        self.id = xml.get("ID")
        self.last_modified_time = xml.get("lastModifiedTime")

class Notebook(HierarchyNode):
    def __init__ (self, xml=None):
        super().__init__(self)
        self.nickname = ""
        self.color = ""
        self.is_currently_viewed = ""
        self.recycleBin = None
        self._children = []
        if (xml != None):
            self.__deserialize_from_xml(xml)

    def __deserialize_from_xml(self, xml: ET.Element):
        HierarchyNode.deserialize_from_xml(self, xml)
        self.nickname = xml.get("nickname")
        self.color = xml.get("color")
        self.is_currently_viewed = xml.get("isCurrentlyViewed")
        self.recycleBin = None
        for node in xml:
            if (node.tag == namespace + "Section"):
                self._children.append(Section(node, self)) 

            elif (node.tag == namespace + "SectionGroup"):
                if(node.get("isRecycleBin")):
                    self.recycleBin = SectionGroup(node, self)
                else:
                    self.type = "SectionGroup"
                    self._children.append(SectionGroup(node, self))

    def __iter__(self):
        for c in self._children:
            yield c

    def __str__(self):
        return self.name 


class SectionGroup(HierarchyNode):

    def __init__ (self, xml=None, parent_node=None):
        super().__init__(self)
        self.is_recycle_Bin = False
        self._children = []
        self.parent = parent_node
        if (xml != None):
            self.__deserialize_from_xml(xml)

    def __iter__(self):
        for c in self._children:
            yield c
    
    def __str__(self):
        return self.name 

    def __deserialize_from_xml(self, xml: ET.Element):
        HierarchyNode.deserialize_from_xml(self, xml)
        self.is_recycle_Bin = xml.get("isRecycleBin")
        for node in xml:
            if (node.tag == namespace + "SectionGroup"):
                self.type = "SectionGroup"
                self._children.append(SectionGroup(node, self))
            if (node.tag == namespace + "Section"):
                self.type = "SectionGroup"
                self._children.append(Section(node, self))


class Section(HierarchyNode):
       
    def __init__ (self, xml=None, parent_node=None):
        super().__init__(self)
        self.color = ""
        self.read_only = False
        self.is_currently_viewed = False      
        self._children = []
        self.parent = parent_node
        if (xml != None):
            self.__deserialize_from_xml(xml)

    def __iter__(self):
        for c in self._children:
            yield c
    
    def __str__(self):
        return self.name

    def __deserialize_from_xml(self, xml: ET.Element):
        HierarchyNode.deserialize_from_xml(self, xml)
        self.color = xml.get("color")
        try:
            self.read_only = xml.get("readOnly")
        except Exception as e:
            self.read_only = False
        try:
            self.is_currently_viewed = xml.get("isCurrentlyViewed")      
        except Exception as e:
            self.is_currently_viewed = False
        self.type = "Section"
        self._children = [Page(node, self) for node in xml]


class Page():
    
    def __init__ (self, xml=None, parent_node=None):
        self.name = ""
        self.id = ""
        self.date_time = ""
        self.last_modified_time = ""
        self.page_level = ""
        self.is_currently_viewed = ""
        self._children = []
        self.parent = parent_node
        if (xml != None):                         # != None is required here, since this can return false
            self.__deserialize_from_xml(xml)

    def __iter__(self):
        for c in self._children:
            yield c

    def __str__(self):
        return self.name 

    # Get / Set Meta

    def __deserialize_from_xml (self, xml: ET.Element):
        self.name = xml.get("name")
        self.id = xml.get("ID")
        self.date_time = xml.get("dateTime")
        self.last_modified_time = xml.get("lastModifiedTime")
        self.page_level = xml.get("pageLevel")
        self.is_currently_viewed = xml.get("isCurrentlyViewed")
        self._children = [Meta(node) for node in xml]


class Meta():
    def __init__ (self, xml = None):
        self.name = ""
        self.content = ""
        if (xml!=None):
            self.__deserialize_from_xml(xml)

    def __str__(self):
        return self.name 

    def __deserialize_from_xml (self, xml: ET.Element):
        self.name = xml.get("name")
        self.id = xml.get("content")


class PageContent():
    def __init__ (self, xml=None):
        self.name = ""
        self.id = ""
        self.date_time = ""
        self.last_modified_time = ""
        self.page_level = ""
        self.lang = ""
        self.is_currently_viewed = ""
        self._children= []
        self.files = []

        if (xml != None):
            self.__deserialize_from_xml(xml)

    def __iter__(self):
        for c in self._children:
            yield c
    
    def __str__(self):
        return self.name 

    def __deserialize_from_xml(self, xml: ET.Element):
            self.name = xml.get("name")
            self.id = xml.get("ID")
            self.date_time = xml.get("dateTime")
            self.last_modified_time = xml.get("lastModifiedTime")
            self.page_level = xml.get("pageLevel")
            self.lang = xml.get("lang")
            self.is_currently_viewed = xml.get("isCurrentlyViewed")
            for node in xml:
                if (node.tag == namespace + "Outline"):
                   self._children.append(Outline(node))
                elif (node.tag == namespace + "Ink"):
                    self.files.append(Ink(node))
                elif (node.tag == namespace + "Image"):
                    self.files.append(Image(node))
                elif (node.tag == namespace + "InsertedFile"):
                    self.files.append(InsertedFile(node))       
                elif (node.tag == namespace + "MediaFile"):
                    self.files.append(MediaFile(node, self))  
                elif (node.tag == namespace + "Title"):
                    self._children.append(Title(node))    
                elif (node.tag == namespace + "MediaPlaylist"):
                    self.media_playlist = MediaPlaylist(node, self)

class Title():
    def __init__ (self, xml=None):
        self.style = ""
        self.lang = ""
        self._children = []
        if (xml != None):
            self.__deserialize_from_xml(xml)

    def __str__ (self):
        return "Page Title"

    def __iter__ (self):
        for c in self._children:
            yield c

    def __deserialize_from_xml(self, xml: ET.Element):
        self.style = xml.get("style")
        self.lang = xml.get("lang")
        for node in xml:
            if (node.tag == namespace + "OE"):
                self._children.append(OE(node, self))


class Outline():

    def __init__ (self, xml=None):
        self.author = ""
        self.author_initials = ""
        self.last_modified_by = ""
        self.last_modified_by_initials = ""
        self.last_modified_time = ""
        self.id = ""
        self._children = []
        if (xml != None):
            self.__deserialize_from_xml(xml)

    def __iter__(self):
        for c in self._children:
            yield c

    def __str__(self):
        return "Outline"

    def __deserialize_from_xml (self, xml: ET.Element):     
        self.author = xml.get("author")
        self.author_initials = xml.get("authorInitials")
        self.last_modified_by = xml.get("lastModifiedBy")
        self.last_modified_by_initials = xml.get("lastModifiedByInitials")
        self.last_modified_time = xml.get("lastModifiedTime")
        self.id = xml.get("objectID")
        append = self._children.append
        for node in xml:
            if (node.tag == namespace + "OEChildren"):
                for childNode in node:
                    if (childNode.tag == namespace + "OE"):
                        append(OE(childNode, self))     


class Position():

    def __init__ (self, xml=None, parent_node=None):
        self.x = ""
        self.y = ""
        self.z = ""
        self.parent = parent_node
        if (xml!=None):
            self.__deserialize_from_xml(xml)

    def __deserialize_from_xml(self, xml):
        self.x = xml.get("x")
        self.y = xml.get("y")
        self.z = xml.get("z")


class Size():

    def __init__ (self, xml=None, parent_node=None):
        self.width = ""
        self.height = ""
        self.parent = parent_node
        if (xml!=None):
            self.__deserialize_from_xml(xml)

    def __deserialize_from_xml(self, xml: ET.Element):
        self.width = xml.get("width")
        self.height = xml.get("height")


class OE():

    def __init__ (self, xml=None, parent_node=None):
        
        self.creation_time = ""
        self.last_modified_time = ""
        self.last_modified_by = ""
        self.id = ""
        self.alignment = ""
        self.quick_style_index = ""
        self.style = ""
        self.text = ""
        self._children = []
        self.parent = parent_node
        self.files = []
        self.media_indices = []
        if (xml != None):
            self.__deserialize_from_xml(xml)

    def __iter__(self):
        for c in self._children:
            yield c
    
    def __str__(self):
        try:
            return self.text
        except AttributeError:
            return "Empty OE"

    def __deserialize_from_xml(self, xml: ET.Element):
        self.creation_time = xml.get("creationTime")
        self.last_modified_time = xml.get("lastModifiedTime")
        self.last_modified_by = xml.get("lastModifiedBy")
        self.id = xml.get("objectID")
        self.alignment = xml.get("alignment")
        self.quick_style_index = xml.get("quickStyleIndex")
        self.style = xml.get("style")

        for node in xml:
            if (node.tag == namespace + "T"):
                if (node.text != None):
                    self.text = node.text
                else:
                    self.text = "NO TEXT"

            elif (node.tag == namespace + "OEChildren"):
                for childNode in node:
                    if (childNode.tag == namespace + "OE"):
                        self._children.append(OE(childNode, self))

            elif (node.tag == namespace + "Image"):
                self.files.append(Image(node, self))

            elif (node.tag == namespace + "InkWord"):
                self.files.append(Ink(node, self))

            elif (node.tag == namespace + "InsertedFile"):
                self.files.append(InsertedFile(node, self))

            elif (node.tag == namespace + "MediaFile"):
                self.files.append(MediaFile(node, self))
                
            elif (node.tag == namespace + "MediaIndex"):
                self.media_indices.append(MediaIndex(node, self))


class InsertedFile():

    # need to add position data to this class

    def __init__ (self, xml=None, parent_node=None):
        self.path_cache = ""
        self.path_source = ""
        self.preferred_name = ""
        self.last_modified_time = ""
        self.last_modified_by = ""
        self.id = ""
        self.parent = parent_node
        if (xml != None):
            self.__deserialize_from_xml(xml)

    def __iter__ (self):
        yield None
    
    def __str__(self):
        try:
            return self.preferredName
        except AttributeError:
            return "Unnamed File"

    def __deserialize_from_xml(self, xml: ET.Element):
        self.path_cache = xml.get("pathCache")
        self.path_source = xml.get("pathSource")
        self.preferred_name = xml.get("preferredName")
        self.last_modified_time = xml.get("lastModifiedTime")
        self.last_modified_by = xml.get("lastModifiedBy")
        self.id = xml.get("objectID")   

  
class MediaReference():
    def __init__ (self, xml=None, parent_node=None):
        self.media_id = ""
        
    def __iter__ (self):
        yield None
    
    def __str__(self):
        return "Media Reference"

    def __deserialize_from_xml(self, xml: ET.Element):
        self.media_id = xml.get("mediaID")
        

class MediaPlaylist():
    def __init__ (self, xml=None, parent_node=None):
        self.media_references = []
        
    def __iter__(self):
        for c in self.media_references:
            yield c
    
    def __str__(self):
        return "Media Index"

    def __deserialize_from_xml(self, xml: ET.Element):
        for node in xml:
            if (node.tag == namespace + "MediaReference"):
                self.media_references.append(MediaReference(node, self))
        
        
class MediaIndex():
    def __init__ (self, xml=None, parent_node=None):
        self.media_reference = None
        self.time_index = 0
        
    def __iter__(self):
        yield None
    
    def __str__(self):
        return "Media Index"

    def __deserialize_from_xml(self, xml: ET.Element):
        self.time_index = xml.get("timeIndex")
        for node in xml:
            if (node.tag == namespace + "MediaReference"):
                self.media_reference = MediaReference(node, self)
                
  
class MediaFile(InsertedFile):
    def __init__ (self, xml=None, parent_node=None):
        self.media_reference = None
        super().__init__(xml, parent_node)
        
    def __iter__(self):
        yield None

    def __str__(self):
        try:
            return self.preferredName
        except AttributeError:
            return "Unnamed Media File"
            
    def __deserialize_from_xml(self, xml: ET.Element):
        super().__deserialize_from_xml(xml)
        for node in xml:
            if (node.tag == namespace + "MediaReference"):
                self.media_reference = MediaReference(node, self)
    
    
class Ink():

    # need to add position data to this class

    def __init__ (self, xml=None, parent_node=None):   
        self.recognized_text = ""
        self.x = ""
        self.y = ""
        self.ink_origin_x = ""
        self.ink_origin_y = ""
        self.width = ""
        self.height = ""
        self.data = ""
        self.callback_id = ""
        self.parent = parent_node

        if (xml != None):
            self.__deserialize_from_xml(xml)

    def __iter__ (self):
        yield None
    
    def __str__(self):
        try:
            return self.recognizedText
        except AttributeError:
            return "Unrecognized Ink"

    def __deserialize_from_xml(self, xml: ET.Element):
        self.recognized_text = xml.get("recognizedText")
        self.x = xml.get("x")
        self.y = xml.get("y")
        self.ink_origin_x = xml.get("inkOriginX")
        self.ink_origin_y = xml.get("inkOriginY")
        self.width = xml.get("width")
        self.height = xml.get("height")
            
        for node in xml:
            if (node.tag == namespace + "CallbackID"):
                self.callback_id = node.get("callbackID")
            elif (node.tag == namespace + "Data"):
                self.data = node.text


class Image():

    def __init__ (self, xml=None, parent_node=None):    
        self.format = ""
        self.original_page_number = ""
        self.last_modified_time = ""
        self.id = ""
        self.callback_id = None
        self.data = ""
        self.parent = parent_node
        if (xml != None):
            self.__deserialize_from_xml(xml)

    def __iter__ (self):
        yield None
    
    def __str__(self):
        return self.format + " Image"

    def __deserialize_from_xml(self, xml: ET.Element):
        self.format = xml.get("format")
        self.original_page_number = xml.get("originalPageNumber")
        self.last_modified_time = xml.get("lastModifiedTime")
        self.id = xml.get("objectID")
        for node in xml:
            if (node.tag == namespace + "CallbackID"):
                self.callback_id = node.get("callbackID")
            elif (node.tag == namespace + "Data"):
                if (node.text != None):
                    self.data = node.text
                
class OneNote():
    
    def __init__(self, cdispatch, namespace):
        self.process = cdispatch
        self.namespace = namespace
        
    @classmethod
    def connect(cls):
        try:
            version = int(ON_COM32_VERSION)
            global namespace
            if version == 15:
                cdispatch = win32com.client.Dispatch(ON15_APP_ID) # get COM object
                # module = win32com.client.gencache.EnsureModule("{0EA692EE-BB50-4E3C-AEF0-356D91732725}", 0, 1, 1) # Loads python support
                # cdispatch = module.Application(cdispatch)
                namespace = ON15_SCHEMA
            elif version == 14:
                cdispatch = win32com.client.Dispatch(ON14_APP_ID)
                namespace = ON14_SCHEMA
            return cls(cdispatch, namespace), None
        except Exception as e:
            err_soluce_1 = f"(Office 2013) This COM object can not automate the makepy process - please run makepy manually for this object\n\nTo work around this, run regedit.exe, and navigate to\nHKEY_CLASSES_ROOT\\TypeLib\\{{0EA692EE-BB50-4E3C-AEF0-356D91732725}}\n\nThere should only be one subfolder in this class called 1.1.\nIf you see 1.0 or any other folders, you'll need to delete them.\n\nThe final hierarchy should look like this:\n|- {{0EA692EE-BB50-4E3C-AEF0-356D91732725}}\n|     |- 1.1\n|         |-0\n|         | |- win32\n|         |- FLAGS\n|         |- HELPDIR"
            err_soluce_2 = "Clear contents of C:\\Users\\<username>\\AppData\\Local\\Temp\\gen_py"
            msg = f"Error starting onenote {ON_COM32_VERSION}\n\nError: {e}\n\nPossible solution #1:\n{err_soluce_1}\n\nPossible solution #2:\n{err_soluce_2}"
            logAndDisplayError(msg)
            return None, e
        
    def get_hierarchy(self, start_node_id="", hierarchy_scope=4):
        """
          HierarchyScope
          0 - Gets just the start node specified and no descendants.
          1 - Gets the immediate child nodes of the start node, and no descendants in higher or lower subsection groups.
          2 - Gets all notebooks below the start node, or root.
          3 - Gets all sections below the start node, including sections in section groups and subsection groups.
          4 - Gets all pages below the start node, including all pages in section groups and subsection groups.
        """
        try:
            return self.process.GetHierarchy(start_node_id, hierarchy_scope), None
        except Exception as e:
            msg = f"{e} - Could not Get Hierarchy\n\nPossible solution #1:\n{err_soluce_1}\n\nPossible solution #2:\n{err_soluce_2}"
            logAndDisplayError(msg)
            return None, e

    def update_hierarchy(self, changes_xml_in):
        try:
            self.process.UpdateHierarchy(changes_xml_in)
        except Exception as e:
            logger.error(f"{e} - Could not Update Hierarchy")

    def open_hierarchy(self, path, relative_to_object_id, object_id, create_file_type=0):
        """
          CreateFileType
          0 - Creates no new object.
          1 - Creates a notebook with the specified name at the specified location.
          2 - Creates a section group with the specified name at the specified location.
          3 - Creates a section with the specified name at the specified location.
        """
        try:
            return(self.process.OpenHierarchy(path, relative_to_object_id, "", create_file_type))
        except Exception as e:
            logger.error(f"{e} - Could not Open Hierarchy")

    def delete_hierarchy (self, object_id, last_modified):
        try:
            self.process.DeleteHierarchy(object_id, pwt.Time(last_modified))
        except Exception as e: 
            logger.error(f"{e} - Could not Delete Hierarchy")

    def create_new_page (self, section_id, new_page_style=0):
        """
          NewPageStyle
          0 - Create a Page that has Default Page Style
          1 - Create a blank page with no title
          2 - Createa blank page that has no title
        """
        try:
            self.process.CreateNewPage(section_id, "", new_page_style)
        except Exception as e: 
            logger.error(f"{e} - Unable to create the page")
            
    def close_notebook(self, notebook_id):
        try:
            self.process.CloseNotebook(notebook_id)
        except Exception as e:
            logger.error(f"{e} - Could not Close Notebook") 

    def get_page_content(self, page_id, page_info=0):
        """
          PageInfo
          0 - Returns only basic page content, without selection markup and binary data objects. This is the standard value to pass.
          1 - Returns page content with no selection markup, but with all binary data.
          2 - Returns page content with selection markup, but no binary data.
          3 - Returns page content with selection markup and all binary data.
        """
        try:
            return(self.process.GetPageContent(page_id, "", page_info))
        except Exception as e: 
            logger.error(f"{e} - Could not get Page Content") 
            
    def update_page_content(self, page_changes_xml_in, last_modified):
        try:
            self.process.UpdatePageContent(page_changes_xml_in, pwt.Time(last_modified))
        except Exception as e: 
            logger.error(f"{e} - Could not Update Page Content") 
            
    def get_binary_page_content(self, page_id, callback_id):
        try:
            return(self.process.GetBinaryPageContent(page_id, callback_id))
        except Exception as e: 
            logger.error(f"{e} - Could not Get Binary Page Content")

    def delete_page_content(self, page_id, object_id, last_modified):
        try:
            self.process.DeletePageContent(page_id, object_id, pwt.Time(last_modified))
        except Exception as e: 
            logger.error(f"{e} - Could not Delete Page Content")


      # Actions


    def navigate_to(self, object_id, new_window=False):
        try:
            self.process.NavigateTo(object_id, "", new_window)
        except Exception as e: 
            logger.error(f"{e} - Could not Navigate To")

    def publish(self, hierarchy_id, target_file_path, publish_format, clsid_of_exporter=""):
        """
         PublishFormat
          0 - Published page is in .one format.
          1 - Published page is in .onea format.
          2 - Published page is in .mht format.
          3 - Published page is in .pdf format.
          4 - Published page is in .xps format.
          5 - Published page is in .doc or .docx format.
          6 - Published page is in enhanced metafile (.emf) format.
        """
        try:
            self.process.Publish(hierarchy_id, target_file_path, publish_format, clsid_of_exporter)
        except Exception as e: 
            logger.error(f"{e} - Could not Publish")

    def open_package(self, path_package, path_dest):
        try:
            return(self.process.OpenPackage(path_package, path_dest))
        except Exception as e: 
            logger.error(f"{e} - Could not Open Package")

    def get_hyperlink_to_object(self, hierarchy_id, target_file_path=""):
        try:
            return(self.process.GetHyperlinkToObject(hierarchy_id, target_file_path))
        except Exception as e: 
            logger.error(f"{e} - Could not Get Hyperlink")

    def find_pages(self, start_node_id, search_string, display):
        try:
            return(self.process.FindPages(start_node_id, search_string, "", False, display))
        except Exception as e: 
            logger.error(f"{e} - Could not Find Pages")

    def get_special_location(self, special_location=0):
        """
          SpecialLocation
          0 - Gets the path to the Backup Folders folder location.
          1 - Gets the path to the Unfiled Notes folder location.
          2 - Gets the path to the Default Notebook folder location.
        """
        try:
            return(self.process.GetSpecialLocation(special_location))
        except Exception as e: 
            logger.error(f"{e} - Could not retreive special location")
    
    def get_parent(self, object_id):
        try:
            return(self.process.GetHierarchyParent(object_id))
        except Exception as e:
            logger.error(f"{e} - Could not retrieve parent object")

    def get_tags(self, page_id: str, page_tree: ET.Element) -> list[Tag]:
        """Return a list of tags from the xml of a onenote page"""
        tags = []

        # Build a dict containing the tag index definition
        tagdefs = {}
        for tagdef in page_tree.findall(f".//{namespace}TagDef"):
            index = tagdef.get("index")
            name = tagdef.get("name").capitalize()
            tagdefs[index] = name

        # Find the 'one:OE' elements that contain Tag child element
        # TODO: change namespace to remove curly braces -> page_root.findall('.//one:OE[one:Tag]', namespace)
        for oe_element in page_tree.findall(f".//{namespace}OE[{namespace}Tag]"):
            tag = self.get_tag_data(page_id, oe_element)
            tag.type = tagdefs[tag.index]
            tags.append(tag)
        return tags
    
    def get_tag_data(self, page_id:str, parent_oe: ET.Element, tag: Tag | None = None) -> Tag:
        """Get data of a Tag element and return a dataclass"""
        for child in parent_oe:
                if child.tag == f"{namespace}Tag":
                    object_id = parent_oe.get('objectID')
                    index = child.get('index')
                    lastModifiedTime = child.get("lastModifiedTime")
                    creationTime = child.get('creationTime')
                    link = self.get_hyperlink_to_object(page_id, object_id)
                    tag = Tag(object_id=object_id, lastModifiedTime=lastModifiedTime, index=index, link=link, creationTime=creationTime)
                if child.tag == f"{namespace}T":
                    if not child.text is None:
                        tag.cdata.append(child.text)
                if child.tag == f"{namespace}OEChildren":
                    for oe_child in [oe for oe in child if oe.find(f'{namespace}Tag') is None]:
                        self.get_tag_data(page_id, oe_child, tag=tag)
        tag.cdata_to_text()
        return tag


