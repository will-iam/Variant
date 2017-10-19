#!/usr/bin/python
# -*- coding:utf-8 -*-

import __future__
import os
import sys
import subprocess
import io
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import config

class Engine:
    def __init__(self, project_name, build = True, compiler = 'intel',
            mode = 'debug', precision = 'double', std='c++11',
            clean = False):
        if clean:
            self._clean(project_name, compiler, mode, precision, std)
        elif build:
            self.binary_path = self._build(project_name,
                compiler, mode, precision, std)
        else:
            program_file = project_name + '-' + mode + '-' + compiler + '.exec'
            self.binary_path = os.path.join(config.workspace, program_file)

    def _build(self, project_name, compiler, mode, precision, std):
        p = subprocess.Popen(['scons',
            'workspace=' + config.workspace,
            'project=' + project_name,
            'compiler=' + compiler,
            'mode=' + mode,
            'precision=' + precision,
            'std=' + std],
            cwd = os.path.join(config.workspace, 'source'))
        p.wait()
        if p.returncode != 0:
            print("Compilation failed")
            sys.exit(1)
        program_file = project_name + '-' + mode + '-' + compiler + '.exec'
        return os.path.join(config.workspace, program_file)

    def _clean(self, project_name, compiler, mode, precision, std):
        p = subprocess.Popen(['scons',
            'workspace=' + config.workspace,
            'project=' + project_name,
            'compiler=' + compiler,
            'mode=' + mode,
            'precision=' + precision,
            'std=' + std,
            '-c'],
            cwd = os.path.join(config.workspace, 'source'))
        p.wait()

    def run(self, input_path, output_path, mpi_nprocs = 0, ncores = 1, gdb = False, valgrind = False, vtune = False):
        cmd = config.mpi_RUN.split(' ')
        if mpi_nprocs > 0:
            if gdb:
                subprocess.check_call([config.mpi_RUN, '-n', str(mpi_nprocs), '-x',
                    'xterm', '-e', 'gdb', '--args',
                    self.binary_path, '-i', input_path, '-o', output_path])
            elif valgrind:
                subprocess.check_call([config.mpi_RUN, '-n', str(mpi_nprocs), '-x',
                    'valgrind', '--leak-check=yes',
                    '--log-file=valgrind-out.txt',
                    self.binary_path, '-i', input_path, '-o', output_path])
            elif vtune:
                cmd = cmd + ['-n', str(mpi_nprocs), '-x', '-c', str(ncores), 'amplxe-cl', '-r', 'report-vtune', '-collect', 'hotspots', self.binary_path, '-i', input_path, '-o', output_path]
                print(' '.join(cmd))
                subprocess.check_call(cmd)
            else:
                # visible in this process + all children
                #os.environ['SCOREP_EXPERIMENT_DIRECTORY'] = 'weak64.SDD' + str(mpi_nprocs) + '.r1'
                #os.environ['SCOREP_FILTERING_FILE'] = '/ccc/home/cont999/formation/stag26/Variant/filter'
                #os.environ['SCOREP_MEMORY_RECORDING'] = 'true'
                #os.environ['SCOREP_MPI_MEMORY_RECORDING'] = 'true'
                #cmd = cmd + ['-n', str(mpi_nprocs), '-x', '-c', str(ncores), self.binary_path, '-i', input_path, '-o', output_path]
                cmd = cmd + ['-n', str(mpi_nprocs), self.binary_path, '-i', input_path, '-o', output_path]
                print(' '.join(cmd))
                subprocess.check_call(cmd, env=dict(os.environ, SQSUB_VAR="visible in this subprocess"))
        else:
            if gdb:
                subprocess.check_call(['gdb', '--args', self.binary_path, '-i', input_path, '-o', output_path])
            elif valgrind:
                subprocess.check_call(['valgrind', '--leak-check=yes',
                    self.binary_path, '-c', str(nthreads), '-i', input_path, '-o', output_path])
            else:
                subprocess.check_call([self.binary_path, '-i', input_path, '-o', output_path])
