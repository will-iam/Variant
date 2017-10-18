#include "timer.hpp"
#include "exception/exception.hpp"

Timer::Timer() :
    _totalSystem(0.), _totalSteady(0.),
_totalClock(0.),
_call(0.) {

}

void Timer::begin(){
    _startSystem = std::chrono::system_clock::now();
    _startSteady = steady_clock::now();
    _startClock = std::clock();
}

void Timer::end(){
    _endSystem = std::chrono::system_clock::now();
    _endSteady = steady_clock::now();
    _endClock = std::clock();

    _totalSystem += getLastSystemDuration();;

    unsigned long int steady = getLastSteadyDuration();
    _totalSteady += steady;
#if PROFILE >= 1
    _steadyList.push_back(steady);
#endif

    _totalClock += getLastClockDuration();

    _call += 1.;
}

unsigned long int Timer::getLastSystemDuration() const {
    return std::chrono::duration_cast<std::chrono::milliseconds>(_endSystem - _startSystem).count();
}

unsigned long int Timer::getLastSteadyDuration() const {
    return std::chrono::duration_cast<std::chrono::milliseconds>(_endSteady - _startSteady).count();
}

unsigned long int Timer::getLastClockDuration() const {
    return 1000.0 * (_endClock - _startClock) / CLOCKS_PER_SEC;
}

double Timer::getMeanSystemDuration() const {
    return _totalSystem / _call;
}

double Timer::getMeanSteadyDuration() const {
    return _totalSteady / _call;
}

double Timer::getMeanClockDuration() const {
    return _totalClock / _call;
}

double Timer::getTotalSystemDuration() const {
    return _totalSystem;
}

double Timer::getTotalSteadyDuration() const {
    return _totalSteady;
}

double Timer::getTotalClockDuration() const {
    return _totalClock;
}

void Timer::reportLast() {
    std::cout << Console::_bold << Console::_green << "[Timer Report System/Steady/Clock: "<< getLastSystemDuration() << ", "<< getLastSteadyDuration() << ", " << getLastClockDuration() << " ms]" << Console::_normal << std::endl;
}

void Timer::reportMean() {
    std::cout << Console::_bold << Console::_yellow << "[Timer Report System/Steady/Clock: "<< getMeanSystemDuration() << ", " << getMeanSteadyDuration() << ", " << getMeanClockDuration() << " ms]" << Console::_normal << std::endl;
}

void Timer::reportTotal() {
    std::cout << Console::_bold << Console::_pink << "[Timer Report System/Steady/Clock: "<< getTotalSystemDuration() << ", " << getTotalSteadyDuration() << ", " << getTotalClockDuration() << " ms]" << Console::_normal << std::endl;
}

