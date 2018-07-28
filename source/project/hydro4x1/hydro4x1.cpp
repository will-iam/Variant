#include "hydro4x1.hpp"
#include "IO.hpp"

#include <ios>
#include <iomanip>
#include <iostream>
#include <fstream>
#include <string>

Hydro4x1::Hydro4x1():
    Engine() {

}

Hydro4x1::~Hydro4x1() {

    delete _domain;
}

int Hydro4x1::init() {

    // Init domain
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

    // Now that the subdomains info were loaded they can be built
    _domain->buildSubDomainsMPI(4, 1);

    // build SDS in each SDD.
    _domain->buildThreads();

    // Initial time
    _t = 0;

    // Loading initial values
    IO::loadQuantity(_initpath, "rho", *_domain);
    IO::loadQuantity(_initpath, "rhou_x", *_domain);
    IO::loadQuantity(_initpath, "rhou_y", *_domain);
    IO::loadQuantity(_initpath, "rhoe", *_domain);

    // Loading boundary conditions on \rho
    IO::loadBoundaryConditions(_initpath, *_domain);

    // Build communication maps between sdds (overlap and boundary).
    _domain->buildCommunicationMap();

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

            if (rho.get(0, i, j) != 0.) {
                _SDS_uxmax[sds.getId()] = std::max(_SDS_uxmax[sds.getId()], std::abs(rhou_x.get(1, i, j) / rho.get(0, i, j)) + std::abs(sqrt(_gamma * (_gamma - 1) * rhoe.get(0, i, j) / rho.get(0, i, j))));
                _SDS_uymax[sds.getId()] = std::max(_SDS_uymax[sds.getId()], std::abs(rhou_y.get(1, i, j) / rho.get(0, i, j)) + std::abs(sqrt(_gamma * (_gamma - 1) * rhoe.get(0, i, j) / rho.get(0, i, j))));
            }
        }
    }

    // Init tasks pool
    _domain->addEquation("advection", std::bind(&Hydro4x1::advection, this,
                                   std::placeholders::_1, std::placeholders::_2));
    _domain->addEquation("source", std::bind(&Hydro4x1::source, this,
                                   std::placeholders::_1, std::placeholders::_2));

    _domain->addEquation("updateBoundary", std::bind(&Hydro4x1::updateBoundary, this,
                                   std::placeholders::_1, std::placeholders::_2));

    return 0;
}

int Hydro4x1::start() {

    int iPrint = 0;
    _nIterations = 0;

    // Initialize first and then put it at the end of the loop,
    // instead of the beginning so the All Reduce is at the end and
    // everybody is synchronized when the time measures the end of the iteration.
    updateDomainUxmax();
    updateDomainUymax();

    while (_t < _T) {
        if (_MPI_rank == 0 && _t / _T * 10.0 >= iPrint) {
            iPrint = int(_t / _T * 10.0) + 1;
            std::cout << "[0] - Computation done: " <<  _t / _T * 100.0 << "%, time: ";
            _timerIteration.reportTotal();
        }
        _timerIteration.begin();
        _timerComputation.begin();

        ++_nIterations;

        // Compute next dt
        computeDT();

        // ----------------------------------------------------------------------
        // Synchronize overlap cells: requires communication
   	    _timerComputation.end();
        _domain->updateOverlapCells();
   	    _timerComputation.begin();
        // ----------------------------------------------------------------------

        // update BoundaryCells
        _domain->execEquation("updateBoundary");

        // Start works on this equation
        _domain->execEquation("advection");
        _domain->switchQuantityPrevNext("rho");
        _domain->switchQuantityPrevNext("rhou_x");
        _domain->switchQuantityPrevNext("rhou_y");
        _domain->switchQuantityPrevNext("rhoe");

        // ----------------------------------------------------------------------
        // Resynchronize overlap cells for rho quantity before calling next step
   	    _timerComputation.end();
        _domain->updateOverlapCells();
   	    _timerComputation.begin();

        // ----------------------------------------------------------------------
        // update BoundaryCells
        _domain->execEquation("updateBoundary");

        // Start works on this equation
        _domain->execEquation("source");
        _domain->switchQuantityPrevNext("rhou_x");
        _domain->switchQuantityPrevNext("rhou_y");
        _domain->switchQuantityPrevNext("rhoe");

        _t += _dt;
   	    _timerComputation.end();

        // Update speed parameters in order to compute dt
        updateDomainUxmax();
        updateDomainUymax();

        _timerIteration.end();
    }

    return 0;
}

int Hydro4x1::finalize() {
    writeState();
    return 0;
}

void Hydro4x1::computeDT() {
    // Updating according to CFL and max velocity
    _dt = _CFL / (_Domain_uxmax / _dx + _Domain_uymax / _dy);

    // So that the final T is reached
    _dt = std::min(_dt, _T - _t);
}

void Hydro4x1::advection(const SDShared& sds, const std::map< std::string, Quantity<real>* >& quantityMap) {

    Quantity<real>& rho = *quantityMap.at("rho");
    Quantity<real>& rhou_x = *quantityMap.at("rhou_x");
    Quantity<real>& rhou_y = *quantityMap.at("rhou_y");
    Quantity<real>& rhoe = *quantityMap.at("rhoe");

    for (const auto& coords: sds) {

        const int i = coords.first;
        const int j = coords.second;
        
        // Get values from quantity.
        size_t k_bottom = sds.convert(i, j - 1);
        size_t k_top = sds.convert(i, j + 1);
        size_t k_center = sds.convert(i, j);
        size_t k_left(k_center - 1);
        size_t k_right(k_center + 1);

        real rho_left = rho.get0(k_left);
        real rho_center = rho.get0(k_center);
        real rho_right = rho.get0(k_right);
        real rho_top = rho.get0(k_top);
        real rho_bottom = rho.get0(k_bottom);

        real rhou_x_left = rhou_x.get0(k_left);
        real rhou_x_center = rhou_x.get0(k_center);
        real rhou_x_right = rhou_x.get0(k_right);
        real rhou_x_top = rhou_x.get0(k_top);
        real rhou_x_bottom = rhou_x.get0(k_bottom);

        real rhou_y_left = rhou_y.get0(k_left);
        real rhou_y_center = rhou_y.get0(k_center);
        real rhou_y_right = rhou_y.get0(k_right);
        real rhou_y_top = rhou_y.get0(k_top);
        real rhou_y_bottom = rhou_y.get0(k_bottom);

        real rhoe_left = rhoe.get0(k_left);
        real rhoe_center = rhoe.get0(k_center);
        real rhoe_right = rhoe.get0(k_right);
        real rhoe_top = rhoe.get0(k_top);
        real rhoe_bottom = rhoe.get0(k_bottom);

        // Computing velocity on nodes
        real uxCellLeft = (rho_left == 0.) ? 0. : rhou_x_left / rho_left;
        real uxCellCenter = (rho_center == 0.) ? 0. : rhou_x_center / rho_center;
        real uxCellRight = (rho_right == 0.) ? 0. : rhou_x_right / rho_right;
        real uLeft = 0.5 * (uxCellLeft + uxCellCenter);
        real uRight = 0.5 * (uxCellRight + uxCellCenter);

        real uyCellBottom = (rho_bottom == 0.) ? 0. : rhou_y_bottom / rho_bottom;
        real uyCellCenter = (rho_center == 0.) ? 0. : rhou_y_center / rho_center;
        real uyCellTop = (rho_top == 0.) ? 0. : rhou_y_top / rho_top;
        real uBottom = 0.5 * (uyCellBottom + uyCellCenter);
        real uTop = 0.5 * (uyCellTop + uyCellCenter);

        // Computing fluxes for all three quantities
        real rho_fluxLeft = uLeft * ((uLeft > 0.) ? rho_left : rho_center);
        real rho_fluxRight = uRight * ((uRight < 0.) ? rho_right : rho_center);
        real rho_fluxBottom = uBottom * ((uBottom > 0.) ? rho_bottom : rho_center);
        real rho_fluxTop = uTop * ((uTop < 0.) ? rho_top : rho_center);

        real rhou_x_fluxLeft = uLeft * ((uLeft > 0.) ? rhou_x_left : rhou_x_center);
        real rhou_x_fluxRight = uRight * ((uRight < 0.) ? rhou_x_right : rhou_x_center);
        real rhou_x_fluxBottom = uBottom * ((uBottom > 0.) ? rhou_x_bottom : rhou_x_center);
        real rhou_x_fluxTop = uTop * ((uTop < 0.) ? rhou_x_top : rhou_x_center);

        real rhou_y_fluxLeft = uLeft * ((uLeft > 0.) ? rhou_y_left : rhou_y_center);
        real rhou_y_fluxRight = uRight * ((uRight < 0.) ? rhou_y_right : rhou_y_center);
        real rhou_y_fluxBottom = uBottom * ((uBottom > 0.) ? rhou_y_bottom : rhou_y_center);
        real rhou_y_fluxTop = uTop * ((uTop < 0.) ? rhou_y_top : rhou_y_center);

        real rhoe_fluxLeft = uLeft * ((uLeft > 0.) ? rhoe_left : rhoe_center);
        real rhoe_fluxRight = uRight * ((uRight < 0.) ? rhoe_right : rhoe_center);
        real rhoe_fluxBottom = uBottom * ((uBottom > 0.) ? rhoe_bottom : rhoe_center);
        real rhoe_fluxTop = uTop * ((uTop < 0.) ? rhoe_top : rhoe_center);

        // std::cout << "Flux differences " << rho_fluxRight - rho_fluxLeft << " ; " << rho_fluxTop - rho_fluxBottom << std::endl;
        // std::cout << "Speeds on centers " << uxCellCenter << " " << uyCellCenter << std::endl;

        rho.set1(rho_center - _dt * ((rho_fluxRight - rho_fluxLeft) / _dx + (rho_fluxTop - rho_fluxBottom) / _dy), k_center);
        rhou_x.set1(rhou_x_center - _dt * ((rhou_x_fluxRight - rhou_x_fluxLeft) / _dx + (rhou_x_fluxTop - rhou_x_fluxBottom) / _dy), k_center);
        rhou_y.set1(rhou_y_center - _dt * ((rhou_y_fluxRight - rhou_y_fluxLeft) / _dx + (rhou_y_fluxTop - rhou_y_fluxBottom) / _dy), k_center);
        rhoe.set1(rhoe_center - _dt * ((rhoe_fluxRight - rhoe_fluxLeft) / _dx + (rhoe_fluxTop - rhoe_fluxBottom) / _dy), k_center);

        /*
        std::cout << i << " ; " << j << std::endl;
        std::cout << "Values of rho " << rho.get(1, i, j) << std::endl;
        std::cout << "Values of rhou_x " << rhou_x.get(1, i, j) << std::endl;
        std::cout << "Values of rhou_y " << rhou_x.get(1, i, j) << std::endl;
    */
    }
}

void Hydro4x1::source(const SDShared& sds, const std::map< std::string, Quantity<real>*>& quantityMap) {

    Quantity<real>& rho = *quantityMap.at("rho");
    Quantity<real>& rhou_x = *quantityMap.at("rhou_x");
    Quantity<real>& rhou_y = *quantityMap.at("rhou_y");
    Quantity<real>& rhoe = *quantityMap.at("rhoe");

    real sdsUxMax(0.), sdsUyMax(0.);
    for (const auto& coords: sds) {

        const int i = coords.first;
        const int j = coords.second;

        // Get values from quantity.
        size_t k_bottom = sds.convert(i, j - 1);
        size_t k_top = sds.convert(i, j + 1);
        size_t k_center = sds.convert(i, j);
        size_t k_left(k_center - 1);
        size_t k_right(k_center + 1);

        real rho_left = rho.get0(k_left);
        real rho_center = rho.get0(k_center);
        real rho_right = rho.get0(k_right);
        real rho_bottom = rho.get0(k_bottom);
        real rho_top = rho.get0(k_top);

        real rhoe_center = rhoe.get0(k_center);

        // Quantity of motion source term
        real PLeft = (_gamma - 1) * rhoe.get0(k_left);
        real PRight = (_gamma - 1) * rhoe.get0(k_right);
        real PBottom = (_gamma - 1) * rhoe.get0(k_bottom);
        real PTop = (_gamma - 1) * rhoe.get0(k_top);

        real rhou_x1 = rhou_x.get(0, i, j) - _dt * (PRight - PLeft) / (2 * _dx);
        rhou_x.set1(rhou_x1, k_center);

        real rhou_y1 = rhou_y.get(0, i, j) - _dt * (PTop - PBottom) / (2 * _dy);
        rhou_y.set1(rhou_y1, k_center);

        // Energy source term
        real PCenter = (_gamma - 1) * rhoe_center;

        real uxCellLeft = (rho_left == 0.) ? 0. : rhou_x.get0(k_left) / rho_left;

        real uxCellRight = (rho_right == 0.) ? 0. : rhou_x.get0(k_right) / rho_right;

        real uyCellBottom = (rho_bottom == 0.) ? 0. : rhou_y.get0(k_bottom) / rho_bottom;

        real uyCellTop = (rho_top == 0.) ? 0. : rhou_y.get0(k_top) / rho_top;

        rhoe.set1(rhoe_center - _dt * PCenter * ((uxCellRight - uxCellLeft) / (2 * _dx) + (uyCellTop - uyCellBottom) / (2 * _dy)), k_center);

        // Updating umax and uymax
        if (rho_center != 0.) {
            // real plus = std::abs(sqrt(_gamma * PCenter / rho0ij));
            real plus = std::abs(sqrt(_gamma * (_gamma - 1) * rhoe_center / rho_center));
            real uxMax = std::abs(rhou_x1 / rho_center) + plus;
            if (sdsUxMax < uxMax)
                sdsUxMax = uxMax;

            real uyMax = std::abs(rhou_y1 / rho_center) + plus;
            if (sdsUyMax < uyMax)
                sdsUyMax = uyMax;
        }
    }

    _SDS_uxmax[sds.getId()] = sdsUxMax;
    _SDS_uymax[sds.getId()] = sdsUyMax;
}

void Hydro4x1::updateBoundary(const SDShared& sds, const std::map< std::string, Quantity<real>*>& quantityMap) {
    // update BoundaryCells
    sds.updateBoundaryCells(quantityMap.at("rho"));
    sds.updateBoundaryCells(quantityMap.at("rhou_x"), true);
    sds.updateBoundaryCells(quantityMap.at("rhou_y"), true);
    sds.updateBoundaryCells(quantityMap.at("rhoe"));
}

void Hydro4x1::writeState() {

    writeState(_outputpath);
}

void Hydro4x1::writeState(std::string directory) {

    if (_dryFlag == 0) {
        IO::writeQuantity(directory, "rho", *_domain);
        IO::writeQuantity(directory, "rhou_x", *_domain);
        IO::writeQuantity(directory, "rhou_y", *_domain);
        IO::writeQuantity(directory, "rhoe", *_domain);
    }

    IO::writeVariantInfo(directory, *_domain);
    IO::writeSDDTime(directory, *_domain, "compute", _timerComputation.getSteadyTimeDeque());
    IO::writeSDDTime(directory, *_domain, "iteration", _timerIteration.getSteadyTimeDeque());
}
