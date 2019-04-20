#include "weakfloat.hpp"
#include <limits>
#include <iomanip>

bool test_weak_float() {
    std::cout << "     !~ ------------  Weak float " << PRECISION_WEAK_FLOAT << " test ------------ ~! " << std::endl;
    constexpr int max_digits10 = std::ceil((PRECISION_WEAK_FLOAT - 8) * std::log10(2) + 1.1);
    srand (time(NULL));
    float m = std::numeric_limits<float>::max();
    weakfloat<PRECISION_WEAK_FLOAT> w1(m);
    std::cout << std::setprecision(std::numeric_limits<float>::max_digits10);
    std::cout << "\tXX | " << std::defaultfloat << m << " | " << std::hexfloat << m << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::defaultfloat << w1 << " | " << std::hexfloat << w1 << std::endl;

    float f1 = static_cast <float> (rand() / (float)RAND_MAX);
    float f2 = static_cast <float> (rand() / (float)RAND_MAX);
    unsigned int u = rand();

    w1 = f1;
    weakfloat<PRECISION_WEAK_FLOAT> w2(f2);

    std::cout << "\tXX | " << std::defaultfloat << f1 << " | " << std::hexfloat << f1 << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::defaultfloat << w1 << " | " << std::hexfloat << w1 << std::endl;

    std::cout << "\tXX | " << std::defaultfloat << f2 << " | " << std::hexfloat << f2 << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::defaultfloat << w2 << " | " << std::hexfloat << w2 << std::endl;

    if (PRECISION_WEAK_FLOAT == 32) {
        if (w1 != f1 || w2 != f2)
            return false;

        if (w1 + w2 != f1 + f2)
            return false;

        if (w1 - w2 != f1 - f2)
            return false;

        if (w1 * w2 != f1 * f2)
            return false;

        if (w1 / w2 != f1 / f2)
            return false;

        if (w1 / u != f1 / u)
            return false;

        if (rabs(w1 * w2) != fabsf(f1 * f2))
            return false;

        if (rsqrt(w1) != sqrtf(f1))
            return false;

        if (rcos(w2) != cosf(f2))
            return false;
    }

    std::cout << "\tXX | " << std::defaultfloat << f1 << " + " << f2 << " = " << (f1 + f2) << " | " << std::hexfloat << (f1 + f2) << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::defaultfloat << w1 << " + " << w2 << " = " << (w1 + w2) << " | " << std::hexfloat << (w1 + w2) << std::endl;

    auto w3 = w1 + w2;
    if (w3.truncated() == false)
        return false;

    std::cout << "\tXX | " << std::defaultfloat << f1 << " - " << f2 << " = " << (f1 - f2) << " | " << std::hexfloat << (f1 - f2) << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::defaultfloat << w1 << " - " << w2 << " = " << (w1 - w2) << " | " << std::hexfloat << (w1 - w2) << std::endl;

    w3 = w1 - w2;
    if (w3.truncated() == false)
        return false;

    std::cout << "\tXX | " << std::defaultfloat << f1 << " * " << f2 << " = " << (f1 * f2) << " | " << std::hexfloat << (f1 * f2) << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::defaultfloat << w1 << " * " << w2 << " = " << (w1 * w2) << " | " << std::hexfloat << (w1 * w2) << std::endl;

    w3 = w1 * w2;
    if (w3.truncated() == false)
        return false;

    std::cout << "\tXX | " << std::defaultfloat << f1 << " / " << f2 << " = " << (f1 / f2) << " | " << std::hexfloat << (f1 / f2) << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::defaultfloat << w1 << " / " << w2 << " = " << (w1 / w2) << " | " << std::hexfloat << (w1 / w2) << std::endl;

    w3 = w1 / w2;
    if (w3.truncated() == false)
        return false;

    std::cout << "\tXX | " << std::defaultfloat << f1 << " / " << u << " = " << (f1 / u) << " | " << std::hexfloat << (f1 / u) << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::defaultfloat << w1 << " / " << u << " = " << (w1 / u) << " | " << std::hexfloat << (w1 / u) << std::endl;

    w3 = w1 * w2;
    if (w3.truncated() == false)
        return false;

    std::cout << std::defaultfloat;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::setprecision(max_digits10) << w1 << "(" << max_digits10 << ") | " << std::setprecision(std::numeric_limits<float>::max_digits10) << w1 << "(" << max_digits10 << ")" << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::setprecision(max_digits10) << w1 << "(" << max_digits10 << ") | " << std::setprecision(std::numeric_limits<float>::max_digits10) << w1 << "(" << max_digits10 << ")" << std::endl;

    std::cout << std::endl;

    /*
    std::cout << "float::digits = " << std::numeric_limits<float>::digits << std::endl;
    std::cout << "float::digits10 = " << std::numeric_limits<float>::digits10 << std::endl;
    std::cout << "float::max_digits10 = " << std::numeric_limits<float>::max_digits10 << std::endl;
    std::cout << "(PRECISION_WEAK_FLOAT - 8) * std::log10(2) + 1 = " << (PRECISION_WEAK_FLOAT - 8) << " * " << std::log10(2) << " + 1 = ";
    std::cout << (PRECISION_WEAK_FLOAT - 8) * std::log10(2) + 1 << std::endl;
    std::cout << "Number::max_digits10 = " << max_digits10 << std::endl;
    for (int i = 8; i < 33; ++i)
        std::cout << i << " -> " << (i - 8) * std::log10(2) + 1.1 << std::endl;
    */

    std::cout << "     !~ ------------  Weak float " << PRECISION_WEAK_FLOAT << " end  ------------ ~! " << std::endl;
    return true;
}
