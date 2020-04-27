from python import langPackPython
import cimCodebaseGenerator
import os
import argparse

parser = argparse.ArgumentParser(description='Generate some CIM classes.')

parser.add_argument('outdir', type=str, help='The output directory')

args = parser.parse_args()
schema_path = os.path.join(os.getcwd(), "cgmes_schema/cgmes_v2_4_15_schema")
cimCodebaseGenerator.cim_generate(schema_path, args.outdir, "cgmes_v2_4_15", langPackPython)
