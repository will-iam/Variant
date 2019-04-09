#include <iostream>
#include <iomanip>
#include <cassert>
#include "exception/exception.hpp"
#include "number.hpp"
#include "console/console.hpp"

bool Number::equal(real a, real b, real precision) {
    if (vabs(a - b) <= precision) 
        return true;
    std::cerr << "Absolute error: " << Console::_red << std::scientific << std::setprecision(max_digits10);
    std::cerr << vabs(a - b) << Console::_normal << " > ";
    std::cerr << precision << std::endl;

    std::cerr << "Relative error: " << Console::_red << std::scientific << std::setprecision(max_digits10);
    std::cerr << vabs(a / b - unit) << Console::_normal;

    return false;
}

bool Number::relative(real a, real b, real precision) {
    if (vabs(a / b - unit) <= precision) 
        return true;

    std::cerr << "Relative error: " << Console::_red << std::scientific << std::setprecision(max_digits10);
    std::cerr << vabs(a / b - unit) << Console::_normal << " > " << precision << std::endl;

    std::cerr << "Absolute error: " << Console::_red << std::scientific << std::setprecision(max_digits10);
    std::cerr << vabs(a - b) << Console::_normal;

    return false;
}