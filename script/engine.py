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
        self._verrou = engineOptionDict['verrou']

        if clean:
            self._clean(self._project_name, self._compiler, self._mode, self._precision, self._std)
        elif build:
            self._build(self._project_name, self._compiler, self._mode, self._precision, self._std)

        program_file = self._project_name + '-' + self._mode + '-' + self._compiler + '-' + self._precision + '.exec'
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

        cmd = list()
        # Command base: mpirun specified in config file.
        if self._compiler == 'mpi':
            mpi_opt = []
            for x in  config.mpi_RUN.split(' '):
                if x == '$mpi_nprocs':
                    mpi_opt.append(str(mpi_nprocs))
                elif x == '$ncores':
                    mpi_opt.append(str(ncores))
                else:
                    mpi_opt.append(x)
            cmd = cmd + mpi_opt

        if self._gdb:
            #cmd = cmd + ['xterm', '-e', 'gdb', '--args']
            #cmd = cmd + ['lldb', '--']
            cmd = cmd + ['gdb', '--args']
        elif self._valgrind:
            #cmd = cmd + ['valgrind', '--leak-check=yes', '--track-origins=yes', '--leak-check=full', '--show-leak-kinds=all', '--log-file=valgrind-out.txt']
            cmd = cmd + ['valgrind', '--leak-check=yes', '--track-origins=yes']
        elif self._vtune:
            cmd = cmd + ['amplxe-cl', '-r', 'vtune-hs', '-collect', 'hotspots']
            #cmd = cmd + ['amplxe-cl', '-r', 'report-vtune-ma', '-collect', 'memory-access']
            #cmd = cmd + ['amplxe-cl', '-r', 'report-vtune-mc', '-collect', 'memory-consumption']
            #cmd = cmd + ['amplxe-cl', '-r', 'report-vtune-ge', '-collect', 'general-exploration']
        elif self._verrou is not None:
            if self._verrou == 'check':
                cmd = ['valgrind', '--tool=none'] + cmd
            else:
                # --rounding-mode=<random|average|upward|downward|toward_zero|farthest|float|nearest>
                #os.environ['VERROU_LIBM_ROUNDING_MODE'] = "nearest"
                
                if self._precision != 'quad': 
                    f = open("list.ex", "w")
                    ldd = subprocess.check_output(["ldd", self._binary_path])
                    for lib in ldd.split():
                        if 'libm' in str(lib) and "/" in str(lib):
                            f.write("*\t%s\n" % lib.decode("utf-8"))
                    
                    ldd = subprocess.check_output(["ldd", "./lib/interlibmath.so"])
                    for lib in ldd.split():
                        if 'libquad' in str(lib) and "/" in str(lib):
                            f.write("*\t%s\n" % lib.decode("utf-8"))

                    f.close()
                
                    os.environ['VERROU_ROUNDING_MODE'] = self._verrou
                    os.environ['LD_PRELOAD'] = "./lib/interlibmath.so"


                cmd = ['valgrind', '--tool=verrou', '--rounding-mode=' + self._verrou, '--demangle=no', '--exclude=list.ex'] + cmd
        '''
        # to add environment variable visible in this process + all children:
        os.environ['SCOREP_EXPERIMENT_DIRECTORY'] = project + 'weak.SDD' + str(mpi_nprocs) + '.r1'
        '''
        
        cmd = cmd + [self._binary_path, '-i', input_path, '-o', output_path] + run_option
        print(' '.join(cmd))
        subprocess.check_call(cmd, env=dict(os.environ, SQSUB_VAR="visible in this subprocess"))
