#ifndef THREADPOOL_H
#define THREADPOOL_H

#include <iostream>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <vector>
#include <map>
#include <cassert>
/*#ifdef __GXX_EXPERIMENTAL_CXX0X__
    #include <cstdatomic>
#elif __cplusplus >= 201103L*/
    #include <atomic>
//#endif

#if PROFILE >= 1
#include "timer/timer.hpp"
#endif

// This can be any less than zero value
#define SYNC -1
//#define END -2

class ThreadPool;

// Worker for thread pool object.
class Worker {
    public:
        Worker(ThreadPool &s, int id) : _pool(s), _id(id) { }
        void work();
    private:
        ThreadPool& _pool;
        int _id;
};

// Thread pool with single task method.
class ThreadPool {
    public:
        ThreadPool(size_t);
        ~ThreadPool();

        void wait() const {

            while (_nextTaskCursor != SYNC || _busyWorkerNumber.load() > 0) {}
        }

        void addTask(std::string taskList_name, std::function<void()> f);
        void setNewTaskList();

        void start(std::string taskList_name);

        /// Return the actual queue size.
        size_t workerSize() const { return _workerVectorSize; }

    private:
        friend class Worker;

        // need to keep track of threads so we can join them
        Worker _ownWorker;
        std::vector< std::thread > _workerVector;
        const size_t _workerVectorSize;
        std::atomic<size_t> _busyWorkerNumber;

        std::map<std::string, std::vector< std::function<void()> > > _taskList_map;
        std::vector< std::function<void()> > _currentTaskList;
        std::atomic<int> _nextTaskCursor;
        bool _finished;

        // synchronization
        std::mutex _taskMutex;

#if PROFILE >= 1
        Timer _timer;
#endif
        
};

#endif // THREADPOOL_H
