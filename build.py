import CIMgen
import os
import argparse
import importlib

parser = argparse.ArgumentParser(description='Generate some CIM classes.')
parser.add_argument('outdir', type=str, help='The output directory')
parser.add_argument('schemadir', type=str, help='The schema directory')
parser.add_argument('langdir', type=str, help='The langpack directory')
parser.add_argument('--cgmes_version', type=str, choices=['cgmes_v2_4_13', 'cgmes_v2_4_15', 'cgmes_v3_0_0'], default='cgmes_v2_4_15', help='CGMES Version')
args = parser.parse_args()

langPack = importlib.import_module(args.langdir + ".langPack")
schema_path = os.path.join(os.getcwd(), args.schemadir)
CIMgen.cim_generate(schema_path, args.outdir, args.cgmes_version, langPack)

langPack.resolve_headers(args.outdir)
