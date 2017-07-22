#ifndef TIMER_H
#define TIMER_H

#include <chrono>

#if __cplusplus >= 201103L
typedef std::chrono::steady_clock steady_clock;
#else
typedef std::chrono::monotonic_clock steady_clock;
#endif

class Timer {
    public:
        Timer();

        void start();
        void end();
        void report();
        void mean();
        unsigned long int getSystemDuration() const;
        unsigned long int getSteadyDuration() const;
        unsigned long int getClockDuration() const;

        double getSystemMeanDuration() const;
        double getSteadyMeanDuration() const;
        double getClockMeanDuration() const;

    private:
        std::chrono::time_point<std::chrono::system_clock> _startSystem, _endSystem;
        std::chrono::time_point<steady_clock> _startSteady, _endSteady;
        std::clock_t _startClock, _endClock;

        double _totalSystem;
        double _totalSteady;
        double _totalClock;
        double _call;
};

#endif // TIMER_H
