import re


SIMPLE_WORDS_RE = r'^(\s?\w+)+$'
OPEN_MULT_RE = r'^(\w+)\s?:\s?(\w+)\s?\*\s?\[$'
CLOSE_MULT_RE = r'^\s*\]$'


all_lines_re = [SIMPLE_WORDS_RE, OPEN_MULT_RE, CLOSE_MULT_RE]


def simple_words_parser(words):
    def f(input_lines, state):
        values = input_lines.pop(0).split(' ')
        if len(values) != len(words):
            raise Exception('Trying to extract ({}) on values ()'.format(words, values))
        state.update({word: value for word,value in zip(words, values)})
    return f


def lines_group_parser(list_name, iterations_varname, subparser):
    def f(input_lines, state):
        iterations_nb = int(state[iterations_varname])
        state[list_name] = []
        for _ in range(iterations_nb):
            state[list_name].append(file_parser(subparser, input_lines))
    return f


def check_lines_format(lines):
    for i,line in enumerate(lines):
        if all(not re.match(regex, line) for regex in all_lines_re):
            print('Error parsing line', i, ': "{}"'.format(line))
            exit(1)


def extract_subgrammar(grammar_lines):
    subgrammar = []
    brackets_opened = 1
    while brackets_opened:
        tmp_line = grammar_lines.pop(0)
        if re.match(OPEN_MULT_RE, tmp_line):
            brackets_opened += 1
        elif re.match(CLOSE_MULT_RE, tmp_line):
            brackets_opened -= 1
        subgrammar.append(tmp_line)
    return subgrammar


def file_parser(line_parsers, input_lines, repeat=1):
    res = {}
    line_parsers = line_parsers * repeat
    while input_lines and line_parsers:
        line_parser = line_parsers.pop(0)
        line_parser(input_lines, res)
    if line_parsers:
        raise Exception('Input file insufficient.')
    return res


def create_line_parsers(grammar_lines):
    line_parsers = []
    while grammar_lines:
        line = grammar_lines.pop(0)
        if re.match(SIMPLE_WORDS_RE, line):
            line_parsers.append(simple_words_parser(line.split(' ')))
        elif re.match(OPEN_MULT_RE, line):
            list_name, iterations_varname = re.search(OPEN_MULT_RE, line).group(1,2)
            subgrammar = extract_subgrammar(grammar_lines)
            subparser = create_line_parsers(subgrammar)
            group_parser = lines_group_parser(list_name, iterations_varname, subparser)
            line_parsers.append(group_parser)
    return line_parsers


def create_parser(grammar_filename):
    with open(grammar_filename) as grammar_file:
        cleaned_content = grammar_file.read().split('\n')
        grammar_lines = [line.strip() for line in cleaned_content if line]
        check_lines_format(grammar_lines)
        line_parsers = create_line_parsers(grammar_lines)

    print('parser created. Now parsing input file ...')

    def parser(input_filename):
        with open(input_filename) as input_file:
            input_lines = [line.strip() for line in input_file.read().split('\n') if line]
            return file_parser(line_parsers[:], input_lines)

    return parser


if __name__ == '__main__':
    import sys
    from pprint import pprint

    if len(sys.argv) < 2:
        print ('Please supply an input file')
    elif len(sys.argv) == 2:
        print('No grammar file given, proceeding assuming a "grammar" file exists in the current directory')
        pprint(create_parser('grammar')(sys.argv[1]))
    else:
        pprint(create_parser(sys.argv[2])(sys.argv[1]))
