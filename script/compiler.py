#!/usr/local/bin/python3
# -*- coding:utf-8 -*-

import __future__
import os
import sys
import subprocess
import script.rio
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

    def run(self, input_path, output_path, nnodes, mpi_nprocs, ncores, run_option = []):
        if mpi_nprocs == 0:
            print("run failed - not enough mpi process specified.")
            sys.exit(1)

        # Command base: mpirun specified in config file.
        cmd = config.mpi_RUN.split(' ')

        # KnL options
        # '-m', 'block:block'
        # '-m', 'block:cyclic'
        # '-m', 'block:fcyclic'
        #cmd = cmd + ['-N', str(nnodes), '-n', str(mpi_nprocs), '-E', '-O', '-x', '-m', 'block:cyclic', '-c', str(ncores)]
        cmd = cmd + ['-hostfile', 'hostfile', '-n', str(mpi_nprocs)]

        if self._gdb:
            cmd = cmd + ['xterm', '-e', 'gdb', '--args']
        elif self._valgrind:
            cmd = cmd + ['valgrind', '--leak-check=yes', '--log-file=valgrind-out.txt']
        elif self._vtune:
            cmd = cmd + ['amplxe-cl', '-r', 'vtune-hs', '-collect', 'hotspots']
            #cmd = cmd + ['amplxe-cl', '-r', 'report-vtune-ma', '-collect', 'memory-access']
            #cmd = cmd + ['amplxe-cl', '-r', 'report-vtune-mc', '-collect', 'memory-consumption']
            #cmd = cmd + ['amplxe-cl', '-r', 'report-vtune-ge', '-collect', 'general-exploration']

        '''
        # to add environment variable visible in this process + all children:
        os.environ['SCOREP_EXPERIMENT_DIRECTORY'] = project + 'weak.SDD' + str(mpi_nprocs) + '.r1'
        '''

        cmd = cmd + [self._binary_path, '-i', input_path, '-o', output_path] + run_option
        print(' '.join(cmd))
        subprocess.check_call(cmd, env=dict(os.environ, SQSUB_VAR="visible in this subprocess"))
