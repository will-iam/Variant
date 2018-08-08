#ifndef NUMBER_HPP
#define NUMBER_HPP

#include <cmath>
#include <random>
#include <limits>
#ifndef SEQUENTIAL
#include <mpi.h>
#endif

#define positiveModulo(a, b) (((a) % (b)) + (b)) % (b)

#if defined(PRECISION_FLOAT)
typedef float real;
typedef std::numeric_limits<float> oss_nl;
    #ifndef SEQUENTIAL
    const MPI_Datatype MPI_REALTYPE = MPI_FLOAT;
    #endif
#endif

#if defined(PRECISION_DOUBLE)
typedef double real;
typedef std::numeric_limits<double> oss_nl;
    #ifndef SEQUENTIAL
    const MPI_Datatype MPI_REALTYPE = MPI_DOUBLE;
    #endif
#endif

#if defined(PRECISION_LONG_DOUBLE)
typedef long double real;
typedef std::numeric_limits<long double> oss_nl;
    #ifndef SEQUENTIAL
    const MPI_Datatype MPI_REALTYPE = MPI_LONGDOUBLE;
    #endif
#endif


namespace Number {

#if defined (PRECISION_FLOAT)
    const real maxprecision = 1.0e-7f;
    const int digitsize = -logf(maxprecision) / logf(10.f) + 1;
    const real unit = 1.0f;
    const real zero = 0.0f;
#endif

#if defined (PRECISION_DOUBLE)
    const real maxprecision = 1.0e-15;
    const int digitsize = -logf(maxprecision) / logf(10.) + 1;
    const real unit = 1.0;
    const real zero = 0.0;
#endif

#if defined (PRECISION_LONG_DOUBLE)
    const real maxprecision = 1.0e-20l;
    const int digitsize = -logf(maxprecision) / logf(10.l) + 1;
    const real unit = 1.0l;
    const real zero = 0.0l;
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
