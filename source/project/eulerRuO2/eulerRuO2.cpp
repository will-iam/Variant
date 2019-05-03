#include "eulerRuO2.hpp"
#include "IO.hpp"

#include <ios>
#include <iomanip>
#include <iostream>
#include <fstream>
#include <string>
#include <ostream>
#include <vector>
#include <algorithm>

EulerRuO2::EulerRuO2():
    Engine() {
}

EulerRuO2::~EulerRuO2() {

    delete _domain;
}

int EulerRuO2::init() {

    // Init domain
    _domain = new Domain();
    unsigned int _BClayer = IO::loadDomainInfo(_initpath, *_domain);
    std::cout << "BClayer" << _BClayer << std::endl;
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
    _domain->addEquation("speed", std::bind(&EulerRuO2::speed, this,
                                   std::placeholders::_1, std::placeholders::_2));

    _domain->addEquation("flux", std::bind(&EulerRuO2::flux, this,
                                   std::placeholders::_1, std::placeholders::_2));

    _domain->addEquation("updateBoundary", std::bind(&EulerRuO2::updateBoundary, this,
                                   std::placeholders::_1, std::placeholders::_2));

    _domain->addEquation("updatePressure", std::bind(&EulerRuO2::updatePressure, this,
                                   std::placeholders::_1, std::placeholders::_2));

    return 0;
}


int EulerRuO2::start() {

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
        //std::cout << "nouvelle iteratioooooooooooooooooooooon" << std::endl;
//        if (_nIterations==1){        exitfail(1);}
   	    _timerComputation.end();
        // ----------------------------------------------------------------------
        _timerIteration.end();
    }
    printStatus(true);
    return 0;
}

// Updating according to CFL and max velocity
void EulerRuO2::computeDT() {

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
        Number::fastTwoSum(_t, y, _t, _t_err);
    }

    #ifndef SEQUENTIAL
    MPI_Bcast(&_t, 1, MPI_REALTYPE, 0, MPI_COMM_WORLD);
    #endif

    // Store current dt
    _last_dt = _dt;
}

real EulerRuO2::computePressure(real Ek, real E) {
    // Ek = (1. / 2.) * (rhou_x * rhou_x + rhou_y * rhou_y) / rho.
    // rhoe = rhoE - Ek
    // P = (gamma - 1.) * rhoe

    // Cannot divide by zero.
    real e = (E - Ek);

    real P = (_gamma - Number::unit) * e;


    // To ensure Positivity in random mode.
    if (P < Number::zero) {
//        std::cout << std::scientific << std::setprecision(std::numeric_limits<real>::max_digits10);
//        std::cout << Console::_red << "P: " << P << " -> " << 0. << std::endl << Console::_normal << std::setprecision(2) << std::fixed;
        P = Number::zero;
    }

    assert(P >= Number::zero);
    return P;
}

real EulerRuO2::computeSoundSpeed(const real& rho, const real& P) {
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

void EulerRuO2::speed(const SDShared& sds, const std::map< std::string, Quantity<real>* >& quantityMap) {
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

    real sdsUxMax(Number::zero), sdsUyMax(Number::zero);
    for (const auto& coords: sds) {
        const int i = coords.first;
        const int j = coords.second;
        size_t k_center = sds.convert(i, j);

        const real rho_center = rho.get0(k_center);
        if (rho_center == Number::zero) {
            pressure.set0(Number::zero, k_center);
            sx.set0(Number::zero, k_center);
            sy.set0(Number::zero, k_center);
            continue;
        }

        // This should never be negative of course.
        assert(rho_center > 0.);

        const real rhou_x_center = rhou_x.get0(k_center);
        const real rhou_y_center = rhou_y.get0(k_center);
        const real rhoE_center = rhoE.get0(k_center);

        const real ux = rhou_x_center / rho_center;
        const real uy = rhou_y_center / rho_center;
        const real Ek = Number::half * (ux * rhou_x_center + uy * rhou_y_center);
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


real EulerRuO2::minmod(real a, real b) {
    real min = std::min(a,b);
    real max = std::max(a,b);
    return std::max(Number::zero,min)+std::min(Number::zero,max); 

}



void EulerRuO2::flux(const SDShared& sds, const std::map< std::string, Quantity<real>* >& quantityMap) {

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
    //const real kx = Number::half * _dt / _dx;
    //const real ky = Number::half * _dt / _dy;
    // std::cout << "dt = " << _dt << "dx = " << _dx << std::endl;

    for (const auto& coords: sds) {

        const int i = coords.first;
        const int j = coords.second;
        //std::cout << "i" << i << std::endl;
        size_t k_center = sds.convert(i, j);
        size_t k_bottom = sds.convert(i, j - 1);
        size_t k_top = sds.convert(i, j + 1);
        size_t k_bottom_center(k_bottom);
        size_t k_top_center(k_top);
        size_t k_bottom_bottom_center(k_bottom - 1);
        size_t k_top_top_center(k_top + 1);
        size_t k_left(k_center - 1);
        size_t k_right(k_center + 1);
        size_t k_left_center(k_center - 1);
        size_t k_right_center(k_center + 1);
        size_t k_left_left_center(k_center - 2);
        size_t k_right_right_center(k_center + 2);

        //std::cout << "kcenter" << k_center << std::endl;
        //std::cout << "kright" << k_right << std::endl;
        //std::cout << "kbottom" << k_bottom << std::endl;

        real rho_leftO1 = rho.get0(k_left);
        real rho_rightO1 = rho.get0(k_right);

        //std::cout << "rholeft O1 = " << rho_leftO1 << " rhoright O1 = " << rho_rightO1 << std::endl;





        real rho_center = rho.get0(k_center);
        
        real rho_left_center = rho.get0(k_left_center);
        real rho_right_center = rho.get0(k_right_center);
        real rho_left_left_center = rho.get0(k_left_left_center);
        real rho_right_right_center = rho.get0(k_right_right_center);

        real rho_bottom_center = rho.get0(k_bottom_center);
        real rho_top_center = rho.get0(k_top_center);
        real rho_bottom_bottom_center = rho.get0(k_bottom_bottom_center);
        real rho_top_top_center = rho.get0(k_top_top_center);
      


 
        real rhou_x_center = rhou_x.get0(k_center);
        
        real rhou_x_left_center = rhou_x.get0(k_left_center);
        real rhou_x_right_center = rhou_x.get0(k_right_center);
        real rhou_x_left_left_center = rhou_x.get0(k_left_left_center);
        real rhou_x_right_right_center = rhou_x.get0(k_right_right_center);

        real rhou_x_bottom_center = rhou_x.get0(k_bottom_center);
        real rhou_x_top_center = rhou_x.get0(k_top_center);
        real rhou_x_bottom_bottom_center = rhou_x.get0(k_bottom_bottom_center);
        real rhou_x_top_top_center = rhou_x.get0(k_top_top_center);


        real rhou_y_center = rhou_y.get0(k_center);

        real rhou_y_left_center = rhou_y.get0(k_left_center);
        real rhou_y_right_center = rhou_y.get0(k_right_center);
        real rhou_y_left_left_center = rhou_y.get0(k_left_left_center);
        real rhou_y_right_right_center = rhou_y.get0(k_right_right_center);

        real rhou_y_bottom_center = rhou_y.get0(k_bottom_center);
        real rhou_y_top_center = rhou_y.get0(k_top_center);
        real rhou_y_bottom_bottom_center = rhou_y.get0(k_bottom_bottom_center);
        real rhou_y_top_top_center = rhou_y.get0(k_top_top_center);


        /*
        if (rhou_y_center != 0. || rhou_y_left != 0. || rhou_y_right != 0.) {
            std::cout << std::scientific << std::setprecision(std::numeric_limits<real>::max_digits10);
            std::cout << "rhou_y_left: " <<  rhou_y_left << std::endl;
            std::cout << "rhou_y_center: " <<  rhou_y_center << std::endl;
            std::cout << "rhou_y_right: " <<  rhou_y_right << std::endl;
            std::cout << _nIterations << " - i: " <<  i << ", j:" << j << std::endl;
            exitfail(1);
        } */

        real rhoE_center = rhoE.get0(k_center);
        
        real rhoE_left_center = rhoE.get0(k_left_center);
        real rhoE_right_center = rhoE.get0(k_right_center);
        real rhoE_left_left_center = rhoE.get0(k_left_left_center);
        real rhoE_right_right_center = rhoE.get0(k_right_right_center);
            
        real rhoE_bottom_center = rhoE.get0(k_bottom_center);
        real rhoE_top_center = rhoE.get0(k_top_center);
        real rhoE_bottom_bottom_center = rhoE.get0(k_bottom_bottom_center);
        real rhoE_top_top_center = rhoE.get0(k_top_top_center);


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


        // U = (rho, rhou_x, rhou_y, rhoE)
        // F = (rhou_x, rhou_x * rhou_x / rho + P, rhou_x *rhou_y / rho, (rhoE + P) * rhou_x / rho)
        // F^n_x = (1. / 2.) * ( F(U^n_{i + 1,j}) - F(U^n_{i - 1,j}) - a^n_{i+1/2,j} * (U^n_{i+1, j} - U^n_{i, j}) + a^n_{i-1/2,j} * (U^n_{i, j} - U^n_{i-1, j}))

        // G = (rhou_y, rhou_x *rhou_y / rho, rhou_y * rhou_y / rho + P, (rhoE + P) * rhou_y / rho)
        // G^n_y = (1. / 2.) * ( G(U^n_{i,j + 1}) - G(U^n_{i,j - 1}) - a^n_{i,j+1/2} * (U^n_{i, j+1} - U^n_{i, j}) + a^n_{i,j-1/2} * (U^n_{i, j} - U^n_{i, j-1}))






        real rho_sigma_left = (rho_center - rho_left_center)/(_dx);
        real rho_sigma_right = (rho_right_center - rho_center)/(_dx);
        real rho_sigma_left_left = (rho_left_center - rho_left_left_center)/(_dx);
        real rho_sigma_right_right = (rho_right_right_center - rho_right_center)/(_dx);
        real rho_by_x_slope_center = minmod(rho_sigma_left, rho_sigma_right);
        real rho_slope_left = minmod(rho_sigma_left_left, rho_sigma_left);
        real rho_slope_right = minmod(rho_sigma_right, rho_sigma_right_right);

        real rho_left_moins = rho_left_center + rho_slope_left * _dx * Number::half;
        real rho_left_plus = rho_center - rho_by_x_slope_center * _dx * Number::half;
        real rho_right_moins = rho_center + rho_by_x_slope_center*_dx * Number::half;
        real rho_right_plus = rho_right_center - rho_slope_right*_dx * Number::half;
        real rho_left = (rho_left_moins + rho_left_plus) * Number::half;
        real rho_right = (rho_right_moins + rho_right_plus) * Number::half;

     //   rho_left = rho_left_moins;
     //   rho_right = rho_right_plus;


        real rho_sigma_bottom = (rho_center - rho_bottom_center)/(_dx);
        real rho_sigma_top = (rho_top_center - rho_center)/(_dx);
        real rho_sigma_bottom_bottom = (rho_bottom_center - rho_bottom_bottom_center)/(_dx);
        real rho_sigma_top_top = (rho_top_top_center - rho_top_center)/(_dx);
        real rho_by_y_slope_center = minmod(rho_sigma_bottom, rho_sigma_top);
        real rho_slope_bottom = minmod(rho_sigma_bottom_bottom, rho_sigma_bottom);
        real rho_slope_top = minmod(rho_sigma_top, rho_sigma_top_top);

        real rho_bottom_moins = rho_bottom_center + rho_slope_bottom * _dx * Number::half;
        real rho_bottom_plus = rho_center - rho_by_y_slope_center * _dx * Number::half;
        real rho_top_moins = rho_center + rho_by_y_slope_center*_dx * Number::half;
        real rho_top_plus = rho_top_center - rho_slope_top*_dx * Number::half;
        real rho_bottom = (rho_bottom_moins + rho_bottom_plus) * Number::half;
        real rho_top = (rho_top_moins + rho_top_plus) * Number::half;

     //   rho_bottom = rho_bottom_moins;
     //   rho_top = rho_top_plus;


 

        real rhou_x_sigma_left = (rhou_x_center - rhou_x_left_center)/(_dx);
        real rhou_x_sigma_right = (rhou_x_right_center - rhou_x_center)/(_dx);
        real rhou_x_sigma_left_left = (rhou_x_left_center - rhou_x_left_left_center)/(_dx);
        real rhou_x_sigma_right_right = (rhou_x_right_right_center - rhou_x_right_center)/(_dx);
        real rhou_x_by_x_slope_center = minmod(rhou_x_sigma_left, rhou_x_sigma_right);
        real rhou_x_slope_left = minmod(rhou_x_sigma_left_left, rhou_x_sigma_left);
        real rhou_x_slope_right = minmod(rhou_x_sigma_right, rhou_x_sigma_right_right);
        
        real rhou_x_left_moins = rhou_x_left_center + rhou_x_slope_left * _dx * Number::half;
        real rhou_x_left_plus = rhou_x_center - rhou_x_by_x_slope_center * _dx * Number::half;
        real rhou_x_right_moins = rhou_x_center + rhou_x_by_x_slope_center*_dx * Number::half; 
        real rhou_x_right_plus = rhou_x_right_center - rhou_x_slope_right*_dx * Number::half;
        real rhou_x_left = (rhou_x_left_moins + rhou_x_left_plus) * Number::half;
        real rhou_x_right = (rhou_x_right_moins + rhou_x_right_plus) * Number::half;


       // rhou_x_left = rhou_x_left_moins;
      //  rhou_x_right = rhou_x_right_plus;

        real rhou_x_sigma_bottom = (rhou_x_center - rhou_x_bottom_center)/(_dx);
        real rhou_x_sigma_top = (rhou_x_top_center - rhou_x_center)/(_dx);
        real rhou_x_sigma_bottom_bottom = (rhou_x_bottom_center - rhou_x_bottom_bottom_center)/(_dx);
        real rhou_x_sigma_top_top = (rhou_x_top_top_center - rhou_x_top_center)/(_dx);
        real rhou_x_by_y_slope_center = minmod(rhou_x_sigma_bottom, rhou_x_sigma_top);
        real rhou_x_slope_bottom = minmod(rhou_x_sigma_bottom_bottom, rhou_x_sigma_bottom);
        real rhou_x_slope_top = minmod(rhou_x_sigma_top, rhou_x_sigma_top_top);
        
        real rhou_x_bottom_moins = rhou_x_bottom_center + rhou_x_slope_bottom * _dx * Number::half;
        real rhou_x_bottom_plus = rhou_x_center - rhou_x_by_y_slope_center * _dx * Number::half;
        real rhou_x_top_moins = rhou_x_center + rhou_x_by_y_slope_center*_dx * Number::half; 
        real rhou_x_top_plus = rhou_x_top_center - rhou_x_slope_top*_dx * Number::half;
        real rhou_x_bottom = (rhou_x_bottom_moins + rhou_x_bottom_plus) * Number::half;
        real rhou_x_top = (rhou_x_top_moins + rhou_x_top_plus) * Number::half;

     //   rhou_x_bottom = rhou_x_bottom_moins;
     //   rhou_x_top = rhou_x_top_plus;



 
        real rhou_y_sigma_left = (rhou_y_center - rhou_y_left_center)/(_dx);
        real rhou_y_sigma_right = (rhou_y_right_center - rhou_y_center)/(_dx);
        real rhou_y_sigma_left_left = (rhou_y_left_center - rhou_y_left_left_center)/(_dx);
        real rhou_y_sigma_right_right = (rhou_y_right_right_center - rhou_y_right_center)/(_dx);
        real rhou_y_by_x_slope_center = minmod(rhou_y_sigma_left, rhou_y_sigma_right);
        real rhou_y_slope_left = minmod(rhou_y_sigma_left_left, rhou_y_sigma_left);
        real rhou_y_slope_right = minmod(rhou_y_sigma_right, rhou_y_sigma_right_right);
       
        real rhou_y_left_moins = rhou_y_left_center + rhou_y_slope_left * _dx * Number::half;
        real rhou_y_left_plus = rhou_y_center - rhou_y_by_x_slope_center * _dx * Number::half;
        real rhou_y_right_moins = rhou_y_center + rhou_y_by_x_slope_center*_dx * Number::half; 
        real rhou_y_right_plus = rhou_y_right_center - rhou_y_slope_right*_dx * Number::half;
        real rhou_y_left = (rhou_y_left_moins + rhou_y_left_plus) * Number::half;
        real rhou_y_right = (rhou_y_right_moins + rhou_y_right_plus) * Number::half;

     //   rhou_y_left = rhou_y_left_moins;
     //   rhou_y_right = rhou_y_right_plus;
        

        real rhou_y_sigma_bottom = (rhou_y_center - rhou_y_bottom_center)/(_dx);
        real rhou_y_sigma_top = (rhou_y_top_center - rhou_y_center)/(_dx);
        real rhou_y_sigma_bottom_bottom = (rhou_y_bottom_center - rhou_y_bottom_bottom_center)/(_dx);
        real rhou_y_sigma_top_top = (rhou_y_top_top_center - rhou_y_top_center)/(_dx);
        real rhou_y_by_y_slope_center = minmod(rhou_y_sigma_bottom, rhou_y_sigma_top);
        real rhou_y_slope_bottom = minmod(rhou_y_sigma_bottom_bottom, rhou_y_sigma_bottom);
        real rhou_y_slope_top = minmod(rhou_y_sigma_top, rhou_y_sigma_top_top);
        
        real rhou_y_bottom_moins = rhou_y_bottom_center + rhou_y_slope_bottom * _dx * Number::half;
        real rhou_y_bottom_plus = rhou_y_center - rhou_y_by_y_slope_center * _dx * Number::half;
        real rhou_y_top_moins = rhou_y_center + rhou_y_by_y_slope_center*_dx * Number::half; 
        real rhou_y_top_plus = rhou_y_top_center - rhou_y_slope_top*_dx * Number::half;
        real rhou_y_bottom = (rhou_y_bottom_moins + rhou_y_bottom_plus) * Number::half;
        real rhou_y_top = (rhou_y_top_moins + rhou_y_top_plus) * Number::half;

     //   rhou_y_bottom = rhou_y_bottom_moins;
    //    rhou_y_top = rhou_y_top_plus;




        real rhoE_sigma_left = (rhoE_center - rhoE_left_center)/(_dx);
        real rhoE_sigma_right = (rhoE_right_center - rhoE_center)/(_dx);
        real rhoE_sigma_left_left = (rhoE_left_center - rhoE_left_left_center)/(_dx);
        real rhoE_sigma_right_right = (rhoE_right_right_center - rhoE_right_center)/(_dx);
        real rhoE_by_x_slope_center = minmod(rhoE_sigma_left, rhoE_sigma_right);
        real rhoE_slope_left = minmod(rhoE_sigma_left_left, rhoE_sigma_left);
        real rhoE_slope_right = minmod(rhoE_sigma_right, rhoE_sigma_right_right);
       
        real rhoE_left_moins = rhoE_left_center + rhoE_slope_left * _dx * Number::half;
        real rhoE_left_plus = rhoE_center - rhoE_by_x_slope_center * _dx * Number::half;
        real rhoE_right_moins = rhoE_center + rhoE_by_x_slope_center*_dx * Number::half; 
        real rhoE_right_plus = rhoE_right_center - rhoE_slope_right*_dx * Number::half;
        real rhoE_left = (rhoE_left_moins + rhoE_left_plus) * Number::half;
        real rhoE_right = (rhoE_right_moins + rhoE_right_plus) * Number::half;

   //     rhoE_left = rhoE_left_moins;
   //     rhoE_right = rhoE_right_plus;


        real rhoE_sigma_bottom = (rhoE_center - rhoE_bottom_center)/(_dx);
        real rhoE_sigma_top = (rhoE_top_center - rhoE_center)/(_dx);
        real rhoE_sigma_bottom_bottom = (rhoE_bottom_center - rhoE_bottom_bottom_center)/(_dx);
        real rhoE_sigma_top_top = (rhoE_top_top_center - rhoE_top_center)/(_dx);
        real rhoE_by_y_slope_center = minmod(rhoE_sigma_bottom, rhoE_sigma_top);
        real rhoE_slope_bottom = minmod(rhoE_sigma_bottom_bottom, rhoE_sigma_bottom);
        real rhoE_slope_top = minmod(rhoE_sigma_top, rhoE_sigma_top_top);
        
        real rhoE_bottom_moins = rhoE_bottom_center + rhoE_slope_bottom * _dx * Number::half;
        real rhoE_bottom_plus = rhoE_center - rhoE_by_y_slope_center * _dx * Number::half;
        real rhoE_top_moins = rhoE_center + rhoE_by_y_slope_center*_dx * Number::half; 
        real rhoE_top_plus = rhoE_top_center - rhoE_slope_top*_dx * Number::half;
        real rhoE_bottom = (rhoE_bottom_moins + rhoE_bottom_plus) * Number::half;
        real rhoE_top = (rhoE_top_moins + rhoE_top_plus) * Number::half;

  //      rhoE_bottom = rhoE_bottom_moins;
  //      rhoE_top = rhoE_top_plus;


/*

         rho_left = rho.get0(k_left);
         rho_center = rho.get0(k_center);
         rho_right = rho.get0(k_right);
         rho_top = rho.get0(k_top);
         rho_bottom = rho.get0(k_bottom);

         rhou_x_left = rhou_x.get0(k_left);
         rhou_x_center = rhou_x.get0(k_center);
         rhou_x_right = rhou_x.get0(k_right);
         rhou_x_top = rhou_x.get0(k_top);
         rhou_x_bottom = rhou_x.get0(k_bottom);

         rhou_y_left = rhou_y.get0(k_left);
         rhou_y_center = rhou_y.get0(k_center);
         rhou_y_right = rhou_y.get0(k_right);
         rhou_y_top = rhou_y.get0(k_top);
         rhou_y_bottom = rhou_y.get0(k_bottom);


         rhoE_left = rhoE.get0(k_left);
         rhoE_center = rhoE.get0(k_center);
         rhoE_right = rhoE.get0(k_right);
         rhoE_top = rhoE.get0(k_top);
         rhoE_bottom = rhoE.get0(k_bottom);


         rho_left = (rho.get0(k_left)+rho.get0(k_center)) * Number::half;
         rho_center = rho.get0(k_center);
         rho_right = (rho.get0(k_right)+rho.get0(k_center)) * Number::half;
         rho_top = (rho.get0(k_top)+rho.get0(k_center)) * Number::half;
         rho_bottom = (rho.get0(k_bottom)+rho.get0(k_center)) * Number::half;


         rhou_x_left = (rhou_x.get0(k_left)+rhou_x.get0(k_center)) * Number::half;
         rhou_x_center = rhou_x.get0(k_center);
         rhou_x_right = (rhou_x.get0(k_right)+rhou_x.get0(k_center)) * Number::half;
         rhou_x_top = (rhou_x.get0(k_top)+rhou_x.get0(k_center)) * Number::half;
         rhou_x_bottom = (rhou_x.get0(k_bottom)+rhou_x.get0(k_center)) * Number::half;

         rhou_y_left = (rhou_y.get0(k_left)+rhou_y.get0(k_center)) * Number::half;
         rhou_y_center = rhou_y.get0(k_center);
         rhou_y_right = (rhou_y.get0(k_right)+rhou_y.get0(k_center)) * Number::half;
         rhou_y_top = (rhou_y.get0(k_top)+rhou_y.get0(k_center)) * Number::half;
         rhou_y_bottom = (rhou_y.get0(k_bottom)+rhou_y.get0(k_center)) * Number::half;

         rhoE_left = (rhoE.get0(k_left)+rhoE.get0(k_center)) * Number::half;
         rhoE_center = rhoE.get0(k_center);
         rhoE_right = (rhoE.get0(k_right)+rhoE.get0(k_center)) * Number::half;
         rhoE_top = (rhoE.get0(k_top)+rhoE.get0(k_center)) * Number::half;
         rhoE_bottom = (rhoE.get0(k_bottom)+rhoE.get0(k_center)) * Number::half;

*/


        real ux_left = ((2 * rho_left - rho_center) == Number::zero) ? Number::zero : (2 * rhou_x_left - rhou_x_center) / (2 * rho_left - rho_center);
        real ux_right = ((2 * rho_right - rho_center) == Number::zero) ? Number::zero : (2 * rhou_x_right - rhou_x_center) / (2 * rho_right - rho_center);

        real ux_center = (rho_center == Number::zero) ? Number::zero : rhou_x_center / rho_center;
        real uy_center = (rho_center == Number::zero) ? Number::zero : rhou_y_center / rho_center;
        
        real uy_top = ((2 * rho_top - rho_center) == Number::zero) ? Number::zero : (2 * rhou_y_top - rhou_y_center) / (2 * rho_top - rho_center);
        real uy_bottom = ((2 * rho_bottom - rho_center) == Number::zero) ? Number::zero : (2 * rhou_y_bottom - rhou_y_center) / (2 * rho_bottom - rho_center); 

        real pressure_left = pressure.get0(k_left);
        real pressure_right = pressure.get0(k_right);
        real pressure_top = pressure.get0(k_top);
        real pressure_bottom = pressure.get0(k_bottom);

        real pressure_center = pressure.get0(k_center);

        pressure_left = (pressure.get0(k_left)+pressure.get0(k_center)) * Number::half;
        pressure_right = (pressure.get0(k_right)+pressure.get0(k_center)) * Number::half;
        pressure_center = pressure.get0(k_center);
        pressure_top = (pressure.get0(k_top)+pressure.get0(k_center)) * Number::half;
        pressure_bottom = (pressure.get0(k_bottom)+pressure.get0(k_center)) * Number::half;
  


        /*std::cout << "rholeft O2 = " << rho_left << " rhoright O2 = " << rho_right << std::endl;
        std::cout << "= " << rho_left_center << " rhoslopeleft = " << rho_slope_left << std::endl;
        std::cout << "rholeftmoins = " << rho_left_moins << " rholeftplus = " << rho_left_plus << std::endl;
        std::cout << "rholeft O2 = " << rho_left << " rhoright O2 = " << rho_right << std::endl;
        */

/*
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
*/

        const real kx = _dt / _dx;
        const real ky = _dt / _dy;

        // Horizontal Flux
        real rho_flux_x = rhou_x_right - rhou_x_left - sx_right * (rho_right - rho_center) + sx_left * (rho_center - rho_left);

        real rhou_x_flux_x = (2 * rhou_x_right - rhou_x_center) * (ux_right * Number::half) + pressure_right - (2 * rhou_x_left - rhou_x_center) * (ux_left * Number::half) - pressure_left - sx_right * (rhou_x_right - rhou_x_center) + sx_left * (rhou_x_center - rhou_x_left);

        real rhou_y_flux_x = (2 * rhou_y_right - rhou_y_center) * (ux_right * Number::half) - (2 * rhou_y_left - rhou_y_center) * (ux_left * Number::half) - sx_right * (rhou_y_right - rhou_y_center) + sx_left * (rhou_y_center - rhou_y_left);

        real rhoE_flux_x = ((2 * rhoE_right - rhoE_center) + (2 * pressure_right - pressure_center)) * (ux_right * Number::half) - ((2 * rhoE_left - rhoE_center) + (2 * pressure_left - pressure_center)) * (ux_left * Number::half) - sx_right * (rhoE_right - rhoE_center) + sx_left * (rhoE_center - rhoE_left);

/*
        rhou_x_flux_x = ux_right * rhou_x_right + pressure_right - ux_left * rhou_x_left  - pressure_left - sx_right * (rhou_x_right - rhou_x_center) + sx_left * (rhou_x_center - rhou_x_left);

        rhou_y_flux_x = ux_right * rhou_y_right - ux_left * rhou_y_left - sx_right * (rhou_y_right - rhou_y_center) + sx_left * (rhou_y_center - rhou_y_left);

        rhoE_flux_x = (rhoE_right + pressure_right ) * ux_right - (rhoE_left + pressure_left ) * ux_left - sx_right * (rhoE_right - rhoE_center) + sx_left * (rhoE_center - rhoE_left);
*/


        // Vertical flux
        real rho_flux_y = rhou_y_top - rhou_y_bottom - sy_top * (rho_top - rho_center) + sy_bottom * (rho_center - rho_bottom);

        real rhou_x_flux_y = (2 * rhou_x_top - rhou_x_center) * (uy_top * Number::half) - (2 * rhou_x_bottom - rhou_x_center) * (uy_bottom * Number::half) - sy_top * (rhou_x_top - rhou_x_center) + sy_bottom * (rhou_x_center - rhou_x_bottom);

        real rhou_y_flux_y = (2 * rhou_y_top - rhou_y_center) * (uy_top * Number::half) + pressure_top - (2 * rhou_y_bottom - rhou_y_center) * (uy_bottom * Number::half) - pressure_bottom - sy_top * (rhou_y_top - rhou_y_center) + sy_bottom * (rhou_y_center - rhou_y_bottom);

        real rhoE_flux_y = ((2 * rhoE_top - rhoE_center) + (2 * pressure_top - pressure_center)) * (uy_top * Number::half) - ((2 * rhoE_bottom - rhoE_center) + (2 * pressure_bottom - pressure_center)) * (uy_bottom * Number::half) - sy_top * (rhoE_top - rhoE_center) + sy_bottom * (rhoE_center - rhoE_bottom);
        
/*
        rhou_x_flux_y = rhou_x_top * uy_top - rhou_x_bottom * uy_bottom - sy_top * (rhou_x_top - rhou_x_center) + sy_bottom * (rhou_x_center - rhou_x_bottom);

        rhou_y_flux_y = uy_top * rhou_y_top + pressure_top - uy_bottom * rhou_y_bottom  - pressure_bottom - sy_top * (rhou_y_top - rhou_y_center) + sy_bottom * (rhou_y_center - rhou_y_bottom);

        rhoE_flux_y = (rhoE_top + pressure_top ) * uy_top - (rhoE_bottom + pressure_bottom ) * uy_bottom - sy_top * (rhoE_top - rhoE_center) + sy_bottom * (rhoE_center - rhoE_bottom);
*/


        std::cout.precision(4);
        std::cout << "kcenter = " << k_center << std::endl;
        std::cout << "rholeft = " << rho_left << std::endl;
        std::cout << "rho instant n = " << rho_center << std::endl;
        std::cout << "rho instant n+1 = " << rho_center - kx * rho_flux_x - ky * rho_flux_y << std::endl;
        std::cout << "rhoright = " << rho_right << std::endl;
        std::cout << "uxleft = " << ux_left << std::endl;
        std::cout << "uxright= " << ux_right << std::endl;
        std::cout << "rhouxleft = " << rhou_x_left << std::endl;
        std::cout << "rhoux n = " << rhou_x_center << std::endl;
        std::cout << "rhoux n+1 = " << rhou_x_center - kx * rhou_x_flux_x - ky * rhou_x_flux_y << std::endl;
        std::cout << "rhoux right" << rhou_x_right << std::endl;
        std::cout << "rhouxflux = " << rhou_x_flux_x << std::endl;
        std::cout << "ux = " << (rhou_x_center - kx * rhou_x_flux_x - ky * rhou_x_flux_y) / (rho_center - kx * rho_flux_x - ky * rho_flux_y) << std::endl;
        std::cout << "energy = " << (rhoE_center - kx * rhoE_flux_x  - ky * rhoE_flux_y) / (rho_center - kx * rho_flux_x - ky * rho_flux_y) << std::endl;
        std::cout << "fluxenergy gauche = " << ((2 * rhoE_left - rhoE_center) + (2 * pressure_left - pressure_center)) * ux_left << std::endl;
        std::cout << "flucenergy droite = " << ((2 * rhoE_right - rhoE_center) + (2 * pressure_right - pressure_center)) * ux_right << std::endl;
        std::cout << "flucenergy sx = " << sx_right * (rhoE_right - rhoE_center) + sx_left * (rhoE_center - rhoE_left) << std::endl;
        std::cout << "rhoEflux = " << rhoE_flux_x << std::endl;
        std::cout << "pressure gauche = " << pressure_left << std::endl;
        std::cout << "pressire center = " << pressure_center << std::endl;
        std::cout << "pressure droite = " << pressure_right << std::endl;

        if ( rho_center - kx * rho_flux_x - ky * rho_flux_y >1){ exitfail(1);}
        // Set new values.
        rho.set1(rho_center - kx * rho_flux_x - ky * rho_flux_y, k_center);
        rhou_x.set1(rhou_x_center - kx * rhou_x_flux_x - ky * rhou_x_flux_y, k_center);
        rhou_y.set1(rhou_y_center - kx * rhou_y_flux_x - ky * rhou_y_flux_y, k_center);
        rhoE.set1(rhoE_center - kx * rhoE_flux_x  - ky * rhoE_flux_y, k_center);


        if (rho.get1(k_center) < Number::zero) {
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

            std::cout << "rho_center: " <<  rho_center << std::endl;
            std::cout << "kx * rho_flux_x: " <<  kx * rho_flux_x << std::endl;
            std::cout << "ky * rho_flux_y: " <<  ky * rho_flux_y << std::endl;
            std::cout << "rho.get1(k_center): " <<  rho.get1(k_center) << std::endl;

            std::cout << _nIterations << " - i: " <<  i << ", j:" << j << std::endl;
            std::cout << sds.getNumberBoundaryCells() << std::endl;
            exitfail(1);
        }

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

int EulerRuO2::finalize() {
    writeState(_outputpath);
    return 0;
}

void EulerRuO2::updateBoundary(const SDShared& sds, const std::map< std::string, Quantity<real>*>& quantityMap) {
    // update BoundaryCells
    sds.updateBoundaryCells(quantityMap.at("rho"), _t);
    sds.updateBoundaryCells(quantityMap.at("rhou_x"), _t);
    sds.updateBoundaryCells(quantityMap.at("rhou_y"), _t);
    sds.updateBoundaryCells(quantityMap.at("rhoE"), _t);
}

void EulerRuO2::updatePressure(const SDShared& sds, const std::map< std::string, Quantity<real>*>& quantityMap) {
    // update BoundaryCells only for pressure
    sds.updateBoundaryCells(quantityMap.at("pressure"), _t);

    // As a max, it's not necessary to update.
    // sds.updateBoundaryCells(quantityMap.at("sx"));
    // sds.updateBoundaryCells(quantityMap.at("sy"));
}

void EulerRuO2::writeState(std::string directory) {

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
