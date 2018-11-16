#include "timer.hpp"
#include "exception/exception.hpp"
#include "timestamp/timestamp.hpp"
#include <iomanip>
#include <ostream>
#include <cmath>

Timer::Timer() :
    _startSteady(steady_clock::now()),
    _endSteady(steady_clock::now()),
    _totalSteady(0.),
    _call(0.),
    _lastTotalPrinted(0.) {
}

void Timer::begin(){
    _startSteady = steady_clock::now();
}

void Timer::end(){
    _endSteady = steady_clock::now();
    unsigned long int steady = getLastSteadyDuration();
    _totalSteady += steady;
    _steadyDeque.push_back(steady);
    _call += 1.;
}

unsigned long int Timer::getLastSteadyDuration() const {
    return std::chrono::duration_cast<std::chrono::milliseconds>(_endSteady - _startSteady).count();
}

double Timer::getMeanSteadyDuration() const {
    return _totalSteady / _call;
}

double Timer::getTotalSteadyDuration() const {
    return _totalSteady;
}


void pretty(double ms) {
   if (ms < 1000.) {
        std::cout << "0''" << ms;
    } else {
        double s = floor(ms / 1000.);
        ms -= s * 1000.;
        if (s < 60.) {
            std::cout << s << "''" << ms;
        } else {
            double m = floor(s / 60.);
            s -= m * 60.;
            if (m < 60.) {
                std::cout << m << "'" << s << "''" << ms;
            } else {
                double h = floor(m / 60.);
                m -= h * 60.;
                std::cout << h << "." << m << "'" << s << "''" << ms;
            }
        }
    } 
}

void Timer::reportLast() {
    std::cout << Console::_bold << Console::_green << "[Timer Report System/Steady/Clock: ";
    pretty(getLastSteadyDuration());
    std::cout << "]" << Console::_normal << std::endl;
}

void Timer::reportMean() {
    std::cout << Console::_bold << Console::_yellow << "[Timer Report System/Steady/Clock: ";
    pretty(getMeanSteadyDuration());
    std::cout << "]" << Console::_normal << std::endl;
}



void Timer::reportTotal() {
    double ms = getTotalSteadyDuration();
    bool stamp = (ms > 60000);
    std::cout << std::setprecision(0) << std::fixed << Console::_bold << Console::_pink;
    std::cout << "[Timer Report System/Steady/Clock: ";

    pretty(ms);
    if (_lastTotalPrinted > 0.) {
        std::cout << "(+";
        pretty(ms - _lastTotalPrinted);
        std::cout << ")";
    }

    std:: cout << "] ";
    if (stamp) {
        std::cout << Console::_blue;
        TimeStamp::printLocalTime();
    }
    std::cout << Console::_normal << std::endl;
    _lastTotalPrinted = getTotalSteadyDuration();
}
