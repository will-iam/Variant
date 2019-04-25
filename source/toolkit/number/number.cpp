#include <iostream>
#include <iomanip>
#include <cassert>
#include "exception/exception.hpp"
#include "number.hpp"

bool Number::equal(real a, real b, real precision) {
    if (rabs(a - b) <= precision)
        return true;
    std::cerr << "Absolute error: " << Console::_red << std::scientific << std::setprecision(max_digits10);
    std::cerr << rabs(a - b) << Console::_normal << " > ";
    std::cerr << precision << std::endl;

    std::cerr << "Relative error: " << Console::_red << std::scientific << std::setprecision(max_digits10);
    std::cerr << rabs(a / b - unit) << Console::_normal;

    return false;
}

bool Number::relative(real a, real b, real precision) {
    if (rabs(a / b - unit) <= precision)
        return true;

    std::cerr << "Relative error: " << Console::_red << std::scientific << std::setprecision(max_digits10);
    std::cerr << rabs(a / b - unit) << Console::_normal << " > " << precision << std::endl;

    std::cerr << "Absolute error: " << Console::_red << std::scientific << std::setprecision(max_digits10);
    std::cerr << rabs(a - b) << Console::_normal;

    return false;
}

void Number::fastTwoSum(real a, real b, real& c, real& d) {
    if (rabs(b) > rabs(a))
        std::swap(a,b);

    c = a + b;
    const real z = c - a;
    d = b - z;
}
