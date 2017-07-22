#include "threadpool.hpp"
#include "exception/exception.hpp"
#include <iostream>

// To be called by the thread.
void Worker::work() {

    std::function<void()> task;
    while (true) {

        {   // acquire lock
            std::unique_lock<std::mutex> lock(_pool._taskMutex);

            if (_pool._nextTaskCursor >= _pool._taskVector.size()) {
                //std::cout << _pool._taskVector.size() << std::endl;
                return;
            }

            // Flag the pool to signal that one worker is computing.
            _pool._busyWorkerNumber += 1;
            assert(_pool._busyWorkerNumber > 0 && _pool._busyWorkerNumber <= _pool._workerVectorSize + 1);

            // get the task from the list
            task = _pool._taskVector[_pool._nextTaskCursor];
            ++_pool._nextTaskCursor;
        }   // release lock

        // execute the task
        task();
        _pool._busyWorkerNumber -= 1;
    }
}

// the constructor just launches some amount of workers
ThreadPool::ThreadPool(size_t nThreads):
    _workerVectorSize(nThreads - 1),
    _nextTaskCursor(_workerVector.max_size() + 1),
    _ownWorker(*this) {

    _busyWorkerNumber = 0;

    for(size_t i = 0; i < _workerVectorSize; ++i) {
        _workerVector.push_back(std::thread(&Worker::work, Worker(*this)));
    }
}

// the destructor joins all threads
ThreadPool::~ThreadPool() {
    
#if PROFILE >= 1
    _timer.report();
#endif
    // join them
    for (auto it = _workerVector.begin(); it != _workerVector.end(); ++it) {
        if (it->joinable())
            it->join();
    }
}

// add new work item to the pool
void ThreadPool::addTask(std::function<void()> f) {

    _taskVector.push_back(f);
}

void ThreadPool::start() {
    
    // This launches tasks for all threads
    _nextTaskCursor = 0;
#if PROFILE >= 1
    _timer.start();
#endif
    _ownWorker.work();
#if PROFILE >= 1
    _timer.end();
#endif
    wait();
}

