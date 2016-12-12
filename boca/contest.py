#  -*- coding: utf-8 -*-
#    @package: contest.py
#     @author: Guilherme N. Ramos (gnramos@unb.br)
#
# Assume-se cada problema está organizado com a seguinte estrutura mínima
# de arquivos (dentro de um diretório que agrupa problemas com
# características similares):
#   - característica
#       `- problema
#            |- input/                (para os casos de teste)
#            `- output/               (para os resultados esperados)

# Caso se deseje sobrescrever alguma configuração específica, basta
# acrescentar o(s) diretório(s) e arquivo(s) relacionados ao diretório do
# problema. Ex:
#   - característica
#       `- problema
#            |- input/
#            |- limits/
#            |    `- java         limites de tempo específicos para java)
#            `- output/


import os
from time import strftime

import utils
from problem import Problem


def copy_BOCA_dirs(src, dest):
    for dirpath, dirnames, filenames in os.walk(src):
        for dir in dirnames:
            if dir in ['compare', 'compile', 'description', 'input',
                       'limits', 'output', 'run', 'tests']:
                    utils.copy(dirpath + '/' + dir,
                               dest + '/' + dir,
                               '-Tr')


def dir_problem_tuple(problem, base_dir='.'):
    for dirpath, dirnames, filenames in os.walk(base_dir):
        if problem in dirnames:
            return Problem(dirpath, problem)
    raise ValueError('Problema \'' + problem + '\'não encontrado.')


def create_info_file(target_dir, problem, pdf_file, basename):
    tex_file = '{}/{}.tex'.format(problem.full_dir(), problem.name)

    with open(tex_file, 'r') as f:
        content = f.read()

    from re import search
    full_name = search(r'\NomeDoProblema{(.*?)}', content)
    if not full_name:
        raise ValueError('Nome completo do problema não definido '
                         'no arquivo \'' + tex_file + '\'.')

    desc_dir = target_dir + '/description'
    desc_file = desc_dir + '/problem.info'
    rpl_dict = {'BASE_NAME': basename,
                'FULL_NAME': full_name.groups(0)[0],
                'DESCRIPTION_FILE': pdf_file}

    utils.makedir(desc_dir)
    utils.fill_template_file('problem.info', desc_file, rpl_dict)

    src = '{}/../{}'.format(target_dir, pdf_file)
    utils.copy(src, desc_dir)


def create_zip_file(letter, problem, target_dir, pdf):
        utils.makedir(target_dir)
        copy_BOCA_dirs('./templates/BocaDefaults', target_dir)     # Padrão
        copy_BOCA_dirs(problem.full_dir(), target_dir)   # Específicos
        create_info_file(target_dir, problem, pdf, letter)
        utils.zip_dir(target_dir, '../{}.zip'.format(letter))


def create_pdf_file(tex_file, base_dir):
    return utils.pdflatex(tex_file, base_dir)


def create_tex_file(contest, problems, date):
    def tex_format(problem):
        return '\t\\Problema[{}]{{{}}}%\n'.format(problem.dir,
                                                  problem.name)

    tex_file = contest + '.tex'
    rpl_dict = {'FILE_NAME': tex_file,
                'FILE_DATE': strftime('%d/%m/%Y')}

    if date:
        rpl_dict['CONTEST_DATE'] = '\data{{{}}}%'.format(date)
    else:
        rpl_dict['\nCONTEST_DATE'] = ''

    tex_problems = ''.join(tex_format(p) for p in problems)
    rpl_dict['INDENTED_PROBLEMS\n'] = tex_problems

    utils.fill_template_file('contest.tex', tex_file, rpl_dict)


def random_problems(dirs):
    def prefix(dirs):
        d = []
        for dir in dirs:
            if not dir.startswith('./problems/'):
                dir = './problems/' + dir
            d.append(dir)
        return d

    def at_least(n, dir):
        for dirpath, dirnames, filenames in os.walk(dir):
            if len(dirnames) < n:
                raise ValueError('Não há {} problemas em \'{}\'.'
                                 ''.format(n, dir))
            return dirnames

    dirs = prefix(dirs)
    problems = {}
    for dir in dirs:
        n = dirs.count(dir)
        problems[dir] = {'n': n, 'problems': at_least(n, dir)}

    from random import sample, shuffle
    random_problems = []
    for key, dict_ in problems.items():
        for p in sample(dict_['problems'], dict_['n']):
            random_problems.append(p)
    shuffle(random_problems)
    return random_problems


def create(problems, contest_tex_file, base_dir='.', date=None):
    contest = contest_tex_file[:-4]
    problems = [dir_problem_tuple(p) for p in problems]

    base_dir += '/' + contest

    utils.makedir(base_dir)
    create_tex_file(contest, problems, date)
    pdf_file = create_pdf_file(contest + '.tex', base_dir)

    letter = 'A'
    for p in problems:
        utils.log('=== {} - {} ==='.format(letter, p.name))
        target_dir = base_dir + '/' + p.name
        create_zip_file(letter, p, target_dir, pdf_file)

        # Ajuste
        letter = chr(ord(letter) + 1)

    utils.remove_subdirs(base_dir)


if __name__ == '__main__':
    def check_tex(value):
        svalue = str(value)
        if not svalue or not svalue.lower().endswith('.tex'):
            raise ValueError('Arquivo \'' + svalue + '\' não é TeX.')

        if os.path.isfile(svalue):
            utils.warning('O arquivo \'' + svalue + '\' será sobrescrito.')
        return svalue

    from argparse import ArgumentParser, RawDescriptionHelpFormatter
    parser = ArgumentParser(add_help=False,
                            description='Geração/manipulação automática de '
                                        'arquivos de um contest para a '
                                        'Maratona (BOCA).',
                            formatter_class=RawDescriptionHelpFormatter,
                            epilog='Exemplos de uso:\n'
                                   '\tpython %(prog)s fizzbuzz easyled\n'
                                   '\tpython %(prog)s -r 0 0 1 2\n\n')

    parser.add_argument('-d', dest='base_dir',
                        type=str, default='/tmp',
                        help='diretório onde criar os arquivos '
                        '(default: %(default)s)')
    parser.add_argument('-date', dest='date', type=str,
                        help='data da prova')
    parser.add_argument('-h', '--help', action='help',
                        help='mostrar esta mensagem e sair')
    parser.add_argument('ids', nargs='+', type=str,
                        help='identificador(es) de problema(s) ou '
                        'diretório(s)')
    parser.add_argument('-q', '--quiet', dest='quiet',
                        action='store_true',
                        help='omitir os resultados do processo')
    parser.add_argument('-r', '--random', dest='random',
                        action='store_true',
                        help='criar uma prova aleatória')
    parser.add_argument('-t', dest='tex_file', type=check_tex,
                        default=strftime('%Y-%m-%d.tex'),
                        help='nome do arquivo TeX '
                        '(default: %(default)s)')

    args = parser.parse_args()
    if args.random:
        problems = random_problems(args.ids)
    else:
        from collections import OrderedDict
        problems = list(OrderedDict.fromkeys(p for p in args.ids))

    create(problems, args.tex_file, args.base_dir, args.date)