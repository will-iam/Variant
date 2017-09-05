#include "hydrodynamics.hpp"
#include "IO.hpp"

#include <ios>
#include <iomanip>
#include <iostream>
#include <fstream>
#include <string>

Hydrodynamics::Hydrodynamics():
    Engine() {

}

Hydrodynamics::~Hydrodynamics() {

    delete _domain;
}

int Hydrodynamics::init() {

    // Init domain
    std::vector<std::string> quantityNames;
    quantityNames.push_back("rho");
    quantityNames.push_back("rhou_x");
    quantityNames.push_back("rhou_y");
    quantityNames.push_back("rhoe");

    _domain = new Domain();

    IO::loadDomainInfo(_initpath, *_domain);

    _Nx = _domain->getSizeX();
    _Ny = _domain->getSizeY();
    _dx = _domain->getdx();
    _dy = _domain->getdy();

    // Physical constants
    _gamma = 1.4;

    // Load scheme info and exec options
    // (T, CFL, nSDD, nSDS)
    IO::loadSchemeInfo(_initpath, *this);
    IO::loadExecOptions(_initpath, *_domain);
    IO::loadSDDInfo(_initpath, *_domain);

    // Now that the subdomains info were loaded they can
    // be built
    _domain->buildSubDomainsMPI();

    // Initial time
    _t = 0;

    // Loading initial values
    IO::loadQuantity(_initpath, "rho", *_domain);
    IO::loadQuantity(_initpath, "rhou_x", *_domain);
    IO::loadQuantity(_initpath, "rhou_y", *_domain);
    IO::loadQuantity(_initpath, "rhoe", *_domain);

    // Loading boundary conditions on \rho
    IO::loadBoundaryConditions(_initpath, *_domain);

    // The first dt has to be computed 
    // and the first umax searched manually
    SDDistributed& sdd = _domain->getSDD();

    const Quantity<real>& rho = *(sdd.getQuantity("rho"));
    const Quantity<real>& rhou_x = *(sdd.getQuantity("rhou_x"));
    const Quantity<real>& rhou_y = *(sdd.getQuantity("rhou_y"));
    const Quantity<real>& rhoe = *(sdd.getQuantity("rhoe"));

    unsigned int nSDS = _domain->getNumberSDS();
    _SDS_uxmax.resize(nSDS);
    _SDS_uymax.resize(nSDS);
    std::fill(_SDS_uxmax.begin(), _SDS_uxmax.end(), 0);
    std::fill(_SDS_uymax.begin(), _SDS_uymax.end(), 0);

    for (const auto& sds: sdd.getSDS()) {
        for (std::pair<int, int> coords: sds) {

            int i = coords.first;
            int j = coords.second;

            if (rho.get(0, i, j) != 0) {
                _SDS_uxmax[sds.getId()] = std::max(_SDS_uxmax[sds.getId()], std::abs(rhou_x.get(1, i, j) / rho.get(0, i, j)) + std::abs(sqrt(_gamma * (_gamma - 1) * rhoe.get(0, i, j) / rho.get(0, i, j))));
                _SDS_uymax[sds.getId()] = std::max(_SDS_uymax[sds.getId()], std::abs(rhou_y.get(1, i, j) / rho.get(0, i, j)) + std::abs(sqrt(_gamma * (_gamma - 1) * rhoe.get(0, i, j) / rho.get(0, i, j))));
            }
        }
    }

    // Init tasks pool
    _domain->buildThreads();
    _domain->addEquation("advection", std::bind(&Hydrodynamics::advection, this,
                                   std::placeholders::_1, std::placeholders::_2));
    _domain->addEquation("source", std::bind(&Hydrodynamics::source, this,
                                   std::placeholders::_1, std::placeholders::_2));

    return 0;
}

int Hydrodynamics::start() {

    int i = 0;
    _nIterations = 0;
    while (_t < _T) {
       
        ++_nIterations;

        if (_MPI_rank == 0 && _t / _T * 10.0 >= i) {
            std::cout << "Done " <<  _t / _T * 100.0 << "%" <<  std::endl;
            i = int(_t / _T * 10.0) + 1;
        }


        // Update speed parameters in order to compute dt
        updateDomainUxmax();
        updateDomainUymax();
        std::fill(_SDS_uxmax.begin(), _SDS_uxmax.end(), 0);
        std::fill(_SDS_uymax.begin(), _SDS_uymax.end(), 0);

        // Compute next dt
        computeDT();

        // Synchronize overlap cells: requires communication
        _domain->updateOverlapCells();
        _domain->updateBoundaryCells("rho");
        _domain->updateBoundaryCells("rhou_x", true);
        _domain->updateBoundaryCells("rhou_y", true);
        _domain->updateBoundaryCells("rhoe");

        // Start works and wait for ending
        _domain->execEquation("advection");
        _domain->switchQuantityPrevNext("rho");
        _domain->switchQuantityPrevNext("rhou_x");
        _domain->switchQuantityPrevNext("rhou_y");
        _domain->switchQuantityPrevNext("rhoe");

        // Resynchronize ghost cells for rho quantity before calling next step
        _domain->updateOverlapCells();
        _domain->updateBoundaryCells("rho");
        _domain->updateBoundaryCells("rhou_x", true);
        _domain->updateBoundaryCells("rhou_y", true);
        _domain->updateBoundaryCells("rhoe");

        _domain->execEquation("source");
        _domain->switchQuantityPrevNext("rhou_x");
        _domain->switchQuantityPrevNext("rhou_y");
        _domain->switchQuantityPrevNext("rhoe");

        _t += _dt;
        //getchar();

    }

    // Done
    //_domain->printState("rho");

    return 0;
}

int Hydrodynamics::finalize() {

    writeState();
    return 0;
}

void Hydrodynamics::computeDT() {

    // Updating according to CFL and max velocity
    _dt = _CFL / (_Domain_uxmax / _dx + _Domain_uymax / _dy);
    // So that the final T is reached
    _dt = std::min(_dt, _T - _t);
}

void Hydrodynamics::advection(const SDShared& sds,
        std::map< std::string, Quantity<real>* > quantityMap) {

    Quantity<real>& rho = *quantityMap["rho"];
    Quantity<real>& rhou_x = *quantityMap["rhou_x"];
    Quantity<real>& rhou_y = *quantityMap["rhou_y"];
    Quantity<real>& rhoe = *quantityMap["rhoe"];

    for (auto coords: sds) {

        int i = coords.first;
        int j = coords.second;

        // Computing velocity on nodes
        real uxCellLeft = (rho.get(0, i - 1, j) == 0) ? 0 :
            rhou_x.get(0, i - 1, j) / rho.get(0, i - 1, j);
        real uxCellCenter = (rho.get(0, i, j) == 0) ? 0 :
            rhou_x.get(0, i, j) / rho.get(0, i, j);
        real uxCellRight = (rho.get(0, i + 1, j) == 0) ? 0 :
            rhou_x.get(0, i + 1, j) / rho.get(0, i + 1, j);
        real uLeft = 0.5 * (uxCellLeft + uxCellCenter);
        real uRight = 0.5 * (uxCellRight + uxCellCenter);

        real uyCellBottom = (rho.get(0, i, j - 1) == 0) ? 0 :
            rhou_y.get(0, i , j - 1) / rho.get(0, i, j - 1);
        real uyCellCenter = (rho.get(0, i, j) == 0) ? 0 :
            rhou_y.get(0, i, j) / rho.get(0, i, j);
        real uyCellTop = (rho.get(0, i, j + 1) == 0) ? 0 :
            rhou_y.get(0, i, j + 1) / rho.get(0, i, j + 1);
        real uBottom = 0.5 * (uyCellBottom + uyCellCenter);
        real uTop = 0.5 * (uyCellTop + uyCellCenter);

        /*
        assert(i != 0 || uLeft == 0);
        assert(j != 0 || uBottom == 0);
        assert(i != _Nx - 1 || uRight == 0);
        assert(j != _Ny - 1 || uTop == 0);
        */

        // Computing fluxes for all three quantities
        real rho_fluxLeft = uLeft * ((uLeft > 0) ? rho.get(0, i - 1, j)
                : rho.get(0, i, j));
        real rho_fluxRight = uRight * ((uRight < 0) ? rho.get(0, i + 1, j)
                : rho.get(0, i, j));
        real rho_fluxBottom = uBottom * ((uBottom > 0) ? rho.get(0, i, j - 1) :
                rho.get(0, i, j));
        real rho_fluxTop = uTop * ((uTop < 0) ? rho.get(0, i, j + 1) :
                rho.get(0, i, j));

        real rhou_x_fluxLeft = uLeft * ((uLeft > 0) ? rhou_x.get(0, i - 1, j)
                : rhou_x.get(0, i, j));
        real rhou_x_fluxRight = uRight * ((uRight < 0) ? rhou_x.get(0, i + 1, j)
                : rhou_x.get(0, i, j));
        real rhou_x_fluxBottom = uBottom * ((uBottom > 0) ? rhou_x.get(0, i, j - 1) :
                rhou_x.get(0, i, j));
        real rhou_x_fluxTop = uTop * ((uTop < 0) ? rhou_x.get(0, i, j + 1) :
                rhou_x.get(0, i, j));

        real rhou_y_fluxLeft = uLeft * ((uLeft > 0) ? rhou_y.get(0, i - 1, j)
                : rhou_y.get(0, i, j));
        real rhou_y_fluxRight = uRight * ((uRight < 0) ? rhou_y.get(0, i + 1, j)
                : rhou_y.get(0, i, j));
        real rhou_y_fluxBottom = uBottom * ((uBottom > 0) ? rhou_y.get(0, i, j - 1) :
                rhou_y.get(0, i, j));
        real rhou_y_fluxTop = uTop * ((uTop < 0) ? rhou_y.get(0, i, j + 1) :
                rhou_y.get(0, i, j));

        real rhoe_fluxLeft = uLeft * ((uLeft > 0) ? rhoe.get(0, i - 1, j)
                : rhoe.get(0, i, j));
        real rhoe_fluxRight = uRight * ((uRight < 0) ? rhoe.get(0, i + 1, j)
                : rhoe.get(0, i, j));
        real rhoe_fluxBottom = uBottom * ((uBottom > 0) ? rhoe.get(0, i, j - 1) :
                rhoe.get(0, i, j));
        real rhoe_fluxTop = uTop * ((uTop < 0) ? rhoe.get(0, i, j + 1) :
                rhoe.get(0, i, j));

        //std::cout << "Flux differences " << rho_fluxRight - rho_fluxLeft << " ; " << rho_fluxTop - rho_fluxBottom << std::endl;
        //std::cout << "Speeds on centers " << uxCellCenter << " " << uyCellCenter << std::endl;

        rho.set(rho.get(0, i, j)
                - _dt * ((rho_fluxRight - rho_fluxLeft) / _dx + (rho_fluxTop - rho_fluxBottom) / _dy),
                1, i, j); 
        rhou_x.set(rhou_x.get(0, i, j)
                - _dt * ((rhou_x_fluxRight - rhou_x_fluxLeft) / _dx + (rhou_x_fluxTop - rhou_x_fluxBottom) / _dy),
                1, i, j);
        rhou_y.set(rhou_y.get(0, i, j)
                - _dt * ((rhou_y_fluxRight - rhou_y_fluxLeft) / _dx + (rhou_y_fluxTop - rhou_y_fluxBottom) / _dy),
                1, i, j);
        rhoe.set(rhoe.get(0, i, j)
                - _dt * ((rhoe_fluxRight - rhoe_fluxLeft) / _dx + (rhoe_fluxTop - rhoe_fluxBottom) / _dy),
                1, i, j);
        /*
        std::cout << i << " ; " << j << std::endl;
        std::cout << "Values of rho " << rho.get(1, i, j) << std::endl;
        std::cout << "Values of rhou_x " << rhou_x.get(1, i, j) << std::endl;
        std::cout << "Values of rhou_y " << rhou_x.get(1, i, j) << std::endl;
    */
    }
}

void Hydrodynamics::source(const SDShared& sds,
        std::map< std::string, Quantity<real>* > quantityMap) {

    Quantity<real>& rho = *quantityMap["rho"];
    Quantity<real>& rhou_x = *quantityMap["rhou_x"];
    Quantity<real>& rhou_y = *quantityMap["rhou_y"];
    Quantity<real>& rhoe = *quantityMap["rhoe"];

    for (auto coords: sds) {

        int i = coords.first;
        int j = coords.second;

        // Quantity of motion source term
        real PLeft = (_gamma - 1) * rhoe.get(0, i - 1, j);
        real PRight = (_gamma - 1) * rhoe.get(0, i + 1, j);
        real PBottom = (_gamma - 1) * rhoe.get(0, i, j - 1);
        real PTop = (_gamma - 1) * rhoe.get(0, i, j + 1);
        
        rhou_x.set(rhou_x.get(0, i, j)
                - _dt * (PRight - PLeft) / (2 * _dx),
                1, i, j);
        rhou_y.set(rhou_y.get(0, i, j)
                - _dt * (PTop - PBottom) / (2 * _dy),
                1, i, j);

        // Energy source term
        real PCenter = (_gamma - 1) * rhoe.get(0, i, j);
        /*
        assert(i != 0 || PLeft == PCenter);
        assert(j != 0 || PBottom == PCenter);
        assert(i != _Nx - 1 || PRight == PCenter);
        assert(j != _Ny - 1 || PTop == PCenter);
        */

        real uxCellLeft = (rho.get(0, i - 1, j) == 0) ? 0 :
            rhou_x.get(0, i - 1, j) / rho.get(0, i - 1, j);
        real uxCellRight = (rho.get(0, i + 1, j) == 0) ? 0 :
            rhou_x.get(0, i + 1, j) / rho.get(0, i + 1, j);

        real uyCellBottom = (rho.get(0, i, j - 1) == 0) ? 0 :
            rhou_y.get(0, i , j - 1) / rho.get(0, i, j - 1);
        real uyCellTop = (rho.get(0, i, j + 1) == 0) ? 0 :
            rhou_y.get(0, i, j + 1) / rho.get(0, i, j + 1);

        rhoe.set(rhoe.get(0, i, j)
                - _dt * PCenter * ((uxCellRight - uxCellLeft) / (2 * _dx)
                                 + (uyCellTop - uyCellBottom) / (2 * _dy)),
                1, i, j);
        
        // Updating umax
        if (rho.get(0, i, j) != 0) {
            _SDS_uxmax[sds.getId()] = std::max(_SDS_uxmax[sds.getId()], std::abs(rhou_x.get(1, i, j) / rho.get(0, i, j)) + std::abs(sqrt(_gamma * (_gamma - 1) * rhoe.get(0, i, j) / rho.get(0, i, j))));
            _SDS_uymax[sds.getId()] = std::max(_SDS_uymax[sds.getId()], std::abs(rhou_y.get(1, i, j) / rho.get(0, i, j)) + std::abs(sqrt(_gamma * (_gamma - 1) * rhoe.get(0, i, j) / rho.get(0, i, j))));
        }
    }
}


void Hydrodynamics::writeState() {

    writeState(_outputpath);
}

void Hydrodynamics::writeState(std::string directory) {

    IO::writeQuantity(directory, "rho", *_domain);
    IO::writeQuantity(directory, "rhou_x", *_domain);
    IO::writeQuantity(directory, "rhou_y", *_domain);
    IO::writeQuantity(directory, "rhoe", *_domain);
    IO::writeVariantInfo(directory, *_domain);
}

void Hydrodynamics::boundaryConditionsOnSpeed() {

    _domain->updateOverlapCells("rhou_x");
    _domain->updateOverlapCells("rhou_y");

    // For the case of the speed, we change the Neumann cells
    // into their opposite
    _domain->updateBoundaryCells("rhou_x", true);
    _domain->updateBoundaryCells("rhou_y", true);
}

