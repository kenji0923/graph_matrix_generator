#!/usr/bin/env python3

import argparse
import datetime
import glob
import json
import os
import re
import subprocess
import shutil

from pathlib import Path


def get_unique_filename(dir_source, filepath):
    def check_source_file_exists(filename):
        return os.path.exists(os.path.join(dir_source, os.path.basename(filename)))

    def get_filename_postfixed(postfix):
        return Path(filepath).stem + postfix + Path(filepath).suffix

    if check_source_file_exists(filepath):
        index = 0
        while True:
            postfix = '_' + str(index)
            test_filename = get_filename_postfixed(postfix)

            if not check_source_file_exists(test_filename):
                break

            index = index + 1
    else:
        postfix = ''

    return os.path.join(dir_source, get_filename_postfixed(postfix))


def get_and_copy_source_graph(input_file_list, dir_base, dir_source):
    input_files_str = ''
    source_file_dict = {}
    for input_file in input_file_list:
        if not os.path.isfile(input_file):
            continue

        copied_input_filepath = get_unique_filename(dir_source, input_file)
        shutil.copy2(input_file, copied_input_filepath)

        relative_input_filepath = str(Path(copied_input_filepath).relative_to(dir_base))

        input_files_str = input_files_str + '\t\'' + relative_input_filepath + '\'' + ',\n'

        source_file_dict[os.path.basename(relative_input_filepath)] = {
                'original_path': input_file
            }

    if not input_files_str == '':
        input_files_str = input_files_str[0:-1]

    with open(os.path.join(dir_source, 'source_files.json'), 'w') as f_source_file_dict:
        json.dump(source_file_dict, f_source_file_dict, indent=4)

    return input_files_str


def backup_existing(args):
    dir_write = args.output

    if os.path.exists(dir_write):
        time_stamp = datetime.datetime.now()
        backup_dir = os.path.join(dir_write, 'backup', time_stamp.strftime('%Y%m%d_%H%M%S'))

        tex_files = glob.glob(os.path.join(dir_write, '*.tex'))
        for tex_file in tex_files:
            os.makedirs(backup_dir, exist_ok=True)
            shutil.move(tex_file, os.path.join(backup_dir, os.path.basename(tex_file)))

        source_dir = os.path.join(dir_write, 'source')
        if os.path.exists(source_dir):
            os.makedirs(backup_dir, exist_ok=True)
            shutil.move(source_dir, os.path.join(backup_dir, 'source'))

    return


def output_graph_matrix(args):
    if os.path.islink(__file__):
        script_path = os.path.realpath(__file__)
    else:
        script_path = __file__

    template_filepath = os.path.join(
            Path(script_path).parent,
            'template',
            'template.tex'
        )

    with open(template_filepath, 'r') as f_template:
        dir_write = args.output
        dir_source = os.path.join(dir_write, 'source')

        os.makedirs(dir_source, exist_ok=True)

        template_data = f_template.read()

        input_files_str = get_and_copy_source_graph(args.input, dir_write, dir_source)

        template_data = re.sub('{{GRAPH_LIST}}', input_files_str, template_data)

        write_tex_filename = args.output + '.tex'
        write_tex_filepath = os.path.join(dir_write, write_tex_filename)
        with open(write_tex_filepath, 'w') as f_write:
            f_write.write(template_data)

    subprocess.run(['latexmk', '-pdflua', write_tex_filename], cwd=dir_write)
    subprocess.run(['latexmk', '-pdflua', '-c', write_tex_filename], cwd=dir_write)

    aux_files = []

    for aux_filename in aux_files:
        aux_filepath = os.path.join(dir_write, aux_filename)
        if os.path.exists(aux_filepath):
            os.remove(aux_filepath)

    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input", nargs='+', help='input image files')

    parser.add_argument(
            "-o",
            "--output",
            default='graph_matrix',
            help='name of output files'
        )

    args = parser.parse_args()

    backup_existing(args)

    output_graph_matrix(args)
