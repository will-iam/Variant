#include "exception.hpp"
#include <cstdlib>
#include <cstdarg>

void convert(std::ostream& o, const char *s) {
    while (*s) {
        if (*s == '%') {
            if (*(s + 1) == '%') {
                ++s;
            }
            else {
                throw "invalid format string: missing arguments";
            }
        }
        o << *s++;
    }
}

void title(const char *mask, ...){
        va_list argp;
        va_start(argp, mask);

        Console::color(36);
        Console::bold();
        printf("-----: ");
        Console::normal();
        Console::color(36);
        vprintf(mask, argp);
        Console::bold();
        printf(" :-----\n");
        Console::normal();
        va_end(argp);
}

void emphasize(const char *mask, ...){
        va_list argp;
        va_start(argp, mask);

        Console::color(34);
        Console::bold();
        vprintf(mask, argp);
        printf("\n");
        Console::normal();
        va_end(argp);
}

std::ostream& operator<< (std::ostream& os, const Console::Mode& mode) {
    switch (mode) {
        case Console::_normal:
            os << (char)Console::esc << "[0;24m";
            break;
        case Console::_bold:
            os << (char)Console::esc << "[1m";
            break;
        case Console::_black:
            os << (char)Console::esc << "[30m";
            break;
        case Console::_red:
            os << (char)Console::esc << "[31m";
            break;
        case Console::_green:
            os << (char)Console::esc << "[32m";
            break;
        case Console::_yellow:
            os << (char)Console::esc << "[33m";
            break;
        case Console::_blue:
            os << (char)Console::esc << "[34m";
            break;
        case Console::_pink:
            os << (char)Console::esc << "[35m";
            break;
        case Console::_cyan:
            os << (char)Console::esc << "[36m";
            break;

        default:
            break;
    }
    return os;
}
