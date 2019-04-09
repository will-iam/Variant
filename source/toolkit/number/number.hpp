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

#if defined(PRECISION_FLOAT)
    typedef float real;
    typedef std::numeric_limits<float> oss_nl;
    constexpr auto rabs = fabsf;
    inline void stor(std::string tmpStr, float& target) {
        target = std::stof(tmpStr);
    }
    #ifndef SEQUENTIAL
    const MPI_Datatype MPI_REALTYPE = MPI_FLOAT;
    #endif
#endif

#if defined(PRECISION_DOUBLE)
    typedef double real;
    typedef std::numeric_limits<double> oss_nl;
    constexpr auto rabs = fabs;
    inline void stor(std::string tmpStr, double& target) {
        target = std::stod(tmpStr);
    }
    #ifndef SEQUENTIAL
    const MPI_Datatype MPI_REALTYPE = MPI_DOUBLE;
    #endif
#endif

#if defined(PRECISION_LONG_DOUBLE)
    typedef long double real;
    typedef std::numeric_limits<long double> oss_nl;
    constexpr auto rabs = fabsl;
    inline void stor(std::string tmpStr, long double& target) {
        target = std::stold(tmpStr);
    }
    #ifndef SEQUENTIAL
    const MPI_Datatype MPI_REALTYPE = MPI_LONGDOUBLE;
    #endif
#endif

#if defined(PRECISION_QUAD)
    extern "C" {
        #include <quadmath.h>
    }
    typedef __float128 real;
    typedef std::numeric_limits<__float128> oss_nl;
    constexpr auto rabs = fabsq;
    inline void stor(std::string tmpStr, __float128& target) {
        target = strtoflt128 (tmpStr.c_str(), NULL);
    }

    #ifndef SEQUENTIAL
    const MPI_Datatype MPI_REALTYPE = MPI_REAL4;
    #endif

    inline std::ostream& operator<< (std::ostream& out, const __float128& x) {
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
#if defined (PRECISION_FLOAT)
    const real maxprecision = 1.0e-7f;
    const real unit = 1.0f;
    const real zero = 0.0f;
    const int max_digits10 = std::numeric_limits<real>::max_digits10;
#endif

#if defined (PRECISION_DOUBLE)
    const real maxprecision = 1.0e-15;
    const real unit = 1.0;
    const real zero = 0.0;
    const int max_digits10 = std::numeric_limits<real>::max_digits10;
#endif

#if defined (PRECISION_LONG_DOUBLE)
    const real maxprecision = 1.0e-20l;
    const real unit = 1.0l;
    const real zero = 0.0l;
    const int max_digits10 = std::numeric_limits<real>::max_digits10;
#endif

#if defined (PRECISION_QUAD)
    const real maxprecision = 1.0e-30;
    const real unit = 1.0;
    const real zero = 0.0;
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
