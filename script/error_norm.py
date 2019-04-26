#!/usr/bin/python3
# -*- coding:utf-8 -*-

import __future__
import numpy as np
from script.rio import read_converter_1D, make_sure_path_exists
from timeit import default_timer as timer
import sys
import os


def save(err_path, err):
    make_sure_path_exists(err_path)
    with open(os.path.join(err_path, "error.dat"), 'a+') as f:
#        f.write("%s\t%s\t%s\t%s\n" % (err['N'], err['rho'], err['energy'], err['u']))
        f.write("%s\t%s\t%s\t%s\n" % (err['N'], err['rho'], 0., 0.))

def load(err_path):
    make_sure_path_exists(err_path)
    file_path = os.path.join(err_path, "error.dat")
    if not os.path.isfile(file_path):
        raise ValueError("No file!")

    err_list = []
    with open(file_path, 'r') as f:       
        for line in f.readlines():
            el = line.split()
            err_list.append({'N': float(el[0]), 'rho': float(el[1]), 'energy': float(el[2]), 'u': float(el[3])})
           
    return err_list


def compute(data_path, qty_name_list, solver):
    """
    Compute L^2 error between a solution in path and exact Sod solution 1D.
    """
    uid_to_coords = dict()
    start = timer()
    Nx, Ny, dx, dy = read_converter_1D(data_path, uid_to_coords)
    end = timer()
    print("Time to load coordinates converter of %s elements" % (Nx * Ny), "%s second(s)" % int((end - start)))
        
    # Call solver.
    #in values: ['energy', 'p', 'u', 'rho', 'rho_total', 'x']
    start = timer()
    if solver == 'sod':
        if Nx != 1 and Ny != 1:
            return None
        from sod import solve
        positions, regions, values = solve(left_state=(1, 1, 0), right_state=(0.1, 0.125, 0.),
                        geometry=(0., 1., 0.5), t=0.2, gamma=1.4, npts=Nx)
    if solver == 'sedov':
        from sedov import solve
        x = np.linspace(0., Nx * float(dx) * np.sqrt(2), Nx)
        if Ny==1:
            values = solve(t=1.0, gamma=1.4, xpos=x, ndim=1)
        if Nx and Ny>1:
            values = solve(t=1.0, gamma=1.4, xpos=x, ndim=2)

    if solver == 'noh':
        from noh import solve
        if Nx==1:
            values = solve(t=0.6, gamma=5./3., ndim=1,npts=Ny)
        if Ny==1:
            values = solve(t=0.6, gamma=5./3., ndim=1,npts=Nx)
        if Ny>1:
            values = solve(t=0.6, gamma=5./3., ndim=2,npts=Nx)
    
    
#    values['rho'] = 0*np.ones(Nx)


    end = timer()
    print("Time to compute exact solution of %s elements" % len(values['rho']), "%s second(s)" % int((end - start)))

    result = {'N' : Nx*Ny}
    # Must load rho in any case.
    start = timer()
    rho = np.zeros(Nx)
    counter = 0
    with open(os.path.join(data_path, 'rho.dat'), 'r') as quantity_f:
        for line in quantity_f:
            if counter == Nx:
                break
            
            line_list = line.split(' ')
            pos = int(line_list[0])
            if pos in uid_to_coords:
                coords = uid_to_coords[pos]
                rho[coords[0]] = float(line_list[1])
                counter = counter + 1

    end = timer()
    print("Time to load quantity rho of %s elements" % (Nx * Ny), "%s second(s)" % int((end - start)))
    if (solver == 'sedov' or solver == 'noh') and (Nx>1 and Ny>1):      #2D Sedov or Noh
        result["rho"] = np.linalg.norm((rho - values["rho"]), ord=2) * min(float(dx),float(dy)) * np.sqrt(2)
    else:
        result["rho"] = np.linalg.norm((rho - values["rho"]), ord=2) * min(float(dx),float(dy))


    '''
    q_map = {"rhoE" : "energy", "rhou_x" : "u"}
    for q_name in q_map:
        # Load data
        start = timer()
        data = np.zeros((Nx, Ny))
        read_quantity(data, data_path, uid_to_coords, q_name)

        if Ny == Nx:
            data_uy = np.zeros((Nx, Ny))
            read_quantity(data_uy, data_path, uid_to_coords, "rhou_y")
            q = np.zeros(Nx)
            for i in range(Nx):
                uy = data_uy[i][i] / rho[i]
                ux = data[i][i] / rho[i]
                q[i] = np.sqrt((ux**2. + uy**2.) / 2.)
        else:
            q = data[:,0] / rho

        end = timer()
        print("Time to load quantity", q_name, "of %s elements" % (Nx * Ny), "%s second(s)" % int((end - start)))
        result[q_map[q_name]] = np.linalg.norm((q - values[q_map[q_name]]), ord=2) / Nx
    '''
    return result
