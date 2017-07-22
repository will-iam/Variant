#include "timer.hpp"
#include "exception/exception.hpp"

Timer::Timer() :
    _totalSystem(0.), _totalSteady(0.),
_totalClock(0.),
_call(0.) {

}

void Timer::start(){
    _startSystem = std::chrono::system_clock::now();
    _startSteady = steady_clock::now();
    _startClock = std::clock();
}

void Timer::end(){
    _endSystem = std::chrono::system_clock::now();
    _endSteady = steady_clock::now();
    _endClock = std::clock();

    _totalSystem += getSystemDuration();
    _totalSteady += getSteadyDuration();
    _totalClock += getClockDuration();
    _call += 1.;
}

unsigned long int Timer::getSystemDuration() const {
    return std::chrono::duration_cast<std::chrono::milliseconds>(_endSystem - _startSystem).count();
}

unsigned long int Timer::getSteadyDuration() const {
    return std::chrono::duration_cast<std::chrono::milliseconds>(_endSteady - _startSteady).count();
}

unsigned long int Timer::getClockDuration() const {
    return 1000.0 * (_endClock - _startClock) / CLOCKS_PER_SEC;
}

double Timer::getSystemMeanDuration() const {
    return _totalSystem / _call;
}

double Timer::getSteadyMeanDuration() const {
    return _totalSteady / _call;
}

double Timer::getClockMeanDuration() const {
    return _totalClock / _call;
}

void Timer::report() {
    std::cout << Console::_bold << Console::_green << "[Timer Report System/Steady/Clock: "<< getSystemDuration() << ","<< getSteadyDuration() << "," << getClockDuration() << " ms]" << Console::_normal << std::endl;
}

void Timer::mean() {
    std::cout << Console::_bold << Console::_pink << "[Timer Report System/Steady/Clock: "<< getSystemMeanDuration() << "," << getSteadyMeanDuration() << "," << getClockMeanDuration() << " ms]" << Console::_normal << std::endl;
}
