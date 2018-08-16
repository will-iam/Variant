#ifndef SEQUENTIAL_H
#define SEQUENTIAL_H

#include <iostream>
#include <vector>
#include <map>
#include <cassert>
#include <functional>

// Thread pool with single task method.
class ThreadPool {
    public:
        ThreadPool(size_t, size_t) {}
        ~ThreadPool() {}

        void addTask(std::string taskListName, std::function<void()> f) {
            _taskListMap[taskListName].push_back(f);
        }

        void start(const std::string& taskListName) {
            std::vector< std::function<void()> >* pTaskVector =  &(_taskListMap[taskListName]);
            for (size_t i = 0; i < pTaskVector->size(); ++i)
                (*pTaskVector)[i]();
        }
    private:
        std::map<std::string, std::vector< std::function<void()> > > _taskListMap;
};

#endif // THREADPOOL_H
