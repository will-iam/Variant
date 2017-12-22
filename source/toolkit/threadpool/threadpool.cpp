#include "threadpool.hpp"
#include "exception/exception.hpp"
#include <iostream>

Worker::Worker(ThreadPool &s, int id) : _pool(s), _id(id), _start(0), _coworkerA(nullptr) , _coworkerB(nullptr) { }

void Worker::setCoworker(Worker* a, Worker* b) {_coworkerA = a; _coworkerB = b;}

void Worker::addTask(std::string taskListName, std::function<void()> f) {

    _ownTaskVectorMap[taskListName].push_back(f);
}

void Worker::start(const std::string& taskListName) {
    assert(_start == 0);

    if (_coworkerA != nullptr)
        _coworkerA->start(taskListName);

    if (_coworkerB != nullptr)
        _coworkerB->start(taskListName);

    _ownTaskVector = &(_ownTaskVectorMap[taskListName]);
    _ownTaskVectorSize = _ownTaskVector->size();
    ++_start;
}

// To be called by the thread.
void Worker::_commonTask() {
    int taskIndex(SYNC);
    while (true) {
        { // acquire lock
            std::lock_guard<std::mutex> lock(_pool._taskMutex);
            
            // There is no common work available.
            if (_pool._nextTaskCursor.load() == SYNC)
                return;

            // get the task from the list
            taskIndex = _pool._nextTaskCursor;

            // Flag the pool to signal that one worker is computing.
            ++_pool._nextTaskCursor;
            if (_pool._nextTaskCursor.load() >= _pool._commonTaskVectorSize)
                _pool._nextTaskCursor = SYNC;

        } // release lock

        // execute the task
        if (taskIndex >= 0) {
            (*_pool._commonTaskVector)[taskIndex]();
            taskIndex = SYNC;
        }
    }
}

void Worker::work() {

    // If all tasks were done (ie. end of simulation), kill thread
    while (_pool._running) {

        if (_start.load() > 0) {

            // execute all the tasks
            for (size_t i = 0; i < _ownTaskVectorSize; ++i)
                (*_ownTaskVector)[i]();

            // Now common part
            _commonTask();

            // Unflag the pool to signal that the worker is free.
            --_pool._busyWorkerNumber;

            // Job done
            --_start;
        }

        // If main thread, return when done (split to check which one is blocking the other in Vtune)
        if (_id == 0)
            if (_pool._busyWorkerNumber.load() == 0)
                if( _pool._nextTaskCursor.load() == SYNC)
                    return;
    }
}

// the constructor just launches some amount of workers
ThreadPool::ThreadPool(size_t nThreads, size_t commonSize):
    _running(true),
    _nextTaskCursor(-1),
    _busyWorkerNumber(0),
    _workerVector(nThreads),
    _commonSize(commonSize) {

    for(size_t i = 0; i < _workerVector.size(); ++i)
       _workerVector[i] = new Worker(*this, i);

    // Create coworker tree
    for(size_t i = 0, cursor = 1; i < _workerVector.size() && cursor < _workerVector.size(); ++i) {
        Worker* a = _workerVector[cursor];            
        ++cursor;

        Worker* b = nullptr;
        if (cursor < _workerVector.size())
            b = _workerVector[cursor];        
        ++cursor;

       _workerVector[i]->setCoworker(a, b);
    }

    size_t threadVectorSize(nThreads - 1);
    for(size_t i = 0; i < threadVectorSize; ++i)
        _threadVector.push_back(std::thread(&Worker::work, _workerVector[i+1]));
}

// the destructor joins all threads
ThreadPool::~ThreadPool() {

    #if PROFILE >= 1
    _timer.report();
    #endif

    // join them
    _running = false;
    for (auto it = _threadVector.begin(); it != _threadVector.end(); ++it) {
        if (it->joinable())
            it->join();
    }

    for(size_t i = 0; i < _workerVector.size(); ++i)
       delete _workerVector[i];
}

// add new work item to the pool
void ThreadPool::addTask(std::string taskListName, std::function<void()> f) {

    if (_dispatchMap.find(taskListName) == _dispatchMap.end())
        _dispatchMap[taskListName] = 0;

    size_t dispatch = _dispatchMap[taskListName];

    // Put it in the common task list.
    if (dispatch < _commonSize) {
        _taskListMap[taskListName].push_back(f);
    } else {
        // Pick a worker
        size_t w = (dispatch + _commonSize) % _workerVector.size();
        //size_t w = 1 + (dispatch + _commonSize) % (_workerVector.size() - 1);
        _workerVector[w]->addTask(taskListName, f);
    }

    ++_dispatchMap[taskListName];
}

void ThreadPool::start(const std::string& taskListName) {
    #if PROFILE >= 1
    _timer.start();
    #endif

    // This defines the common tasks
    //if (_taskListMap.find(taskListName) != _taskListMap.end()) {
    if (_commonSize > 0) {
        _commonTaskVector = &(_taskListMap[taskListName]);
        _commonTaskVectorSize = _commonTaskVector->size();
        _nextTaskCursor = 0;
    }

    // Flag the pool to signal that all workers are computing (they will try at least).
    _busyWorkerNumber = _workerVector.size();

    // Start the work of each thread
    _workerVector[0]->start(taskListName);

    // Start master worker (the worker of this 'master' thread).
    _workerVector[0]->work();
    
    #if PROFILE >= 1
    _timer.end();
    #endif
}
