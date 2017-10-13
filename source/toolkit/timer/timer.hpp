#ifndef TIMER_H
#define TIMER_H

#include <chrono>
#include <list>

#if __cplusplus >= 201103L
typedef std::chrono::steady_clock steady_clock;
#else
typedef std::chrono::monotonic_clock steady_clock;
#endif

class Timer {
    public:
        Timer();

        void begin();
        void end();
        void reportLast();
        void reportMean();
        void reportTotal();

        unsigned long int getLastSystemDuration() const;
        unsigned long int getLastSteadyDuration() const;
        unsigned long int getLastClockDuration() const;

        double getMeanSystemDuration() const;
        double getMeanSteadyDuration() const;
        double getMeanClockDuration() const;

        double getTotalSystemDuration() const;
        double getTotalSteadyDuration() const;
        double getTotalClockDuration() const;

        const std::list<unsigned long int>& getSteadyTimeList() const {return _steadyList;}
    private:
        std::chrono::time_point<std::chrono::system_clock> _startSystem, _endSystem;
        std::chrono::time_point<steady_clock> _startSteady, _endSteady;
        std::clock_t _startClock, _endClock;

        double _totalSystem;
        double _totalSteady;
        double _totalClock;
        double _call;

        std::list<unsigned long int> _steadyList;
};

#endif // TIMER_H
