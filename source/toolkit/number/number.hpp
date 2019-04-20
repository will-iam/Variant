#ifndef NUMBER_HPP
#define NUMBER_HPP

#include <cmath>
#include <random>
#include <limits>
#include <sstream>
#ifndef SEQUENTIAL
#include <mpi.h>
#endif

#define positiveModulo(a, b) (((a) % (b)) + (b)) % (b)

#if defined(PRECISION_WEAK_FLOAT)
    #include "weakfloat.hpp"
    typedef weakfloat<PRECISION_WEAK_FLOAT> real;
    inline void stor(std::string tmpStr, real& target) {
        target = std::stof(tmpStr);
    }
    #ifndef SEQUENTIAL
    const MPI_Datatype MPI_REALTYPE = MPI_FLOAT;
    #endif
#endif

#if defined(PRECISION_FLOAT)
    typedef float real;
    constexpr auto rabs = fabsf;
    constexpr auto rcos = cosf;
    constexpr auto rsqrt = sqrtf;
    inline void stor(std::string tmpStr, real& target) {
        target = std::stof(tmpStr);
    }
    #ifndef SEQUENTIAL
    const MPI_Datatype MPI_REALTYPE = MPI_FLOAT;
    #endif
#endif

#if defined(PRECISION_DOUBLE)
    typedef double real;
    constexpr auto rabs = fabs;
    constexpr auto rcos = cos;
    constexpr auto rsqrt = sqrt;
    inline void stor(std::string tmpStr, real& target) {
        target = std::stod(tmpStr);
    }
    #ifndef SEQUENTIAL
    const MPI_Datatype MPI_REALTYPE = MPI_DOUBLE;
    #endif
#endif

#if defined(PRECISION_LONG_DOUBLE)
    typedef long double real;
    constexpr auto rabs = fabsl;
    constexpr auto rcos = cosl;
    constexpr auto rsqrt = sqrtl;
    inline void stor(std::string tmpStr, real& target) {
        target = std::stold(tmpStr);
    }
    #ifndef SEQUENTIAL
    const MPI_Datatype MPI_REALTYPE = MPI_LONG_DOUBLE;
    #endif
#endif

#if defined(PRECISION_QUAD)
    extern "C" {
        #include <quadmath.h>
    }
    typedef __float128 real;
    constexpr auto rabs = fabsq;
    constexpr auto rcos = cosq;
    constexpr auto rsqrt = sqrtq;
    inline void stor(std::string tmpStr, real& target) {
        target = strtoflt128 (tmpStr.c_str(), NULL);
    }

    #ifndef SEQUENTIAL
    const MPI_Datatype MPI_REALTYPE = MPI_REAL16;
    #endif

    inline std::ostream& operator<< (std::ostream& out, const real& x) {
        char buf[128];
        const int charPrinted = quadmath_snprintf (buf, 128, "%.30Qe", x);
        if (static_cast<size_t> (charPrinted) >= 128) {
            std::ostringstream os;
            os << "__float128 print failure";
            throw std::runtime_error(os.str());
        }
        out << buf;
        return out;
    }
#endif

namespace Number {
#if defined (PRECISION_WEAK_FLOAT)
    constexpr int max_digits10 = std::ceil((PRECISION_WEAK_FLOAT - 8) * std::log10(2) + 1.1);
    //const int max_digits10 = std::numeric_limits<float>::max_digits10;
    const real maxprecision = powf(10.0f, max_digits10);
    const real unit = real(1.0f);
    const real zero = real(0.0f);
    const real half = real(1.f / 2.f);
#endif

#if defined (PRECISION_FLOAT)
    const real maxprecision = 1.0e-7f;
    const real unit = 1.0f;
    const real zero = 0.0f;
    const real half = 1.f / 2.f;
    const int max_digits10 = std::numeric_limits<real>::max_digits10;
#endif

#if defined (PRECISION_DOUBLE)
    const real maxprecision = 1.0e-15;
    const real unit = 1.0;
    const real zero = 0.0;
    const real half = 1. / 2.;
    const int max_digits10 = std::numeric_limits<real>::max_digits10;
#endif

#if defined (PRECISION_LONG_DOUBLE)
    const real maxprecision = 1.0e-20l;
    const real unit = 1.0l;
    const real zero = 0.0l;
    const real half = 1.l / 2.l;
    const int max_digits10 = std::numeric_limits<real>::max_digits10;
#endif

#if defined (PRECISION_QUAD)
    const real maxprecision = 1.0e-30;
    const real unit = 1.0l;
    const real zero = 0.0l;
    const real half = 1.l / 2.l;
    const int max_digits10 = FLT128_DIG;
#endif

    bool equal(real a, real b, real precision = maxprecision);
    bool relative(real a, real b, real precision = maxprecision);

    template <typename T> //inline constexpr
    int signum(T x, std::false_type) {
        return T(0) < x;
    }

    template <typename T> //inline constexpr
    int signum(T x, std::true_type) {
        return (T(0) < x) - (x < T(0));
    }

    // How to use signum: signum(-1.) = -1, signum(1.) = 1, signum(0) = 0
    template <typename T> //inline constexpr
    int signum(T x) {
        return signum(x, std::is_signed<T>());
    }
}

#endif
