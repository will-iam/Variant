#ifdef SEQUENTIAL
#include "sequential.hpp"
#else
#ifndef THREADPOOL_H
#define THREADPOOL_H

#include <iostream>
#include <vector>
#include <map>
#include <cassert>
#include <functional>
#include <atomic>

#include <mutex>
#include <thread>

#if PROFILE >= 1
#include "timer/timer.hpp"
#endif

// This can be any less than zero value
#define SYNC -1

class ThreadPool;

// Worker for thread pool object.
class Worker {
    public:
        Worker(ThreadPool &s, int id);

        void setCoworker(Worker* a, Worker* b);
        void work();
        void start(const std::string& taskListName);
        void addTask(std::string taskListName, std::function<void()> f);
    private:
        void _commonTask();

        ThreadPool& _pool;
        int _id;
        std::atomic<int> _start;
        Worker* _coworkerA;
        Worker* _coworkerB;

        std::map<std::string, std::vector< std::function<void()> > > _ownTaskVectorMap;
        std::vector< std::function<void()> >* _ownTaskVector;
        size_t _ownTaskVectorSize;
        std::mutex _ownMutex;
};

// Thread pool with single task method.
class ThreadPool {
    public:
        ThreadPool(size_t, size_t);
        ~ThreadPool();

        void addTask(std::string taskList_name, std::function<void()> f);
        void start(const std::string& taskListName);

    private:
        friend class Worker;


        std::vector< std::function<void()> >* _commonTaskVector;
        int _commonTaskVectorSize = 0;

        std::map<std::string, std::vector< std::function<void()> > > _taskListMap;
        std::map<std::string, size_t> _dispatchMap;
        std::atomic<bool> _running;
        std::atomic<int> _nextTaskCursor;
        std::atomic<size_t> _busyWorkerNumber;
        std::vector<Worker*> _workerVector;
        std::vector< std::thread > _threadVector;
        std::mutex _taskMutex;

        #if PROFILE >= 1
        Timer _timer;
        #endif
        const size_t _commonSize;
};

#endif // THREADPOOL_H
#endif // SEQUENTIAL
