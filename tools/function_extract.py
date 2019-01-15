import io
import re

CHAPTER_FUNCTIONS = r'\chapter{Standard Library Functions}'
API_ITEM_DIREC = r'\apiitem{'
API_ITEM_END_DIREC = r'\apiend'
API_INDEX_DIREC = r'\indexapi'
CHAPTER_ITEM_DIREC = r'\chapter'
TEX_BIGSPC_DIREC = r'\bigspc'
TEX_CLOSURE_COLOR_DIREC = r'\colorclosure'
ELLIPSIS_NOTATION = '...'

NEW_LINE = '\n'
COLOR_CLOSURE = 'closure color'
OUTPUT_MARK = 'output'

FUNC_PATTERN = re.compile(r'(?:(?P<rtype>[^,\n]+?)\\? +)?\{\\ce +(?P<name>\w+)\} +\(\s*(?P<params>.+?)\s*\)')
GENERIC_TYPE_PATTERN = re.compile(r'\\emph *\{(\w+?)\}')
PARAM_TEX_STYLE_PATTERN = re.compile(r'\$\\mathtt\{(\w+)\}_(\w+)\$')

class OSLFuncInfo(object):
    class OSLParamInfo(object):
        def __init__(self, type_, name, is_output=False):
            self.param_type = type_
            self.param_name = name
            self.is_output = is_output

        def format(self):
            result = []
            if self.is_output:
                result.append(OUTPUT_MARK)

            if self.param_type == '':
                result.append(self.param_name)
            else:
                result.append(self.param_type)
                result.append(self.param_name)

            return ' '.join(result)

    def __init__(self, name, rtype, *params):
        self.name = name
        self.rtype = rtype if bool(rtype) else ''
        self.params = []

        for param in params:
            self.add_param(*param)

    def add_param(self, type_, name, is_output=False):
        self.params.append(OSLFuncInfo.OSLParamInfo(type_, name, is_output))

    def _format_params(self, name_only=False):
        if name_only:
            return ', '.join(param.param_name for param in self.params)
        else:
            return ', '.join(param.format() for param in self.params)

    def format(self, name_only=False):
        if name_only:
            return f"{self.name}({self._format_params(True)})"
        else:
            return f"{self.rtype} {self.name}({self._format_params()})"


def parse_function_params(param_notation):
    def normalize_param_name(name):
        style_match = PARAM_TEX_STYLE_PATTERN.search(name)
        if style_match is not None:
            name = style_match.group(1) + style_match.group(2)

        name = name.replace('\\_', '_')
        return name

    def normalize_param_decl(types):
        types = types.replace(r'\\ ', ' ')
        types = types.replace(TEX_BIGSPC_DIREC, '')
        return GENERIC_TYPE_PATTERN.sub(lambda m: m.group(1), types).strip()

    result = []
    params = param_notation.split(',')

    for param in params:
        param = param.strip()
        if param.startswith(ELLIPSIS_NOTATION):
            result.append(('', ELLIPSIS_NOTATION, False))
        else:
            param = normalize_param_decl(param)
            param_segments = re.split(' +', param)

            is_output = False
            param_type = ''
            param_name = ''

            if len(param_segments) == 1:
                param_name = normalize_param_name(param_segments[0])
            else:
                if len(param_segments) == 3:
                    if param_segments[0] == OUTPUT_MARK:
                        is_output = True
                    else:
                        raise RuntimeError("invalid function signature")

                    param_type = param_segments[1]
                    param_name = param_segments[2]
                else:
                    param_type = param_segments[0]
                    param_name = param_segments[1]

                param_name = normalize_param_name(param_name)

            result.append((param_type, param_name, is_output))

    return result

def parse_function_rtype(rtype):
    if rtype is None:
        return ''
    else:
        rtype = rtype.replace(API_ITEM_DIREC, '')
        rtype = rtype.replace(TEX_CLOSURE_COLOR_DIREC, COLOR_CLOSURE)
        rtype = GENERIC_TYPE_PATTERN.sub(lambda m: m.group(1), rtype)
        return rtype.strip()

def extract_function_info(reader, init_line):
    def read_next_func_chunk(current_line):
        output = []
        line = current_line
        while True:
            line = line.strip()
            if line.endswith('}') or line.endswith(r'\\'):
                output.append(line)
                return ' '.join(output)
            else:
                if len(line) > 0:
                    # discard empty lines
                    output.append(line)
                line = reader.readline()

    result = []

    line = read_next_func_chunk(init_line)
    while True:
        if line.startswith(API_ITEM_END_DIREC) or line.startswith(API_INDEX_DIREC):
            return result
        else:
            pos = 0
            while True:
                match = FUNC_PATTERN.search(line, pos)
                if match is not None:
                    params = parse_function_params(match.group('params'))
                    rtype = parse_function_rtype(match.group('rtype'))
                    func_info = OSLFuncInfo(match.group('name'), rtype, *params)
                    result.append(func_info)
                    pos = match.end()
                else:
                    break

        line = read_next_func_chunk(reader.readline())

def scan_api_functions(reader):
    while True:
        line = reader.readline()
        if not line.startswith(CHAPTER_ITEM_DIREC):
            if line.startswith(API_ITEM_DIREC):
                result = extract_function_info(reader, line)
                if result is not None and len(result) > 0:
                    for func in result:
                        if func.name.startswith('D') and func.rtype == '':
                            # fix Dy, Dz explicitly
                            func.rtype = func.params[0].param_type

                    yield result
        else:
            return

def read_until_first_function_line(file):
    chapter_found = False

    while True:
        line = file.readline()

        if len(line) > 0:
            if chapter_found:
                if line.startswith(API_ITEM_DIREC):
                    byte_len = len(line.encode())
                    file.seek(file.tell() - byte_len - 1, io.SEEK_SET)
                    return True
            else:
                if line.strip() == CHAPTER_FUNCTIONS:
                    chapter_found = True
        else:
            return False

def extract_from_file(specfile):
    with open(specfile, 'r') as inf:
        if read_until_first_function_line(inf):
            for func_group in scan_api_functions(inf):
                for func in func_group:
                    yield func

def main():
    # testing
    with open('./spec.tex', 'r') as inf:
        if read_until_first_function_line(inf):
            with open('./functions.txt', 'w', encoding='utf8') as outf:
                for func_group in scan_api_functions(inf):
                    for func in func_group:
                        outf.write(func.format())
                        outf.write(NEW_LINE)
                    outf.write(NEW_LINE)
        else:
            print('failed')

if __name__ == "__main__":
    main()