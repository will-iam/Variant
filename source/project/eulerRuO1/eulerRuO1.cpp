#include "eulerRuO1.hpp"
#include "IO.hpp"

#include <ios>
#include <iomanip>
#include <iostream>
#include <fstream>
#include <string>
#include <ostream>
#include <vector>
#include <algorithm>

EulerRuO1::EulerRuO1():
    Engine() {
}

EulerRuO1::~EulerRuO1() {

    delete _domain;
}

int EulerRuO1::init() {

    // Init domain
    _domain = new Domain();

    IO::loadDomainInfo(_initpath, *_domain);

    _Nx = _domain->getSizeX();
    _Ny = _domain->getSizeY();
    _dx = _domain->getdx();
    _dy = _domain->getdy();

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
    _t = 0.; _t_err = 0.;

    // Initial last.
    _last_dt = -1.0;

    // Initial min.
    _min_dt = std::numeric_limits<real>::max();

    // Loading initial values
    IO::loadQuantity(_initpath, "rho", *_domain);
    IO::loadQuantity(_initpath, "rhou_x", *_domain);
    IO::loadQuantity(_initpath, "rhou_y", *_domain);
    IO::loadQuantity(_initpath, "rhoE", *_domain);
    IO::loadQuantity(_initpath, "pressure", *_domain);
    IO::loadQuantity(_initpath, "sx", *_domain);
    IO::loadQuantity(_initpath, "sy", *_domain);

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
    _domain->addEquation("speed", std::bind(&EulerRuO1::speed, this,
                                   std::placeholders::_1, std::placeholders::_2));

    _domain->addEquation("flux", std::bind(&EulerRuO1::flux, this,
                                   std::placeholders::_1, std::placeholders::_2));
    
    _domain->addEquation("updateBoundary", std::bind(&EulerRuO1::updateBoundary, this,
                                   std::placeholders::_1, std::placeholders::_2));

    _domain->addEquation("updatePressure", std::bind(&EulerRuO1::updatePressure, this,
                                   std::placeholders::_1, std::placeholders::_2));

    return 0;
}


int EulerRuO1::start() {

    #ifndef SEQUENTIAL
    // This is to ensure that everybody starts at the same time so you won't get init time
    // of a slow SDD in the loop waiting time of a faster one.
    MPI_Barrier(MPI_COMM_WORLD);
    #endif

    _nIterations = 0;
    while (_t < _T) {
        printStatus();

        _timerIteration.begin();
        // ----------------------------------------------------------------------
        _timerComputation.begin();

        ++_nIterations;
        
        // Compute pressure and speed.
        _domain->execEquation("updateBoundary");
        
        // ----------------------------------------------------------------------
        // (with a stencil of one, it's not required here because there is no overlap/boundary cell needed in the computation).
   	    /* _timerComputation.end();
        _domain->updateOverlapCells();
        _timerComputation.begin(); */
        // ----------------------------------------------------------------------

        // Compute interface speed and pressure in cell.
        _domain->execEquation("speed");

        // Copy the pressure value in boundary.
        _domain->execEquation("updatePressure");

        // ----------------------------------------------------------------------
        // Communicate the fluxes computed.
   	    _timerComputation.end();
        _domain->updateOverlapCells();
        computeDT();
        _timerComputation.begin();
        // ----------------------------------------------------------------------

        // Start works on this equation
        _domain->execEquation("flux");

        _domain->switchQuantityPrevNext("rho");
        _domain->switchQuantityPrevNext("rhou_x");
        _domain->switchQuantityPrevNext("rhou_y");
        _domain->switchQuantityPrevNext("rhoE");

   	    _timerComputation.end();
        // ----------------------------------------------------------------------
        _timerIteration.end();
    }

    printStatus(true);
    return 0;
}

// Kahan algorithm.
void fastTwoSum(real a, real b, real& c, real& d) {
    if (rabs(b) > rabs(a))
        std::swap(a,b);

    c = a + b;
    const real z = c - a;
    d = b - z;    
}

// Updating according to CFL and max velocity
void EulerRuO1::computeDT() {

    if (_Ny == 1) {
        _SDD_uxmax = *std::max_element(_SDS_uxmax.begin(), _SDS_uxmax.end());
        _dt = _CFL * _dx / _SDD_uxmax;
    }

    if (_Nx == 1) {
        _SDD_uymax = *std::max_element(_SDS_uymax.begin(), _SDS_uymax.end());
        _dt = _CFL * _dy / _SDD_uymax;
    }

    // Real formula in two dimensions
    if (_Nx > 1 && _Ny > 1) {
        // We need the max above all to be reproducible.
        updateDomainUmax();
        _dt = _CFL * _dx * _dy / (_Domain_uxmax * _dy + _Domain_uymax * _dx);
    }

    // Max increase.
    /*
    if (_last_dt > 0. && _dt > 1.1 * _last_dt)
        _dt = 1.1 * _last_dt;
    */

    // So that the final T is reached perfectly.
    std::min(_dt, _T - _t);
    
    // If the computation is set with random rounding error, the dt may differ among the sub-domains.
    // To ensure the computation (and also the number of iteration), we must communicate it.
    _dt = reduceMin(_dt);

    #ifndef NDEBUG
    // Show if dt drops.
    if (_MPI_rank == 0 && _dt < _min_dt) {
        std::cout << "[0] - " << _nIterations << " dt drops of ";
        std::cout << std::scientific << std::setprecision(std::numeric_limits<real>::max_digits10);
        std::cout << (1. - (_dt/_min_dt)) * 100. << " % to ";
        std::cout << Console::_red << Console::_bold ;
        std::cout << _dt << std::endl;
        std::cout << std::setprecision(2) << std::fixed << Console::_normal;
        _min_dt = _dt;
    }
    #endif
    
    #ifndef NDEBUG
    //std::cout << "New timestep _dt = " << _dt << " (ux / dx = " << _Domain_uxmax / _dx << ", uy / dy = " << _Domain_uymax / _dy << ")" << std::endl;
    // std::cout << "_t: " << _t << ",  _dt: " << _dt << ", _T:" << _T << std::endl;
    #endif

    // add timestep to global time.
    if (_MPI_rank == 0) {
        real y = _dt + _t_err;
        fastTwoSum(_t, y, _t, _t_err);
    }

    #ifndef SEQUENTIAL
    MPI_Bcast(&_t, 1, MPI_REALTYPE, 0, MPI_COMM_WORLD);
    #endif

    // Store current dt
    _last_dt = _dt;
}

real EulerRuO1::computePressure(real Ek, real E) {
    // Ek = (1. / 2.) * (rhou_x * rhou_x + rhou_y * rhou_y) / rho.
    // rhoe = rhoE - Ek
    // P = (gamma - 1.) * rhoe
    
    // Cannot divide by zero.
    real e = (E - Ek);

    real P = (_gamma - 1) * e;


    // To ensure Positivity in random mode.
    if (P < 0.) {
//        std::cout << std::scientific << std::setprecision(std::numeric_limits<real>::max_digits10);
//        std::cout << Console::_red << "P: " << P << " -> " << 0. << std::endl << Console::_normal << std::setprecision(2) << std::fixed;
        P = 0.;
    }

    assert(P >= 0.);
    return P; 
}

real EulerRuO1::computeSoundSpeed(const real& rho, const real& P) {
    // Cannot divide by zero.
    assert(rho > 0.);
    assert(P >= 0.);

    real c = rsqrt(_gamma * P / rho);
    assert(c >= 0.);

    /*
    if (rabs(c * c - _gamma * P / rho) != 0.0) {
        std::cout << std::scientific << std::setprecision(Number::max_digits10);
        std::cout << "c * c: " << c * c << ", _gamma * P / rho: " << _gamma * P / rho << std::endl;
        std::cout << "c: " << c << ", sqrt(_gamma * P / rho): " <<  sqrt(_gamma * P / rho) << std::endl;
        assert(c < 0.);
    }
    */

    return c;
}

void EulerRuO1::speed(const SDShared& sds, const std::map< std::string, Quantity<real>* >& quantityMap) {
    Quantity<real>& rho = *quantityMap.at("rho");
    Quantity<real>& rhou_x = *quantityMap.at("rhou_x");
    Quantity<real>& rhou_y = *quantityMap.at("rhou_y");
    Quantity<real>& rhoE = *quantityMap.at("rhoE");
    Quantity<real>& pressure = *quantityMap.at("pressure");
    Quantity<real>& sx = *quantityMap.at("sx");
    Quantity<real>& sy = *quantityMap.at("sy");

    // P = gamma * (gamma - 1.) * rho * e
    // c = sqrt(gamma * P / rho);

    // Flux speed
    // s_x = a^n_{i+1/2, j} = max(max(|u_x^n_{i,j} + c^n_{i,j}|, |u_x^n_{i,j} - c^n_{i,j}|), max(|u_x^n_{i+1,j} + c^n_{i+1,j}|, |u_x^n_{i+1,j} - c^n_{i+1,j}|))
    // s_y = a^n_{i, j+1/2} = max(max(|u_y^n_{i,j} + c^n_{i,j}|, |u_y^n_{i,j} - c^n_{i,j}|), max(|u_y^n_{i,j+1} + c^n_{i,j+1}|, |u_y^n_{i,j+1} - c^n_{i,j+1}|))

    real sdsUxMax(0.), sdsUyMax(0.);
    for (const auto& coords: sds) {
        const int i = coords.first;
        const int j = coords.second;
        size_t k_center = sds.convert(i, j);

        const real rho_center = rho.get0(k_center);
        if (rho_center == 0.) {
            pressure.set0(0., k_center);
            sx.set0(0., k_center);
            sy.set0(0., k_center);
            continue;
        }

        // This should never be negative of course.
        assert(rho_center > 0.);

        const real rhou_x_center = rhou_x.get0(k_center);
        const real rhou_y_center = rhou_y.get0(k_center);
        const real rhoE_center = rhoE.get0(k_center);

        const real ux = rhou_x_center / rho_center;
        const real uy = rhou_y_center / rho_center;
        const real Ek = (1. / 2.) * (ux * rhou_x_center + uy * rhou_y_center);
        const real pressure_center = computePressure(Ek, rhoE_center);
        pressure.set0(pressure_center, k_center);
        const real c = computeSoundSpeed(rho_center, pressure_center);

        const real sx_center = std::max(rabs(ux + c), rabs(ux - c));
        sx.set0(sx_center, k_center);

        const real sy_center = std::max(rabs(uy + c), rabs(uy - c));
        sy.set0(sy_center, k_center);

        if (sdsUxMax < sx_center)
            sdsUxMax = sx_center;

        if (sdsUyMax < sy_center)
            sdsUyMax = sy_center;
    }

    // Updating umax and uymax
    _SDS_uxmax[sds.getId()] = sdsUxMax;
    _SDS_uymax[sds.getId()] = sdsUyMax;
}

void EulerRuO1::flux(const SDShared& sds, const std::map< std::string, Quantity<real>* >& quantityMap) {

    Quantity<real>& rho = *quantityMap.at("rho");
    Quantity<real>& rhou_x = *quantityMap.at("rhou_x");
    Quantity<real>& rhou_y = *quantityMap.at("rhou_y");
    Quantity<real>& rhoE = *quantityMap.at("rhoE");
    Quantity<real>& pressure = *quantityMap.at("pressure");
    Quantity<real>& sx = *quantityMap.at("sx");
    Quantity<real>& sy = *quantityMap.at("sy");

    // U^{n+1}_{i,j} = U^n_{i,j} - dt / dx * (F^n_{i+1/2, j} - F^n_{i-1/2, j}) - dt / dy * (G^n_{i, j+1/2} - G^n_{i, j-1/2})
    // U^{n+1}_{i,j} = U^n_{i,j} - dt / dx * (F^n_x) - dt / dy * (G^n_y)

    // P = gamma * (gamma - 1.) * rho * e
    // c = sqrt(gamma * P / rho);
    // U = (rho, rhou_x, rhou_y, rhoE)
    // F = (rhou_x, rhou_x * rhou_x / rho + P, rhou_x *rhou_y / rho, (rhoE + P) * rhou_x / rho)
    // G = (rhou_y, rhou_x *rhou_y / rho, rhou_y * rhou_y / rho + P, (rhoE + P) * rhou_y / rho)

    // Fluxes
    // F^n_{i+1/2, j} = (1. / 2.) * ( F(U^n_{i,j}) + F(U^n_{i + 1,j}) - a^n_{i+1/2,j} * (U^n_{i+1, j} - U^n_{i, j}) )
    // F^n_{i-1/2, j} = (1. / 2.) * ( F(U^n_{i - 1,j}) + F(U^n_{i,j}) - a^n_{i-1/2,j} * (U^n_{i, j} - U^n_{i-1, j}) )
    // F^n_x = F^n_{i+1/2, j} - F^n_{i-1/2, j}
    // F^n_x = (1. / 2.) * ( F(U^n_{i + 1,j}) - F(U^n_{i - 1,j}) - a^n_{i+1/2,j} * (U^n_{i+1, j} - U^n_{i, j}) + a^n_{i-1/2,j} * (U^n_{i, j} - U^n_{i-1, j}))

    // G^n_{i, j+1/2} = (1. / 2.) * ( G(U^n_{i,j}) + G(U^n_{i,j + 1}) - a^n_{i,j+1/2} * (U^n_{i, j+1} - U^n_{i, j}) )
    // G^n_{i, j-1/2} = (1. / 2.) * ( G(U^n_{i,j - 1}) + G(U^n_{i,j}) - a^n_{i,j-1/2} * (U^n_{i, j} - U^n_{i, j-1}) )
    // G^n_y = G^n_{i, j+1/2} - G^n_{i, j-1/2}
    // G^n_y = (1. / 2.) * ( G(U^n_{i,j + 1}) - G(U^n_{i,j - 1}) - a^n_{i,j+1/2} * (U^n_{i, j+1} - U^n_{i, j}) + a^n_{i,j-1/2} * (U^n_{i, j} - U^n_{i, j-1}))

    // Flux speed
    // s_x = a^n_{i+1/2, j} = max(max(|u_x^n_{i,j} + c^n_{i,j}|, |u_x^n_{i,j} - c^n_{i,j}|), max(|u_x^n_{i+1,j} + c^n_{i+1,j}|, |u_x^n_{i+1,j} - c^n_{i+1,j}|))
    // s_y = a^n_{i, j+1/2} = max(max(|u_y^n_{i,j} + c^n_{i,j}|, |u_y^n_{i,j} - c^n_{i,j}|), max(|u_y^n_{i,j+1} + c^n_{i,j+1}|, |u_y^n_{i,j+1} - c^n_{i,j+1}|))

   
    // Compute flux X
    const real kx = 0.5 * _dt / _dx;
    const real ky = 0.5 * _dt / _dy;

    for (const auto& coords: sds) {

        const int i = coords.first;
        const int j = coords.second;
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

        /*
        if (rhou_y_center != 0. || rhou_y_left != 0. || rhou_y_right != 0.) {
            std::cout << std::scientific << std::setprecision(std::numeric_limits<real>::max_digits10);
            std::cout << "rhou_y_left: " <<  rhou_y_left << std::endl;
            std::cout << "rhou_y_center: " <<  rhou_y_center << std::endl;
            std::cout << "rhou_y_right: " <<  rhou_y_right << std::endl;            
            std::cout << _nIterations << " - i: " <<  i << ", j:" << j << std::endl;
            exitfail(1);
        } */

        real rhoE_left = rhoE.get0(k_left);
        real rhoE_center = rhoE.get0(k_center);
        real rhoE_right = rhoE.get0(k_right);
        real rhoE_top = rhoE.get0(k_top);
        real rhoE_bottom = rhoE.get0(k_bottom);

        real cell_sx_left = sx.get0(k_left);
        real cell_sx_center = sx.get0(k_center);
        real cell_sx_right = sx.get0(k_right);

        real cell_sy_top = sy.get0(k_top);
        real cell_sy_center = sy.get0(k_center);
        real cell_sy_bottom = sy.get0(k_bottom);

        real sx_left  = std::max(cell_sx_left, cell_sx_center);
        real sx_right = std::max(cell_sx_right, cell_sx_center);

        real sy_top  = std::max(cell_sy_top, cell_sy_center);
        real sy_bottom = std::max(cell_sy_bottom, cell_sy_center);

        real ux_left = (rho_left == 0.) ? 0. : rhou_x_left / rho_left;
        real ux_right = (rho_right == 0.) ? 0. : rhou_x_right / rho_right;
        
        real uy_top = (rho_top == 0.) ? 0. : rhou_y_top / rho_top;
        real uy_bottom = (rho_bottom == 0.) ? 0. : rhou_y_bottom / rho_bottom;
        
        real pressure_left = pressure.get0(k_left);
        real pressure_right = pressure.get0(k_right);
        real pressure_top = pressure.get0(k_top);
        real pressure_bottom = pressure.get0(k_bottom);
        
        // U = (rho, rhou_x, rhou_y, rhoE)
        // F = (rhou_x, rhou_x * rhou_x / rho + P, rhou_x *rhou_y / rho, (rhoE + P) * rhou_x / rho)
        // F^n_x = (1. / 2.) * ( F(U^n_{i + 1,j}) - F(U^n_{i - 1,j}) - a^n_{i+1/2,j} * (U^n_{i+1, j} - U^n_{i, j}) + a^n_{i-1/2,j} * (U^n_{i, j} - U^n_{i-1, j}))
    
        // G = (rhou_y, rhou_x *rhou_y / rho, rhou_y * rhou_y / rho + P, (rhoE + P) * rhou_y / rho)
        // G^n_y = (1. / 2.) * ( G(U^n_{i,j + 1}) - G(U^n_{i,j - 1}) - a^n_{i,j+1/2} * (U^n_{i, j+1} - U^n_{i, j}) + a^n_{i,j-1/2} * (U^n_{i, j} - U^n_{i, j-1}))

        // Horizontal Flux
        real rho_flux_x = rhou_x_right - rhou_x_left - sx_right * (rho_right - rho_center) + sx_left * (rho_center - rho_left);

        real rhou_x_flux_x = ux_right * rhou_x_right + pressure_right - ux_left * rhou_x_left  - pressure_left - sx_right * (rhou_x_right - rhou_x_center) + sx_left * (rhou_x_center - rhou_x_left);

        real rhou_y_flux_x = ux_right * rhou_y_right - ux_left * rhou_y_left - sx_right * (rhou_y_right - rhou_y_center) + sx_left * (rhou_y_center - rhou_y_left);

        real rhoE_flux_x = (rhoE_right + pressure_right ) * ux_right - (rhoE_left + pressure_left ) * ux_left - sx_right * (rhoE_right - rhoE_center) + sx_left * (rhoE_center - rhoE_left);

        // Vertical flux
        real rho_flux_y = rhou_y_top - rhou_y_bottom - sy_top * (rho_top - rho_center) + sy_bottom * (rho_center - rho_bottom);

        real rhou_x_flux_y = rhou_x_top * uy_top - rhou_x_bottom * uy_bottom - sy_top * (rhou_x_top - rhou_x_center) + sy_bottom * (rhou_x_center - rhou_x_bottom);

        real rhou_y_flux_y = uy_top * rhou_y_top + pressure_top - uy_bottom * rhou_y_bottom  - pressure_bottom - sy_top * (rhou_y_top - rhou_y_center) + sy_bottom * (rhou_y_center - rhou_y_bottom);

        real rhoE_flux_y = (rhoE_top + pressure_top ) * uy_top - (rhoE_bottom + pressure_bottom ) * uy_bottom - sy_top * (rhoE_top - rhoE_center) + sy_bottom * (rhoE_center - rhoE_bottom);

        // Set new values.
        rho.set1(rho_center - kx * rho_flux_x - ky * rho_flux_y, k_center);
        rhou_x.set1(rhou_x_center - kx * rhou_x_flux_x - ky * rhou_x_flux_y, k_center);
        rhou_y.set1(rhou_y_center - kx * rhou_y_flux_x - ky * rhou_y_flux_y, k_center);
        rhoE.set1(rhoE_center - kx * rhoE_flux_x  - ky * rhoE_flux_y, k_center);

        /*
        if (rhou_y.get1(k_center) != 0.) {
            std::cout << std::scientific << std::setprecision(std::numeric_limits<real>::max_digits10);
            std::cout << "ux_right: " <<  ux_right << ", rhou_y_right: " <<  rhou_y_right << " = " << ux_right * rhou_y_right  << std::endl;
            std::cout << "ux_left: " <<  ux_left << ", rhou_y_left: " <<  rhou_y_left << " = " << ux_left * rhou_y_left  << std::endl;
            std::cout << "sx_right: " <<  sx_right << ", (rhou_y_right - rhou_y_center): " <<  (rhou_y_right - rhou_y_center) << " = " << sx_right * (rhou_y_right - rhou_y_center)  << std::endl;
            std::cout << "sx_left: " <<  sx_left << ", (rhou_y_center - rhou_y_left): " <<  (rhou_y_center - rhou_y_left) << " = " << sx_left * (rhou_y_center - rhou_y_left)  << std::endl;

            std::cout << "rhou_y_left: " <<  rhou_y_left << std::endl;
            std::cout << "rhou_y_center: " <<  rhou_y_center << std::endl;
            std::cout << "rhou_y_right: " <<  rhou_y_right << std::endl;
            
            std::cout << "rhou_y_flux_x: " <<  rhou_y_flux_x << std::endl << std::endl;

            std::cout << "uy_top: " <<  uy_top<< ", rhou_y_top: " <<  rhou_y_top << " = " << uy_top * rhou_y_top  << std::endl;
            std::cout << "uy_bottom: " <<  uy_bottom << ", rhou_y_bottom: " <<  rhou_y_bottom << " = " << uy_bottom * rhou_y_bottom  << std::endl;
            std::cout << "sy_top: " <<  sy_top << ", (rhou_y_top - rhou_y_center): " <<  (rhou_y_top - rhou_y_center) << " = " << sy_top * (rhou_y_top - rhou_y_center)  << std::endl;
            std::cout << "sy_bottom: " <<  sy_bottom << ", (rhou_y_center - rhou_y_bottom): " <<  (rhou_y_center - rhou_y_bottom) << " = " << sy_bottom * (rhou_y_center - rhou_y_bottom) << std::endl;
            std::cout << "pressure_top: " <<  pressure_top << std::endl;
            std::cout << "pressure_bottom: " <<  pressure_bottom << std::endl;
            std::cout << "rhou_y_top: " <<  rhou_y_top << std::endl;
            std::cout << "rhou_y_center: " <<  rhou_y_center << std::endl;
            std::cout << "rhou_y_bottom: " <<  rhou_y_bottom << std::endl;
            std::cout << "rhou_y_flux_y: " <<  rhou_y_flux_y << std::endl;

            std::cout << _nIterations << " - i: " <<  i << ", j:" << j << std::endl;
            std::cout << sds.getNumberBoundaryCells() << std::endl;
            exitfail(1);
        } */
        
        /*
        if (rhou_y_flux_y > 0.) {
            std::cout << "y";
        }

        #ifndef NDEBUG
        if (rhoE_center - kx * rhoE_flux_x  + ky * rhoE_flux_y < 0.) {
            std::cout << "rhoE_center: " <<  rhoE_center << std::endl;
            std::cout << "rhoE_flux_x: " <<  rhoE_flux_x << std::endl;
            std::cout << "rhoE+1: " <<  rhoE_center - kx * rhoE_flux_x  + ky * rhoE_flux_y << std::endl;
        }
        #endif
        */
    }
}

int EulerRuO1::finalize() {
    writeState(_outputpath);
    return 0;
}

void EulerRuO1::updateBoundary(const SDShared& sds, const std::map< std::string, Quantity<real>*>& quantityMap) {
    // update BoundaryCells
    sds.updateBoundaryCells(quantityMap.at("rho"));
    sds.updateBoundaryCells(quantityMap.at("rhou_x"));
    sds.updateBoundaryCells(quantityMap.at("rhou_y"));
    sds.updateBoundaryCells(quantityMap.at("rhoE"));
}

void EulerRuO1::updatePressure(const SDShared& sds, const std::map< std::string, Quantity<real>*>& quantityMap) {
    // update BoundaryCells only for pressure
    sds.updateBoundaryCells(quantityMap.at("pressure"));

    // As a max, it's not necessary to update.
    // sds.updateBoundaryCells(quantityMap.at("sx"));
    // sds.updateBoundaryCells(quantityMap.at("sy"));
}

void EulerRuO1::writeState(std::string directory) {

    if (_dryFlag == 0) {
        IO::writeQuantity(directory, "rho", *_domain);
        IO::writeQuantity(directory, "rhou_x", *_domain);
        IO::writeQuantity(directory, "rhou_y", *_domain);
        IO::writeQuantity(directory, "rhoE", *_domain);
    }

    IO::writeVariantInfo(directory, *_domain);
    IO::writeSDDTime(directory, *_domain, "compute", _timerComputation.getSteadyTimeDeque());
    IO::writeSDDTime(directory, *_domain, "iteration", _timerIteration.getSteadyTimeDeque());
}
