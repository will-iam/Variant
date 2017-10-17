#include "threadpool.hpp"
#include "exception/exception.hpp"
#include <iostream>

// To be called by the thread.
void Worker::work() {

   
    int taskIndex(-1);
    while (true) {

        {   // acquire lock
            std::lock_guard<std::mutex> lock(_pool._taskMutex);

            if (_pool._nextTaskCursor >= 0) {

		#ifndef NDEBUG
                ++_pool._doneTasks[_pool._nextTaskCursor];
		#endif

                // get the task from the list
                taskIndex = _pool._nextTaskCursor;

                // Flag the pool to signal that one worker is computing.
                _pool._busyWorkerNumber++;
                _pool._nextTaskCursor++;
                if (_pool._nextTaskCursor.load() >= _pool._currentTaskVectorSize)
                    _pool._nextTaskCursor = SYNC;

            }
        }   // release lock

        // execute the task
        if (taskIndex >= 0) {
            (*_pool._currentTaskVector)[taskIndex]();
            taskIndex = -1;
            _pool._busyWorkerNumber--;
        }

        // If main thread, return when done
        if (_id == 0)
            if (_pool._busyWorkerNumber.load() == 0
                && _pool._nextTaskCursor.load() == SYNC) {
                _pool.wait();
                return;
            }

        // If all tasks were done (ie. end of simulation), kill thread
        if (_pool._finished)
            return;
    }
}

// the constructor just launches some amount of workers
ThreadPool::ThreadPool(size_t nThreads):
    _ownWorker(*this, 0),
    _workerVectorSize(nThreads - 1),
    _nextTaskCursor(-1),
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
void ThreadPool::addTask(std::string taskListName, std::function<void()> f) {

    _taskListMap[taskListName].push_back(f);
}

void ThreadPool::start(std::string taskListName) {

    // This launches tasks for all threads
    _currentTaskVector = &(_taskListMap[taskListName]);
    _currentTaskVectorSize = _currentTaskVector->size();

#ifndef NDEBUG
    _doneTasks.clear();
    _doneTasks.resize(_currentTaskVectorSize);
#endif

    _nextTaskCursor = 0;

#if PROFILE >= 1
    _timer.start();
#endif

    _ownWorker.work();

#if PROFILE >= 1
    _timer.end();
#endif
    wait();

#ifndef NDEBUG
    // Check if all tasks were done
    for (const auto& it: _doneTasks)
        assert(it == 1);
#endif
}
