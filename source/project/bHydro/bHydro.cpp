#include "bHydro.hpp"
#include "IO.hpp"

#include <ios>
#include <iomanip>
#include <iostream>
#include <fstream>
#include <string>
#include <ostream>
#include <vector>
#include <algorithm>

BHydro::BHydro():
    Engine() {
}

BHydro::~BHydro() {

    delete _domain;

    delete[] _mass;
    delete[] _uxl;
    delete[] _uxr;
}

int BHydro::init() {

    // Init domain
    _domain = new Domain();

    IO::loadDomainInfo(_initpath, *_domain);

    _Nx = _domain->getSizeX();
    _Ny = _domain->getSizeY();
    _dx = _domain->getdx();
    _dy = _domain->getdy();

    if (_Nx != _Ny && _Ny != 1)
        exitfail("Work only in one dimension (Ny == 1)");

    // TODO(WW) should work also in two dimensions but only if dx == dy and Nx == Ny

    // Load scheme info and exec options
    // (T, CFL, _gamma, nSDD, nSDS)
    IO::loadSchemeInfo(_initpath, *this);
    IO::loadExecOptions(_initpath, *_domain);
    IO::loadSDDInfo(_initpath, *_domain);

    // Now that the subdomains info were loaded they can be built
    _domain->buildSubDomainsMPI(4, 1);

    // build SDS in each SDD.
    _domain->buildThreads();

    // Show domain info.
    if (_MPI_rank == 0)
        _domain->showInfo();

    // Initial time and error.
    _t = 0.;

    // Loading initial values
    IO::loadQuantity(_initpath, "rho", *_domain);
    IO::loadQuantity(_initpath, "rhou_x", *_domain);
    IO::loadQuantity(_initpath, "rhou_y", *_domain);

    // Loading boundary conditions on \rho and \rhoE
    IO::loadBoundaryConditions(_initpath, *_domain);

    // Build communication maps between sdds (overlap and boundary).
    _domain->buildCommunicationMap();

    unsigned int nSDS = _domain->getNumberSDS();
    _SDS_uxmax.resize(nSDS);
    _SDS_uymax.resize(nSDS);
    std::fill(_SDS_uxmax.begin(), _SDS_uxmax.end(), 0);
    std::fill(_SDS_uymax.begin(), _SDS_uymax.end(), 0);

    // Init tasks pool
    _domain->addEquation("flux", std::bind(&BHydro::flux, this,
                                   std::placeholders::_1, std::placeholders::_2));

    _domain->addEquation("updateBoundary", std::bind(&BHydro::updateBoundary, this,
                                   std::placeholders::_1, std::placeholders::_2));



    // -------------------------------------------------------------------------
    // Compute time step once for all.
    // ux = dx / dt => dt = dx / ux, the speed is 1 which means dt = dx / 1. (m / s)
    // btw we assumed dx == dy.
    if (convolution_support % bunitsize != 0)
        exitfail("We've got a problem here.");

    _bsize = _Nx * convolution_support / bunitsize;
    _dt = _dx / bunitsize;
    _Nt = ceil(_T / _dt);

    #ifndef SEQUENTIAL
    MPI_Bcast(&_Nt, 1, MPI_UNSIGNED, 0, MPI_COMM_WORLD);
    #endif

    initial_condition();

    return 0;
}

void BHydro::initial_condition() {

    _mass = new bline[_bsize];
    _uxr = new bline[_bsize];
    _uxl = new bline[_bsize];

    /*
    const SDDistributed& sdd = _domain->getSDDconst();
    for (unsigned int i = 0; i < sdd.getSizeX(); ++i) {
        for (unsigned int j = 0; j < sdd.getSizeY(); ++j) {
            real r = sdd.getValue("rho", i, j);
            if (r >= 0.5f)
                _mass[i] = 0x00000000000000ff << (8 + rand() % 48);
            else
                _mass[i] = 1UL << (rand() % 62);
        }
    } */

    for (size_t i(0); i < _bsize / 2; ++i)
        _mass[i] = 0x1101010101010100;

    for (size_t i(_bsize / 2); i < _bsize; ++i)
        _mass[i] = 0x0000010000000000;

    for (size_t i(0); i < _bsize / 2; ++i)
        _uxr[i] = _mass[i] & 0xffffffffffffffff;
}

static inline int popCount(unsigned long int x) {
	unsigned long int dummy, dummy2, dummy3;
	asm("          xorq    %0, %0    " "\n\t"
	"          testq   %1, %1    " "\n\t"
	"          jz      2f        " "\n\t"
	"1:        leaq    -1(%1),%2 " "\n\t"
	"          incq    %0        " "\n\t"
	"          andq    %2, %1    " "\n\t"
	"          jnz     1b        " "\n\t"
	"2:                          " "\n\t"
	:   "=&r"(dummy), "=&r"(dummy2), "=&r"(dummy3)
	:   "1"((long) (x))
	:   "cc");
	return (dummy);
}

void BHydro::convolution() {
    std::cout << "Convolution from " << _bsize << " to "<< _Nx << " values." << std::endl;
    SDDistributed& sdd = _domain->getSDD();
    /*
    for (unsigned int i = 0; i < sdd.getSizeX(); ++i) {
        for (unsigned int j = 0; j < sdd.getSizeY(); ++j) {
            double r = (double)popCount(_mass[i]);
            std::cout << "i: " << i << ", r: " << r << std::endl;
            r /= 8.0f;
            std::cout << "i: " << i << ", r: " << r << std::endl;
            sdd.setValue("rho", i, j, r);
        }
    }*/
    for (size_t i(0); i < _bsize; ++i) {
        double r = (double)popCount(_mass[i]);
        //std::cout << "i: " << i << ", r: " << r << std::endl;
        sdd.setValue("rho", i, 0, r);
    }

    std::cout << "end convolution\n";
}

void BHydro::emulate() {
    // emulate quantities
    // Pressure
    // Total Energy
    // Entropy ?
}


int BHydro::start() {

    #ifndef SEQUENTIAL
    // This is to ensure that everybody starts at the same time so you won't get init time
    // of a slow SDD in the loop waiting time of a faster one.
    MPI_Barrier(MPI_COMM_WORLD);
    #endif

    _nIterations = 0;
    while (_nIterations < _Nt) {
        _t = _dt * _nIterations;
        printStatus();

        _timerIteration.begin();
        // ----------------------------------------------------------------------
        _timerComputation.begin();

        ++_nIterations;

        // Compute pressure and speed.
//        _domain->execEquation("updateBoundary");

        // ----------------------------------------------------------------------
        // Communicate the fluxes computed.
//        _timerComputation.end();
//        _domain->updateOverlapCells();
//        _timerComputation.begin();
        // ----------------------------------------------------------------------

        // Start works on this equation
//      _domain->execEquation("flux");

        fluxion();

        //        _domain->switchQuantityPrevNext("mass");
//        _domain->switchQuantityPrevNext("uxr");
//        _domain->switchQuantityPrevNext("uxl");

   	    _timerComputation.end();
        // ----------------------------------------------------------------------
        _timerIteration.end();
    }
    printStatus(true);
    return 0;
}

void BHydro::flux(const SDShared&, const std::map< std::string, Quantity<real>* >&) {
}

void BHydro::fluxion() {

    // Impose left border condition.
    bline previous = 0x0;
    bline immobile(0x0), mobile(0x0);
    for (size_t i(0); i < _bsize; ++i) {
        _mass[i] = (_mass[i] >> 1) | previous;
        previous = (_mass[i] & 1UL) << 63;

        /*
        immobile = _mass[i] & (~_uxr[i]);
        mobile = (_mass[i] & _uxr[i]) >> 1;
        // first bit is lost : => -------------X -> --------------
        // but is copied in the next bline.
        // exception for the last bline.

        _mass[i] = mobile | immobile;
        */
    }

    // Impose right border condition
}

int BHydro::finalize() {
    writeState(_outputpath);
    return 0;
}

void BHydro::updateBoundary(const SDShared& sds, const std::map< std::string, Quantity<real>*>& quantityMap) {
    // update BoundaryCells
    sds.updateBoundaryCells(quantityMap.at("rho"), _t);
    sds.updateBoundaryCells(quantityMap.at("rhou_x"), _t);
    sds.updateBoundaryCells(quantityMap.at("rhou_y"), _t);
}

void BHydro::writeState(std::string directory) {
    convolution();

    if (_dryFlag == 0) {
        IO::writeQuantity(directory, "rho", *_domain);
        IO::writeQuantity(directory, "rhou_x", *_domain);
        IO::writeQuantity(directory, "rhou_y", *_domain);
    }

    IO::writeVariantInfo(directory, *_domain);
    IO::writeSDDTime(directory, *_domain, "compute", _timerComputation.getSteadyTimeDeque());
    IO::writeSDDTime(directory, *_domain, "iteration", _timerIteration.getSteadyTimeDeque());
}
