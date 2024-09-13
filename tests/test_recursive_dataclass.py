import pytest
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Person:
    name: str
    age: int
    children: Optional[List['Person']] = field(default_factory=list)

    @classmethod
    def from_xml(cls, element: ET.Element) -> 'Person':
        # Parse the name and age from the current element
        name = element.find('name').text
        age = int(element.find('age').text)

        # Parse children if any
        children = []
        for child_element in element.findall('child'):
            children.append(cls.from_xml(child_element))
        
        return cls(name=name, age=age, children=children)

# Example XML string with nested person elements
xml_str = '''
<person>
    <name>John Doe</name>
    <age>30</age>
    <child>
        <name>Jane Doe</name>
        <age>10</age>
    </child>
    <child>
        <name>Jim Doe</name>
        <age>8</age>
        <child>
            <name>Johnny Doe</name>
            <age>2</age>
        </child>
    </child>
</person>
'''

# Parse the XML string and create a Person instance
def test_recursive_dataclass():
    root = ET.fromstring(xml_str)
    person = Person.from_xml(root)
    print(person)