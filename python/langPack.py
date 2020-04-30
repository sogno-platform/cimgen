import os
import chevron
import logging
logger = logging.getLogger(__name__)

# This makes sure we have somewhere to write the classes, and
# creates a couple of files the python implementation needs.
def setup(version_path):
    if not os.path.exists(version_path):
        os.makedirs(version_path)
        _create_init(version_path)
        _create_base(version_path)

def location(version):
     return "cimpy." + version + ".Base";

base = {
    "base_class": "Base",
    "class_location": location
}

template_files=[ { "filename": "cimpy_class_template.mustache", "ext": ".py" } ]

def get_class_location(class_name, class_map, version):
    # Check if the current class has a parent class
    if class_map[class_name].superClass() and class_map[class_name].superClass() in class_map:
        return 'cimpy.' + version + "." + class_map[class_name].superClass()
    else:
        logger.info("Parent class {} for class {} not found".format(class_map[class_name].superClass(), class_name))
        return None

partials = {}

# called by chevron, text contains the label {{dataType}}, which is evaluated by the renderer (see class template)
def _set_default(text, render):
    result = render(text)

    # the field {{dataType}} either contains the multiplicity of an attribute if it is a reference or otherwise the
    # datatype of the attribute. If no datatype is set and there is also no multiplicity entry for an attribute, the
    # default value is set to None. The multiplicity is set for all attributes, but the datatype is only set for basic
    # data types. If the data type entry for an attribute is missing, the attribute contains a reference and therefore
    # the default value is either None or [] depending on the mutliplicity. See also write_python_files
    if result in ['M:1', 'M:0..1', 'M:1..1', '']:
        return 'None'
    elif result in ['M:0..n', 'M:1..n'] or 'M:' in result:
        return '"list"'

    result = result.split('#')[1]
    if result in ['integer', 'Integer']:
        return '0'
    elif result in ['String', 'DateTime', 'Date']:
        return "''"
    elif result == 'Boolean':
        return 'False'
    else:
        # everything else should be a float
        return '0.0'

def set_enum_classes(new_enum_classes):
    return

def set_float_classes(new_float_classes):
    return

def run_template(version_path, class_details):
    for template_info in template_files:
        class_file = os.path.join(version_path, class_details['class_name'] + template_info["ext"])
        if not os.path.exists(class_file):
            with open(class_file, 'w') as file:
                with open(template_info["filename"]) as f:
                    args = {
                        'data': class_details,
                        'template': f,
                        'partials_dict': partials
                    }
                    output = chevron.render(**args)
                file.write(output)


def _create_init(path):
    init_file = path + "/__init__.py"
    with open(init_file, 'w'):
        pass

# creates the Base class file, all classes inherit from this class
def _create_base(path):
    base_path = path + "/Base.py"
    base = ['from enum import Enum\n\n', '\n', 'class Base():\n', '    """\n', '    Base Class for CIM\n',
            '    """\n\n',
            '    cgmesProfile = Enum("cgmesProfile", {"EQ": 0, "SSH": 1, "TP": 2, "SV": 3, "DY": 4, "GL": 5, "DI": 6})',
            '\n\n', '    def __init__(self, *args, **kw_args):\n', '        pass\n',
            '\n', '    def printxml(self, dict={}):\n', '        return dict\n']

    with open(base_path, 'w') as f:
        for line in base:
            f.write(line)


