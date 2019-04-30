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
    for (size_t v(0); v < _vsize; ++v) {
        delete[] _mv0[v];
        delete[] _mv1[v];
    }
    delete[] _mv0;
    delete[] _mv1;
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
    if (_cellsize % _bunitsize != 0)
        exitfail("We've got a problem here.");

    _bsize = _Nx * _cellsize / _bunitsize;
    _dt = _dx / _cellsize;
    _Nt = ceil(_T / _dt);

    // Now sizes are defined, must pass the test first.
    if(!unittest())
        exitfail(1);


    #ifndef SEQUENTIAL
    MPI_Bcast(&_Nt, 1, MPI_UNSIGNED, 0, MPI_COMM_WORLD);
    #endif

    initial_condition();
    return 0;
}

void BHydro::initial_condition() {

    _mv0 = new bline*[_vsize];
    _mv1 = new bline*[_vsize];
    for (size_t v(0); v < _vsize; ++v) {
        _mv0[v] = new bline[_bsize];
        _mv1[v] = new bline[_bsize];
    }

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

    for (size_t i(0); i < _bsize / 2; ++i) {
        _mv0[_vnull - 1] = 0x1101010101010100;
        _mv0[_vnull + 1] = 0x1101010101010100;
    }

    for (size_t i(_bsize / 2); i < _bsize; ++i) {
        _mv0[_vnull - 1] = 0x0000010000000000;
        _mv0[_vnull + 1] = 0x0000010000000000;
    }

        /*
        if (rand() % 2)
            _uxr0[i] = _mass0[i] & 0xffffffffffffffff;
        else
            _uxl0[i] = _mass0[i] & 0xffffffffffffffff;
        */
    }
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
    unsigned long int modulo =  _bsize / _Nx;
    std::cout << "modulo: " << modulo << std::endl;
    unsigned long int counter = 0, output_counter = 0;
    int sum = 0;
    unsigned int total = 0;
    double scale = 1. / (double)(16. * _cellsize / _bunitsize);
    for (size_t i(0); i <= _bsize; ++i, ++counter) {
        if (counter == modulo) {
            double r = (double)(sum);
            r *= scale;
            // std::cout << "counter: " << counter << "output_counter: " << output_counter << ", i: " << i << ", r: " << r << std::endl;
            sdd.setValue("rho", output_counter, 0, r);
            counter = 0;
            ++output_counter;
            total += sum;
            sum = 0;
            if (output_counter == _Nx)
                break;
        }
        sum += popCount(_uxl0[i] & _mass0[i]) + popCount(_uxr0[i] & _mass0[i]);
    }

    std::cout << "total mass: " << total << " / " << _bsize * _bunitsize << std::endl;
    std::cout << "end convolution: output " << output_counter << " values.\n";
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

        bline* tmp = _mass0;
        _mass0 = _mass1;
        _mass1 = tmp;

        tmp = _uxr0;
        _uxr0 = _uxr1;
        _uxr1 = tmp;

        tmp = _uxl0;
        _uxl0 = _uxl1;
        _uxl1 = tmp;

   	    _timerComputation.end();
        // ----------------------------------------------------------------------
        _timerIteration.end();
    }
    printStatus(true);
    return 0;
}

void BHydro::flux(const SDShared&, const std::map< std::string, Quantity<real>* >&) {
}




/*
void BHydro::lalgo(const bline& mass_in, const bline& uxl_in,
    bline& mass_out, bline& uxl_out, bline& p_from_right) const {

    bline immobile = mass_in & (~uxl_in);
    bline p = (mass_in & uxl_in);

    uxl_out = (p + mass_in + p_from_right) & ~immobile;
    mass_out = uxl_out | immobile;
    p_from_right = 0; // pb here (uxl_out & 0x8000000000000000) >> 63;
}
*/

/*
void BHydro::ralgo(const bline& mass_in, const bline& uxr_in,
    bline& mass_out, bline& uxr_out, bline& p_from_left) const {

    bline immobile = mass_in & (~uxr_in);
    bline p = (mass_in & uxr_in);

    bline w = ((p >> 1) & immobile) << 1;

    bline z = (mass_in >> 1);

    uxr_out = ((p - immobile) & mass_in) >> 1;
    uxr_out = ((immobile ^ p));
    mass_out = immobile | uxr_out;
    // --------------------------------------

    // This selects only qm (->) against immobile line.
    w = ((qm >> 1) & immobile) << 1;

    // This selects only qm (<-) against immobile line.
    z = ((qm << 1) & immobile) >> 1;

    // These are lines (-last bit) of bridges in -> direction.
    b = ((w - immobile) & immobile) ^ immobile;

    // Remove from speed what will be moved whithin immobile line.
    u = qm ^ w;

    // Finally, only immobile bits that transmit speed.
    // w = (w | b) >> 1;
    // u |= (qm - w) & w;
    // bit_from_left = (u & 1UL) << 63;
    // u >>= 1;

    // 0001001100000001000000010000000111110001011100010111000100001111
    // 0001001000000001000000000000000100000001000100010010000000001000
    // b = ((qm - immobile) & immobile) ^ immobile;
    // 0000000000000000000000000000000011100000010000000001000000000110
    //
    // b = ((w - immobile) & immobile) ^ immobile; // exact wall on the right (minus bit[0])
    // 0000000100000000000000000000000011110000011000000001000000000110

    // u = ((w - immobile) & immobile) ^ immobile;
    // u |=  (w | b);
    // u = b;
    // u = (w + immobile);


    // We add the bit from the left.
    // mobile = bit_from_left | u;
    // mass_out = mobile | immobile;
    // uxr_out = mobile;

    // 0001001100000001000000010000000111110001011100001111000100001111
    // 0001001000000001000000000000000100000001000100000010000000001000
    // w :
    // 0000001000000000000000000000000100000000000000000010000000001000
    // w | immobile: immobile + ceux qui bougent vers la droite contre un mur.
    // 0000001100000000000000010000000111110000011000001111000100001111
    // w - immobile:
    // 0000000011111111111111110000000000001111100111110100111100000001
    // (w - immobile) & immobile:
    // 0000000000000000000000010000000000000000000000000100000100000001
    // ((w - immobile) & immobile) ^ immobile:
    // 0000000100000000000000000000000011110000011000001001000000000110

    // z = ((z + mass_in) & mass_in) ^ mass_in;

    // immobile after an arrow:  -> |
    // mass_out = ((z + mass_in) & mass_in) ^ mass_in;
    // mass_out = z;
    // uxr_out = b;
    //uxr_out = ((w - mass_in) & mass_in) ^ mass_in;
    */
    /*
    bline immobile = mass_in & (~uxr_in);
    bline p = mass_in & uxr_in;

    // uxr_out = (p - mass_in) & (~mass_in);  // >..> => ....
    //uxr_out = (p - mass_in) & (~p);    // >..> => >..>

    //uxr_out = ((p - immobile) & immobile) ^ immobile;

    // if every left cell is ok then ok ?
    // uxr_out = (p - mass_in);

    // 1111000011110001001100010000000111110001011100001111000100001111
    // ...>....>..>...>..>............>.......>...>......>.........>... // p
    // ..>>......>>...>....>>>>...........>....>.>.>>>>.>..>>>>.......> // (p - immobile)
    // ...>.......>...>....>>>.................>...>>>>....>>>........> // (p - immobile) & (-immobile)
    // ..>.......>............>...........>......>......>.....>........ // (p - immobile) & ~(-immobile)
    // ...>>>>>>..>>>>>>>>.>>>.>>>>>>>>....>>>>>..>>>>>..>.>>>.>>>>>..> // -immobile
    // >>>......>>........>...>........>>>>.....>>.....>>.>...>.....>>. // ~(-immobile)

    // uxr_out = (p - immobile);
    uxr_out = (p - immobile) & (-immobile);

    // immobile bridges in the wrong direction.
    //mass_out = ((p + mass_in) ^ immobile) & immobile;
    mass_out = mass_in;

    //uxr_out = ((p + mass_in + p_from_left) & ~immobile);
    //mass_out = uxl_out | immobile;
    //p_from_left = (uxr_out & 0x8000000000000000) >> 63;
    //mass_out = 0UL;
    p_from_left = 0UL;
}
*/

/*
// No immobile version: symmetric velocities.
void BHydro::lalgo(const bline& mass_in, const bline& uxl_in, const bline& p_in,
    bline& mass_out, bline& uxl_out, bline& p_out) const {

    bline p = (mass_in & uxl_in);

    p_out = (p & 0x8000000000000000) >> 63;
    uxl_out = (p << 1) | p_in;
    mass_out |= uxl_out;
}

void BHydro::ralgo(const bline& mass_in, const bline& uxr_in, const bline& p_in,
    bline& mass_out, bline& uxr_out, bline& p_out) const {

    bline p = (mass_in & uxr_in);

    p_out = (p & 0x0000000000000001) << 63;
    uxr_out = (p >> 1) | p_in;
    mass_out = uxr_out;
} */

void BHydro::lalgo(const bline& mass_in, const bline& uxl_in, const bline& p_in,
    bline& mass_out, bline& uxl_out, bline& p_out) const {

    bline immobile(mass_in & ~uxl_in);
    bline p(mass_in & uxl_in);

    // This selects only (<-) against immobile line.
    bline z(((p << 1) & immobile) >> 1);

    // This selects only (<-) that are free.
    bline w(p & ~z);

    p_out = (p & 0x8000000000000000) >> 63;
    uxl_out = (z + (immobile >> 1) + p_in) & immobile;
    uxl_out |= (w << 1);
    mass_out |= uxl_out | immobile;
}

void BHydro::ralgo(const bline& mass_in, const bline& uxr_in, const bline& p_in,
    bline& mass_out, bline& uxr_out, bline& p_out) const {

    bline p = (mass_in & uxr_in);

    p_out = (p & 0x0000000000000001) << 63;
    uxr_out = (p >> 1) | p_in;
    mass_out = uxr_out;
}

void BHydro::lalgoslow(const std::bitset<64>& mass_in, const std::bitset<64>& uxl_in,
    std::bitset<64>& mass_out, std::bitset<64>& uxl_out, std::bitset<64>& p_from_right) const {
    mass_out.reset();
    uxl_out.reset();
    bool b(p_from_right[0]);
    for (size_t i(0); i < 64; ++i) {
        // If empty space, and no incoming value from the right, the result is empty.
        if (!mass_in[i] && !b) {
            mass_out.reset(i);
            uxl_out.reset(i);
            continue;
        }

        if (!mass_in[i] && b) {
            mass_out.set(i);
            uxl_out.set(i);
            b = false;
            continue;
        }

        if (mass_in[i] && uxl_in[i] && b) {
            mass_out.set(i);
            uxl_out.set(i);
            continue;
        }

        if (mass_in[i] && uxl_in[i] && !b) {
            mass_out.reset(i);
            uxl_out.reset(i);
            b = true;
            continue;
        }

        if (mass_in[i] && !uxl_in[i] && !b) {
            mass_out.set(i);
            uxl_out.reset(i);
            continue;
        }

        if (mass_in[i] && !uxl_in[i] && b) {
            mass_out.set(i);
            uxl_out.reset(i);
            continue;
        }
    }
    p_from_right.reset();
    if (b)
        p_from_right.set(0);
}

void BHydro::ralgoslow(const std::bitset<64>& mass_in, const std::bitset<64>& uxr_in,
    std::bitset<64>& mass_out, std::bitset<64>& uxr_out, std::bitset<64>& p_from_left) const {

    mass_out.reset();
    uxr_out.reset();
    bool b(p_from_left[63]);
    for (int i(63); i >= 0; --i) {
        // If empty space, and no incoming value from the right, the result is empty.
        if (!mass_in[i] && !b) {
            mass_out.reset(i);
            uxr_out.reset(i);
            continue;
        }

        if (!mass_in[i] && b) {
            mass_out.set(i);
            uxr_out.set(i);
            b = false;
            continue;
        }

        if (mass_in[i] && uxr_in[i] && b) {
            mass_out.set(i);
            uxr_out.set(i);
            continue;
        }

        if (mass_in[i] && uxr_in[i] && !b) {
            mass_out.reset(i);
            uxr_out.reset(i);
            b = true;
            continue;
        }

        if (mass_in[i] && !uxr_in[i] && !b) {
            mass_out.set(i);
            uxr_out.reset(i);
            continue;
        }

        if (mass_in[i] && !uxr_in[i] && b) {
            mass_out.set(i);
            uxr_out.reset(i);
            continue;
        }
    }
    p_from_left.reset();
    if (b)
        p_from_left.set(63);
}
void BHydro::show(const bline& mass, const bline& uxl, const bline& uxr) const {
    for (size_t i = 0; i < 64; ++i) {
        bline mask = 1UL << (63 - i);
        if (mass & mask) {
            if (uxl & uxr & mask) {
                std::cout << "!";
                continue;
            }

            if(uxl & mask) {
                std::cout << "<";
                continue;
            }

            if(uxr & mask) {
                std::cout << ">";
                continue;
            }
            std::cout << "i";
        } else {
            std::cout << ".";
        }
    }
    std::cout << std::endl;
}

bool BHydro::ralgotest(bline& mass, bline& speed, bline& border) const {
    std::cout << "ralgotest:\n";
    std::bitset<64> mi(mass);
    std::bitset<64> ui(speed);
    std::bitset<64> bl(border);
    bline mass_out(0x0), speed_out, border_out;
    ralgo(mass, speed, border, mass_out, speed_out, border_out);
    std::bitset<64> mo0(mass_out);
    std::bitset<64> uo0(speed_out);
    std::bitset<64> bl0(border);

    std::bitset<64> bl1(bl);
    std::bitset<64> mo1;
    std::bitset<64> uo1;
    ralgoslow(mi, ui, mo1, uo1, bl1);

    //if(mo0 != mo1 || uo0 != uo1 || bl0 != bl1)
    {
        std::cout << "before moving right:\n";
        std::cout << bl.to_string('.', '>') << '\n';
        show(mass, 0x0, speed);

        std::cout << "after moving right:\n";
        std::cout << bl0.to_string('.', '>') << '\n';
        std::cout << mo0 << '\n';
        std::cout << uo0.to_string('.', '>')  << '\n';

        std::cout << "after moving right (slow):\n";
        std::cout << bl1.to_string('.', '>') << '\n';
        std::cout << mo1 << '\n';
        std::cout << uo1.to_string('.', '>')  << '\n';
        // return false;
    }

    return true;
}

bool BHydro::lalgotest(bline& mass, bline& speed, bline& border) const {
    std::cout << "lalgotest:\n";
    std::bitset<64> mi(mass);
    std::bitset<64> ui(speed);
    std::bitset<64> bl(border);
    bline mass_out(0x0), speed_out, border_out;
    lalgo(mass, speed, border, mass_out, speed_out, border_out);
    std::bitset<64> mo0(mass_out);
    std::bitset<64> uo0(speed_out);
    std::bitset<64> bl0(border);

    std::bitset<64> bl1(bl);
    std::bitset<64> mo1;
    std::bitset<64> uo1;
    lalgoslow(mi, ui, mo1, uo1, bl1);

    if(mo0 != mo1 || uo0 != uo1 || bl0 != bl1) {
        std::cout << "before moving left:\n";
        std::cout << bl.to_string('.', '<') << '\n';
        show(mass, speed, 0x0);

        std::cout << "after moving left:\n";
        std::cout << bl0.to_string('.', '<') << '\n';
        show(mass_out, speed_out, 0x0);

        std::cout << "after moving left (slow):\n";
        std::cout << bl1.to_string('.', '<') << '\n';
        std::cout << mo1 << '\n';
        std::cout << uo1.to_string('.', '<')  << '\n';
        return false;
    }
    return true;
}

bool BHydro::unittest() const {
    bline mass_in(0x70f13101f170f10f);
    bline speed_in(0x1091200101102008);
    bline border(1UL);

    mass_in =  0x001003000ff00001;
    speed_in = 0x0010020004f00000;
    if(!lalgotest(mass_in, speed_in, border))
        return false;

    //mass_in =  0x10f13101f170f10f;
    //speed_in = 0x1091200101102008;

    mass_in =  0x00000000007f0000;
    speed_in = 0x0000000000700000;

    //border = 0x8000000000000000;
    border = 0UL;
    if(!ralgotest(mass_in, speed_in, border))
        return false;

    return false;
}

void BHydro::fluxion() {

    // Impose left border condition.
    bline bit_from_left_in(_mass0[0] & _uxl0[0] & 0x8000000000000000);

    // Move right
    bline bit_from_left_out;
    for (size_t i(0); i < _bsize; ++i) {
        ralgo(_mass0[i], _uxr0[i], bit_from_left_in, _mass1[i], _uxr1[i], bit_from_left_out);
        bit_from_left_in = bit_from_left_out;
    }

    // Impose right border condition
    bline bit_from_right_in(_mass0[_bsize - 1] & _uxr0[_bsize - 1] & 0x0000000000000001);

    // Move left
    bline bit_from_right_out;
    for (size_t i(_bsize - 1); i != 0xffffffffffffffff; --i) {
        lalgo(_mass0[i], _uxl0[i], bit_from_right_in, _mass1[i], _uxl1[i], bit_from_right_out);
        bit_from_right_in = bit_from_right_out;
    }

    /*
    unsigned long int total_mass = 0; // 18432
    for (size_t i(0); i <= _bsize; ++i) {
        total_mass += popCount(_uxl1[i] & _mass1[i]) + popCount(_uxr1[i] & _mass1[i]);
    }
    std::cout << "total_mass: " << total_mass << std::endl;
    if (total_mass < 18432)
        exitfail("oh là !");
    */
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
