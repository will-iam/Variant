#include "timer.hpp"
#include "exception/exception.hpp"

Timer::Timer() :
    _totalSteady(0.),
    _call(0.) {
}

void Timer::begin(){
    _startSteady = steady_clock::now();
}

void Timer::end(){
    _endSteady = steady_clock::now();
    unsigned long int steady = getLastSteadyDuration();
    _totalSteady += steady;
    _steadyList.push_back(steady);
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

void Timer::reportLast() {
    std::cout << Console::_bold << Console::_green << "[Timer Report System/Steady/Clock: " << getLastSteadyDuration() << " ms]" << Console::_normal << std::endl;
}

void Timer::reportMean() {
    std::cout << Console::_bold << Console::_yellow << "[Timer Report System/Steady/Clock: " << getMeanSteadyDuration() << " ms]" << Console::_normal << std::endl;
}

void Timer::reportTotal() {
    std::cout << Console::_bold << Console::_pink << "[Timer Report System/Steady/Clock: " << getTotalSteadyDuration() << " ms]" << Console::_normal << std::endl;
}
