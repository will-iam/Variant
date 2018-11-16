#Main Sedov Code Module
#Ported to python from fortran code written by James R Kamm and F X Timmes
#Original Paper and code found at http://cococubed.asu.edu/papers/la-ur-07-2849.pdf

import numpy as np
from globalvars import comvars as gv
from sedov_1d import sed_1d
from sedov_1d_time import sed_1d_time
from matplotlib import pyplot as plt
import pickle

gv.its = 20

# define sedov_main as a function
def sedov_main(geom_in, omega_in, time_in, blast_energy, gamma_in, outfile):
##Explicitly set variables
##Standard Cases
##Spherical constant density should reach r=1 at t=1

                nstep = 12000
                eblast = blast_energy
                gv.xgeom = geom_in
                gv.omega = omega_in
#outputfile = ??????

##input parameters
                time = time_in
                rho0 = 1.225E0
                vel0 = 0.0E0
                ener0 = 0.0E0
                pres0 = 0.0E0
                cs0 = 342.3E0
                gv.gamma = gamma_in

##number of grid points, spatial domain, spatial stepsize.
##to match hydrocode output, use the mid-sell points.
#zpos = array of spatial points
                zlo = 0.0E0
                zhi = 1.2E3
                zstep = (zhi - zlo)/float(nstep)
                zpos = np.arange(zlo + zstep, zhi + zstep, zstep)
                
                den, vel, pres, enertot, enertherm, enerkin, mach, zpos = sed_1d(time, nstep, zpos, eblast, rho0, vel0, ener0, pres0, cs0, gv)

#create final dictionary to pickle
###dictionary is a flexible array
                single_time_output = {'density': den, 'velocity': vel, 'pressure': pres,
                                      'total_energy': enertot, 'thermal_energy': enertherm, 
                                      'kinetic_energy': enerkin, 'mach': mach, 'position': zpos}
                                      
#open file, pickle and dump data, close file                                      
                output = open(outfile, 'wb')
                pickle.dump(single_time_output, output)
                output.close()

#plot outputs vss position
#zmax controls the maximum of the x-axis on the graphs.
                zmax = 1.5 * gv.r2

                plt.plot(zpos, den)
                plt.axis([0,  zmax, 0, max(den)])
                plt.title('Density vs. Position')
                plt.ylabel('Density (kg/m^3)')
                plt.xlabel('Position (m)')
                plt.show()

                plt.plot(zpos, vel)
                plt.axis([0, zmax, 0, max(vel)])
                plt.title('Velocity vs. Position')
                plt.ylabel('Velocity (m/s)')
                plt.xlabel('Position (m)')
                plt.show()

                plt.plot(zpos, pres)
                plt.axis([0,  zmax, 0, max(pres)])
                plt.title('Pressure vs. Position')
                plt.ylabel('Pressure (Pa)')
                plt.xlabel('Position (m)')
                plt.show()
                
                plt.plot(zpos, enertot)
                plt.axis([0,  zmax, 0, max(enertot)])
                plt.title('Total Energy vs. Position')
                plt.ylabel('Energy (J)')
                plt.xlabel('Position (m)')
                plt.show()
                
                plt.plot(zpos, enertherm)
                plt.axis([0,  zmax, 0, max(enertherm)])
                plt.title('Thermal Energy vs. Position')
                plt.ylabel('Energy (J)')
                plt.xlabel('Position (m)')
                plt.show()

                plt.plot(zpos, enerkin)
                plt.axis([0,  zmax, 0, max(enerkin)])
                plt.title('Kinetic Energy vs. Position')
                plt.ylabel('Energy (J)')
                plt.xlabel('Position (m)')
                plt.show()
                
                plt.plot(zpos, mach)
                plt.axis([0,  zmax, 0, max(mach)])
                plt.title('Mach Number vs. Position')
                plt.ylabel('Mach Number')
                plt.xlabel('Position (m)')
                plt.show()
                
#final graph plots scaled density, pressure and velocity one one plot.
                plt.plot(zpos, den/max(den), 'b', label = 'Density') 
                plt.plot(zpos, pres/max(pres), 'g', label = 'Pressure')
                plt.plot(zpos, vel/max(vel), 'r', label = 'Velocity')
                plt.axis([0,  zmax, 0, 1])
                plt.legend(loc = 'upper left')
                plt.title('Scaled Density, Pressure, and Velocity')
                plt.ylabel('Scaled Value (x/max(x))')
                plt.xlabel('Position (m)')
                plt.show()
  

              
#define function to produce results at different points in time instead of sedov_1d
def sedov_main_time(geom_in, omega_in, time_initial, time_final, time_steps, blast_energy, gamma_in, outfile):
##Explicitly set variables
##Standard Cases
##Spherical constant density should reach r=1 at t=1

                nstep = 12000
                eblast = blast_energy
                gv.xgeom = geom_in
                gv.omega = omega_in
#outputfile = ??????

##input parameters
                rho0 = 1.225E0
                vel0 = 0.0E0
                ener0 = 0.0E0
                pres0 = 0.0E0
                cs0 = 342.3E0
                gv.gamma = gamma_in

##number of grid points, spatial domain, spatial stepsize.
##to match hydrocode output, use the mid-sell points.
#zpos = array of spatial points
                zlo = 0.0E0
                zhi = 3.0E2
                zstep = (zhi - zlo)/float(nstep)
                zposition = np.arange(zlo + zstep, zhi + zstep, zstep)
                             
                den_time, vel_time, pres_time, enertot_time, enertherm_time, enerkin_time, mach_time, zpos_time, time = sed_1d_time(time_initial, time_final, time_steps, nstep, zposition, eblast, rho0, vel0, ener0, pres0, cs0, gv)

#create final dictionary to pickle
###dictionary is flexible array
                time_step_output = {'density': den_time, 'velocity': vel_time, 'pressure': pres_time,
                                      'total_energy': enertot_time, 'thermal_energy': enertherm_time, 
                                      'kinetic_energy': enerkin_time, 'mach': mach_time, 
                                      'position': zpos_time, 'time': time}
                                      
#open file, pickle and dump data, close file                                      
                output = open(outfile, 'wb')
                pickle.dump(time_step_output, output)
                output.close()                                      

#zmax controls the maximum of the x-axis on the graphs.
                zmax = 1.5 * gv.r2
# for loops graph a plot for each time step in the final soulution
                for i in range(0, time_steps):
                    plt.plot(zpos_time[i], den_time[i], label = 't=' + str(time[i]))
                plt.xlim([0, zmax])
                plt.title('Density vs. Position')
                plt.ylabel('Density (kg/m^3)')
                plt.xlabel('Position (m)')
                plt.legend(loc = 'upper right', fontsize = 10)
                plt.show()

                for i in range(0, time_steps):
                    plt.plot(zpos_time[i], vel_time[i], label = 't=' + str(time[i]))
                plt.xlim([0, zmax])
                plt.title('Velocity vs. Position')
                plt.ylabel('Velocity (m/s)')
                plt.xlabel('Position (m)')
                plt.legend(loc = 'upper right', fontsize = 10)
                plt.show()

                for i in range(0, time_steps):
                    plt.plot(zpos_time[i], pres_time[i], label = 't=' + str(time[i]))
                plt.xlim([0, zmax])
                plt.title('Pressure vs. Position')
                plt.ylabel('Pressure (Pa)')
                plt.xlabel('Position (m)')
                plt.legend(loc = 'upper right', fontsize = 10)
                plt.show()
                
                for i in range(0, time_steps):
                    plt.plot(zpos_time[i], enertot_time[i], label = 't=' + str(time[i]))
                plt.xlim([0, zmax])
                plt.title('Total Energy vs. Position')
                plt.ylabel('Energy (J)')
                plt.xlabel('Position (m)')
                plt.legend(loc = 'upper right', fontsize = 10)
                plt.show()
                
                for i in range(0, time_steps):
                    plt.plot(zpos_time[i], enertherm_time[i], label = 't=' + str(time[i]))
                plt.xlim([0, zmax])
                plt.title('Thermal Energy vs. Position')
                plt.ylabel('Energy (J)')
                plt.xlabel('Position (m)')
                plt.legend(loc = 'upper right', fontsize = 10)
                plt.show()

                for i in range(0, time_steps):
                    plt.plot(zpos_time[i], enerkin_time[i], label = 't=' + str(time[i]))
                plt.xlim([0, zmax])
                plt.title('Kinetic Energy vs. Position')
                plt.ylabel('Energy (J)')
                plt.xlabel('Position (m)')
                plt.legend(loc = 'upper right', fontsize = 10)
                plt.show()
                
                for i in range(0, time_steps):
                    plt.plot(zpos_time[i], mach_time[i], label = 't=' + str(time[i]))
                plt.xlim([0, zmax])
                plt.title('Mach Number vs. Position')
                plt.ylabel('Mach Number')
                plt.xlabel('Position (m)')
                plt.legend(loc = 'upper right', fontsize = 10)
                plt.show()
                
#final graph plots scaled density, pressure and velocity one one plot.
#                plt.plot(zpos, den/max(den), 'b', label = 'Density') 
#                plt.plot(zpos, pres/max(pres), 'g', label = 'Pressure')
#                plt.plot(zpos, vel/max(vel), 'r', label = 'Velocity')
#                plt.axis([0,  zmax, 0, 1])
#                plt.legend(loc = 'upper left')
#                plt.title('Scaled Density, Pressure, and Velocity')
#                plt.ylabel('Scaled Value (x/max(x))')
#                plt.xlabel('Position (m)')
#                plt.show()

