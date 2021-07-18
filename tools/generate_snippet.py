import sys
import tempfile
import os.path
import json
import argparse
from datetime import datetime

import spec_download
import function_extract


SCOPE_OSL = 'source.osl'

def load_snippet_template(fpath):
    with open(fpath, 'r') as inf:
        return json.load(inf)

def generate_snippet_tpl(osl_func):
    args = []
    for (i, param) in enumerate(osl_func.params, 1):
        args.append("${{{0}:{1}}}".format(i, param.format()))

    arg_tpl = ', '.join(args)
    return f"{osl_func.name}({arg_tpl})"

def create_snippet(osl_func):
    desc = osl_func.format()
    prefix = osl_func.format(name_only=True)
    body = generate_snippet_tpl(osl_func)

    return {
        'description': desc,
        'prefix': prefix,
        'body': body,
        'scope': SCOPE_OSL
    }

def generate_snippets(tex_file, snippet_tpl, output_path):
    snippets = load_snippet_template(snippet_tpl)

    print("begin generate snippets...")

    signatures = {}
    for func in function_extract.extract_from_file(tex_file):
        count = signatures.get(func.name, 0)
        if count == 0:
            snippets[func.name] = create_snippet(func)
            signatures[func.name] = 1
        else:
            snippets[f"{func.name}_{count}"] = create_snippet(func)
            signatures[func.name] = count + 1

    with open(output_path, 'w', encoding='utf8') as outf:
        json.dump(snippets, outf, indent=4)

    print(f"snippets generate success [{output_path}]")

def download_snippets(snippet_tpl, output_path):
    snippets = load_snippet_template(snippet_tpl)

    with tempfile.TemporaryDirectory() as tempdir:
        now = datetime.now()
        temp_tex_file = os.path.join(tempdir, f'spec-{now.hour}-{now.minute}-{now.second}.tex')

        print("begin download language spec...")

        spec_download.download_document(temp_tex_file)

        print("language spec download success")

        generate_snippets(temp_tex_file, snippet_tpl, output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', type=str, required=True)
    parser.add_argument('-t', '--template', type=str, required=True)
    parser.add_argument('--spec', type=str, required=False)

    args = parser.parse_args()
    if args.spec is not None:
        generate_snippets(args.spec, args.template, args.output)
    else:
        download_snippets(args.template, args.output)
