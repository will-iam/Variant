#include "transportUpwind.hpp"
#include "IO.hpp"

#include <ios>
#include <iomanip>
#include <iostream>
#include <fstream>
#include <string>

TransportUpwind::TransportUpwind():
    Engine(), _umax(0) {

}

TransportUpwind::~TransportUpwind() {

    delete _domain;
}

int TransportUpwind::init() {

    // Init domain
    std::vector<std::string> quantityNames;
    quantityNames.push_back("rho");
    quantityNames.push_back("ux");
    quantityNames.push_back("uy");

    _domain = new Domain();

    IO::loadDomainInfo(_initpath, *_domain);

    _Nx = _domain->getSizeX();
    _Ny = _domain->getSizeY();
    _dx = _domain->getdx();
    _dy = _domain->getdy();

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
    IO::loadQuantity(_initpath, "ux", *_domain, true);
    IO::loadQuantity(_initpath, "uy", *_domain, true);

    //_domain->printState("rho");
    //getchar();

    // Loading boundary conditions on \rho
    IO::loadBoundaryConditions(_initpath, *_domain);

    _umax = 1;

    // Setting boundary conditions for speed
    boundaryConditionsOnSpeed();

    // The first dt has to be computed 
    // and the first umax searched manually
    /*
    const SDDistributed& sdd = domain->getSDD();

        const Quantity<real>& ux = *(sdd.getQuantity("ux"));
        const Quantity<real>& uy = *(sdd.getQuantity("uy"));

        for (const auto& sds: sdd->getSDS()) {
            for (std::pair<int, int> coords: sds) {
                _umax = std::max(_umax, std::abs(ux->get(0, coords.first, coords.second)));
                _umax = std::max(_umax, std::abs(uy->get(0, coords.first, coords.second)));
            }
        }
    }
    computeDT();
    */

    // Init tasks pool
    _domain->buildThreads();
    _domain->addEquation(std::bind(&TransportUpwind::massEquation, this,
                                   std::placeholders::_1, std::placeholders::_2));

    return 0;
}

int TransportUpwind::start() {

    while (_t < _T) {

        // Synchronize overlap cells: requires communication
        _domain->updateOverlapCells();

        // Apply (Dirichlet or Neumann) boundary conditions
        _domain->updateBoundaryCells("rho");

        // Compute next dt
        computeDT();

        // Print domain state
        //_domain->printState("rho");
        //getchar();

        // Start works and wait for ending
        _domain->execEquation();

        SDDistributed& sdd = _domain->getSDD();
        // No need to switch u since it is constant in time
        Quantity<real>* rho = sdd.getQuantity("rho");
        rho->switchPrevNext();

        _t += _dt;
        
        //getchar();
    }

    // Done
    //_domain->printState("rho");
    writeState();

    return 0;
}

void TransportUpwind::computeDT() {

    // Updating according to CFL and max velocity
    _dt = _CFL * std::min(_dx, _dy) / std::abs(_umax);
    // So that the final T is reached
    _dt = std::min(_dt, _T - _t);
}

void TransportUpwind::massEquation(const SDShared& sds,
        std::map< std::string, Quantity<real>* > quantityMap) {

    Quantity<real>& rho = *quantityMap["rho"];
    Quantity<real>& ux = *quantityMap["ux"];
    Quantity<real>& uy = *quantityMap["uy"];

    for (auto coords: sds) {

        int i = coords.first;
        int j = coords.second;

        // In order to have a simulation on final time T
        //std::cout << sd.size() << std::endl;
        //getchar();
        //std::cout << "Computing for " << i << "..." << j << std::endl;

        real uLeft = 0.5 * (ux.get(0, i - 1, j) + ux.get(0, i, j));
        real uRight = 0.5 * (ux.get(0, i, j) + ux.get(0, i + 1, j));
        real fluxLeft = uLeft * ((uLeft > 0) ? rho.get(0, i - 1, j) : rho.get(0, i, j));
        real fluxRight = uRight * ((uRight < 0) ? rho.get(0, i + 1, j) : rho.get(0, i, j));

        real uBottom = 0.5 * (uy.get(0, i, j - 1) + uy.get(0, i, j));
        real uTop = 0.5 * (uy.get(0, i, j) + uy.get(0, i, j + 1));
        real fluxBottom = uBottom * ((uBottom > 0) ? rho.get(0, i, j - 1) : rho.get(0, i, j));
        real fluxTop = uTop * ((uTop < 0) ? rho.get(0, i, j + 1) : rho.get(0, i, j));

        rho.set(rho.get(0, i, j)
                - _dt * ((fluxRight - fluxLeft) / _dx + (fluxTop - fluxBottom) / _dy),
                1, i, j); 

        // Updating umax for computation of the next dt
        //_umax = std::max(_umax, std::abs(ux.get(0, i, j)));
        //_umax = std::max(_umax, std::abs(uy.get(0, i, j)));
    }
}

/*
// \partial_t \rho + \div \rho u = 0
void TransportUpwind::massEquation(int i, int j,
        std::map< std::string, Quantity<real>* > quantityMap) {

    Quantity<real>* rho = quantityMap["rho"];
    Quantity<real>* ux = quantityMap["ux"];
    Quantity<real>* uy = quantityMap["uy"];

    // In order to have a simulation on final time T
    //std::cout << sd.size() << std::endl;
    //getchar();
    //std::cout << "Computing for " << i << "..." << j << std::endl;

    real uLeft = 0.5 * (ux->get(0, i - 1, j) + ux->get(0, i, j));
    real uRight = 0.5 * (ux->get(0, i, j) + ux->get(0, i + 1, j));
    real fluxLeft = uLeft * ((uLeft > 0) ? rho->get(0, i - 1, j) : rho->get(0, i, j));
    real fluxRight = uRight * ((uRight < 0) ? rho->get(0, i + 1, j) : rho->get(0, i, j));

    real uBottom = 0.5 * (uy->get(0, i, j - 1) + uy->get(0, i, j));
    real uTop = 0.5 * (uy->get(0, i, j) + uy->get(0, i, j + 1));
    real fluxBottom = uBottom * ((uBottom > 0) ? rho->get(0, i, j - 1) : rho->get(0, i, j));
    real fluxTop = uTop * ((uTop < 0) ? rho->get(0, i, j + 1) : rho->get(0, i, j));

    if (i == 0) {
        std::cout << rho->get(0, i - 1, j) << "..." << rho->get(0, i, j) << std::endl;
        std::cout << ux->get(0, i - 1, j) << "..." << ux->get(0, i, j) << std::endl;
        std::cout << uy->get(0, i - 1, j) << "..." << uy->get(0, i, j) << std::endl << std::endl;
    }

    rho->set(rho->get(0, i, j)
            - _dt * ((fluxRight - fluxLeft) / _dx + (fluxTop - fluxBottom) / _dy),
            1, i, j); 

        // Updating umax for computation of the next dt
        //_umax = std::max(_umax, std::abs(ux->get(0, i, j)));
        //_umax = std::max(_umax, std::abs(uy->get(0, i, j)));
}
*/

void TransportUpwind::writeState() {

    writeState(_outputpath);
}

void TransportUpwind::writeState(std::string directory) {

    IO::writeQuantity(directory, "rho", *_domain);
    //IO::writeBoundaryConditions(directory, "rho", *_domain);
}

void TransportUpwind::boundaryConditionsOnSpeed() {

    _domain->updateOverlapCells("ux");
    _domain->updateOverlapCells("uy");

    // For the case of the speed, we change the Neumann cells
    // into their opposite
    _domain->updateBoundaryCells("ux", true);
    _domain->updateBoundaryCells("uy", true);
}
