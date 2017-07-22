#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import os
import sys
import subprocess
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import config

class Engine:
    def __init__(self, project_name, compiler = 'intel',
            mode = 'debug', precision = 'double', std='c++11'):
        self.binary_path = self._build(project_name,
                compiler, mode, precision, std)

    def _build(self, project_name, compiler, mode, precision, std):
        p = subprocess.Popen(['scons',
            'workspace=' + config.workspace,
            'project=' + project_name,
            'compiler=' + compiler,
            'mode=' + mode,
            'precision=' + precision,
            'std=' + std],
            cwd = os.path.join(config.workspace,
                'Variant', 'source'))
        p.wait()
        if p.returncode != 0:
            print("Compilation failed")
            sys.exit(1)
        program_file = project_name + '-' \
                + mode + '-' \
                + compiler
        return os.path.join(config.workspace, 'Variant',
                program_file)

    def run(self, input_path, output_path, mpi_nprocs = 0, gdb = False):
        if mpi_nprocs > 0:
            if gdb:
                subprocess.check_call([config.mpi_RUN, '--tag-output', '-n', str(mpi_nprocs),
                    'xterm', '-e', 'gdb', '--args',
                    self.binary_path, '-i', input_path, '-o', output_path])
            else:
                subprocess.check_call([config.mpi_RUN, '--tag-output', '-n', str(mpi_nprocs),
                    self.binary_path, '-i', input_path, '-o', output_path])
        else:
            if gdb:
                subprocess.check_call(['gdb', '--args', self.binary_path, '-i', input_path, '-o', output_path])
            else:
                subprocess.check_call([self.binary_path, '-i', input_path, '-o', output_path])


