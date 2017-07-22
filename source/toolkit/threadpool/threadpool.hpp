#ifndef THREADPOOL_H
#define THREADPOOL_H

#include <thread>
#include <mutex>
#include <condition_variable>
#include <deque>
#include <vector>
#include <cassert>
/*#ifdef __GXX_EXPERIMENTAL_CXX0X__
    #include <cstdatomic>
#elif __cplusplus >= 201103L*/
    #include <atomic>
//#endif

#if PROFILE >= 1
#include "timer/timer.hpp"
#endif

class ThreadPool;

// Worker for thread pool object.
class Worker {
    public:
        Worker(ThreadPool &s) : _pool(s) { }
        void work();
    private:
        ThreadPool& _pool;
};

// Thread pool with single task method.
class ThreadPool {
    public:
        ThreadPool(size_t);
        ~ThreadPool();

        void wait() const {

            while (_busyWorkerNumber.load() > 0) {}
        }

        void addTask(std::function<void()> f);

        void start();

        /// Return the actual queue size.
        size_t workerSize() const { return _workerVectorSize; }

    private:
        friend class Worker;

        // need to keep track of threads so we can join them
        Worker _ownWorker;
        std::vector< std::thread > _workerVector;
        const size_t _workerVectorSize;
        std::atomic<size_t> _busyWorkerNumber;

        std::vector< std::function<void()> > _taskVector;
        size_t _nextTaskCursor;

        // synchronization
        mutable std::mutex _taskMutex;

#if PROFILE >= 1
        Timer _timer;
#endif
        
};

#endif // THREADPOOL_H
