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

        unsigned long int getLastSteadyDuration() const;
        double getMeanSteadyDuration() const;
        double getTotalSteadyDuration() const;
        const std::list<unsigned long int>& getSteadyTimeList() const {return _steadyList;}
    private:
        std::chrono::time_point<steady_clock> _startSteady, _endSteady;
        double _totalSteady;
        double _call;
        std::list<unsigned long int> _steadyList;
};

#endif // TIMER_H
