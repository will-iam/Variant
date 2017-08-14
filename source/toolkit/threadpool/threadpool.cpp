#include "threadpool.hpp"
#include "exception/exception.hpp"
#include <iostream>

// To be called by the thread.
void Worker::work() {

    std::function<void()> task;
    while (true) {
        
        {   // acquire lock
            std::lock_guard<std::mutex> lock(_pool._taskMutex);

            if (_pool._nextTaskCursor >= 0) {

                // Flag the pool to signal that one worker is computing.
                //assert(_pool._busyWorkerNumber > 0 && _pool._busyWorkerNumber <= _pool._workerVectorSize + 1);

                // get the task from the list
                task = _pool._currentTaskList->operator[](_pool._nextTaskCursor);
                _pool._busyWorkerNumber++;
                _pool._nextTaskCursor++;
                //std::cout << _pool._nextTaskCursor << " ";
                if (_pool._nextTaskCursor.load() >= _pool._currentTaskList->size())
                    _pool._nextTaskCursor = SYNC;

            }
        }   // release lock

        // execute the task
        if (task) {
            task();
            task = std::function<void()>();
            _pool._busyWorkerNumber--;
        }

        // If main thread, return when done
        if (_id == 0)
            if (_pool._busyWorkerNumber.load() == 0
                && _pool._nextTaskCursor.load() == SYNC) 
                return;

        // If all tasks were done (ie. end of simulation), kill thread
        if (_pool._finished)
            return;
    }
}

// the constructor just launches some amount of workers
ThreadPool::ThreadPool(size_t nThreads):
    _workerVectorSize(nThreads - 1),
    _nextTaskCursor(-1),
    _ownWorker(*this, 0),
    _finished(false) {

    _busyWorkerNumber = 0;

    for(size_t i = 0; i < _workerVectorSize; ++i) {
        _workerVector.push_back(std::thread(&Worker::work, Worker(*this, i + 1)));
    }
}

// the destructor joins all threads
ThreadPool::~ThreadPool() {
    
#if PROFILE >= 1
    _timer.report();
#endif
    // join them
    _finished = true;
    for (auto it = _workerVector.begin(); it != _workerVector.end(); ++it) {
        if (it->joinable())
            it->join();
    }
}

// add new work item to the pool
void ThreadPool::addTask(std::string taskList_name, std::function<void()> f) {

    _taskList_map[taskList_name].push_back(f);
}

void ThreadPool::start(std::string taskList_name) {
    
    // This launches tasks for all threads
    //_doneTasks.resize(_taskVector.size());
    //std::fill(_doneTasks.begin(), _doneTasks.end(), 0);
    //

    // Go !
    _currentTaskList = &(_taskList_map[taskList_name]);
    _nextTaskCursor = 0;
#if PROFILE >= 1
    _timer.start();
#endif
    _ownWorker.work();
#if PROFILE >= 1
    _timer.end();
#endif
    wait();

    // Check if all tasks were done
    /*
    for (const auto& it: _doneTasks)
        assert(it == 1);
    getchar();
    */
}

