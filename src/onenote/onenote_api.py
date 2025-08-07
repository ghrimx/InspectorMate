import logging
import subprocess
import json
from ctypes import windll
from xml.etree import ElementTree as ET
from dataclasses import dataclass, field
from utilities.config import config as msconf

logger = logging.getLogger(__name__)


ON15_APP_ID = 'OneNote.Application.15'
ON15_SCHEMA = "{http://schemas.microsoft.com/office/onenote/2013/onenote}"
ON14_APP_ID = 'OneNote.Application.14'
ON14_SCHEMA = "{http://schemas.microsoft.com/office/onenote/2010/onenote}"
ON_APP = 'OneNote.Application'

namespace = ON15_SCHEMA

def executeScript(section_id: str) -> dict | None:
    ps1 = msconf.app_data_path.joinpath("onenotescrapper.ps1").as_posix()
    outfile = ""

    try:
        process = subprocess.run(
            ["powershell", 
             "-File", ps1, 
             "-SectionId", section_id, 
             "-OutputJson", outfile],
             shell=True,
             check=True,
             capture_output=True,
             encoding="utf-8"
             )
    except subprocess.CalledProcessError as e:
        logger.error(f"CalledProcessError={e}")
        logger.error(f"Command: {e.cmd}")
        logger.error(f"Return Code: {e.returncode}")
        logger.error(f"Output: {e.output}")
        logger.error(f"Error Output: {e.stderr}")
        return
    except Exception as e:
        logger.error(f"Unexepected error occured. Error: {e}")
        return

    try:
        output = json.loads(process.stdout)
    except Exception as e:
        logger.error(f"Cannot parse data into dict using json. Error={e}")
        return         

    return output

def execute(cmd: str) -> str | None:
    """
        Execute Powershell command in subprocess.

        Change Powershell Console Code Page to 65001 (UTF-8).
    """
    code_page_cmd = """$OutputEncoding = [Console]::InputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()"""

    try:
        process = subprocess.run(["powershell", "-Command", code_page_cmd+cmd], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"CalledProcessError={e}")
        return

    try:
        output = process.stdout.decode("UTF-8").strip()
    except Exception as e:
        logger.error(f"Cannot decode powershell command output using UTF-8 codec. Error={e}")
        logger.debug(f"Current Powershell Console Code Page={windll.kernel32.GetConsoleOutputCP()}")
        return         

    return output

def convert2XML(xml_str) -> ET.Element | None:
    xml: ET.Element = None
    try:
        xml = ET.fromstring(xml_str)
    except Exception as e:
        logger.error(e)
    
    return xml

def getHierarchy(node_id: str = "") -> ET.Element | None:
    ps = f"""
            $OneNote = New-Object -ComObject OneNote.Application
            [xml]$Hierarchy = ""
            $OneNote.GetHierarchy("{node_id}", [Microsoft.Office.InterOp.OneNote.HierarchyScope]::hsPages, [ref]$Hierarchy)
            $Hierarchy.outerXml
        """
    output = execute(ps)

    if output is None:
        return

    xml = convert2XML(output)

    return xml

def getPageContent(page_id: str = "") -> ET.Element | None:
    ps = f"""
            $OneNote = New-Object -ComObject OneNote.Application
            [xml]$pageXML = ""
            $OneNote.GetPageContent("{page_id}", [ref]$pageXML, [Microsoft.Office.InterOp.OneNote.PageInfo]::piBasic)
            $pageXML.outerXml
        """
    output = execute(ps)

    if output is None:
        return

    return convert2XML(output)


@dataclass
class Tag():
    object_id: str = ""
    lastModifiedTime: str = ""
    index: str = ""
    text: str = ""
    type: str = ""
    link: str = ""
    page_name: str = ""
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
                

def get_tag_data(page_id:str, parent_oe: ET.Element, tag: Tag | None = None) -> Tag:
        """Get data of a Tag element and return a dataclass"""
        for child in parent_oe:
                if child.tag == f"{namespace}Tag":
                    object_id = parent_oe.get('objectID')
                    index = child.get('index')
                    lastModifiedTime = child.get("lastModifiedTime")
                    creationTime = child.get('creationTime')
                    # link = cls.get_hyperlink_to_object(page_id, object_id)
                    tag = Tag(object_id=object_id, lastModifiedTime=lastModifiedTime, index=index, link=None, creationTime=creationTime)
                if child.tag == f"{namespace}T":
                    if not child.text is None:
                        tag.cdata.append(child.text)
                if child.tag == f"{namespace}OEChildren":
                    for oe_child in [oe for oe in child if oe.find(f'{namespace}Tag') is None]:
                        get_tag_data(page_id, oe_child, tag=tag)
        tag.cdata_to_text()
        return tag

def get_tags(page: Page, page_tree: ET.Element) -> list[Tag]:
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
        tag: Tag = get_tag_data(page.id, oe_element)
        tag.type = tagdefs[tag.index]
        tag.page_name = page.name
        tags.append(tag)
    return tags
    
