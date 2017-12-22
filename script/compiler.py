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
    def __init__(self, engineOptionDict, build = True, clean = False):
        self._project_name = engineOptionDict['project_name']
        self._compiler = engineOptionDict['compiler']
        self._mode = engineOptionDict['mode']
        self._precision = engineOptionDict['precision']
        self._std = engineOptionDict['std']
        self._gdb = engineOptionDict['gdb']
        self._vtune = engineOptionDict['vtune']
        self._valgrind = engineOptionDict['valgrind']

        if clean:
            self._clean(self._project_name, self._compiler, self._mode, self._precision, self._std)
        elif build:
            self._binary_path = self._build(self._project_name, self._compiler, self._mode, self._precision, self._std)
        else:
            program_file = self._project_name + '-' + self._mode + '-' + self._compiler + '.exec'
            self._binary_path = os.path.join(config.workspace, program_file)

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

    def run(self, input_path, output_path, nnodes =1, mpi_nprocs = 0, ncores = 1, run_option = []):
        cmd = config.mpi_RUN.split(' ')
        if mpi_nprocs > 0:
            if self._gdb:
                cmd = [config.mpi_RUN, '-n', str(mpi_nprocs), 'xterm', '-e', 'gdb', '--args', self._binary_path, '-i', input_path, '-o', output_path] + run_option
                print(' '.join(cmd))
                subprocess.check_call(cmd)
            elif self._valgrind:
                subprocess.check_call([config.mpi_RUN, '-n', str(mpi_nprocs), '-x',
                    'valgrind', '--leak-check=yes',
                    '--log-file=valgrind-out.txt',
                    self._binary_path, '-i', input_path, '-o', output_path])
            elif self._vtune:
                #project = os.path.basename(self._binary_path).split('-')[0]
                vcmd = ['amplxe-cl', '-r', 'vtune-hs', '-collect', 'hotspots']
                #vcmd = ['amplxe-cl', '-r', 'report-vtune-ma', '-collect', 'memory-access']
                #vcmd = ['amplxe-cl', '-r', 'report-vtune-mc', '-collect', 'memory-consumption']
                #vcmd = ['amplxe-cl', '-r', 'report-vtune-ge', '-collect', 'general-exploration']
                cmd = cmd + ['-n', str(mpi_nprocs), '-x', '-c', str(ncores)] + vcmd + [self._binary_path, '-i', input_path, '-o', output_path] + run_option
                print(' '.join(cmd))
                subprocess.check_call(cmd)
            else:
                '''
                # to add environment variable visible in this process + all children:
                os.environ['SCOREP_EXPERIMENT_DIRECTORY'] = project + 'weak.SDD' + str(mpi_nprocs) + '.r1'
                '''
                cmd = cmd + ['-n', str(mpi_nprocs), self._binary_path, '-i', input_path, '-o', output_path] + run_option
                print(' '.join(cmd))
                subprocess.check_call(cmd, env=dict(os.environ, SQSUB_VAR="visible in this subprocess"))
        else:
            if self._gdb:
                subprocess.check_call(['gdb', '--args', self._binary_path, '-i', input_path, '-o', output_path])
            elif self._valgrind:
                subprocess.check_call(['valgrind', '--leak-check=yes',
                    self._binary_path, '-c', str(nthreads), '-i', input_path, '-o', output_path])
            else:
                subprocess.check_call([self._binary_path, '-i', input_path, '-o', output_path])
