import os
import chevron
import logging
logger = logging.getLogger(__name__)


# This makes sure we have somewhere to write the generated files
def setup(version_path):
    if not os.path.exists(version_path):
        os.makedirs(version_path)


def location(version):
    return "cimpy." + version + ".Base"


base = {
    "base_class": "Base",
    "class_location": location
}

template_files = [{"filename": "json_ld_template.mustache", "ext": ".json"}]


def get_class_location(class_name, class_map, version):
    pass


def _set_default(text, render):
    return '0.0'


def set_enum_classes(new_enum_classes):
    return


def set_float_classes(new_float_classes):
    return


def run_template(version_path, class_details):
    for template_info in template_files:
        class_file = os.path.join(version_path, class_details['class_name']
                                  + template_info["ext"])
        if not os.path.exists(class_file):
            with open(class_file, 'w') as file:
                template_path = os.path.join(os.getcwd(), 'json_ld/templates',
                                             template_info["filename"])
                class_details['setDefault'] = _set_default
                with open(template_path) as f:
                    args = {
                        'data': class_details,
                        'template': f
                        }
                    output = chevron.render(**args)
                file.write(output)


def resolve_headers(path):
    pass
