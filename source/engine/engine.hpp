#ifndef ENGINE_HPP
#define ENGINE_HPP

/*!
 * @file:
 *
 * @brief define the base Engine class for a numerical scheme
 */
#include <string>
#include <mpi.h>

#include "number/number.hpp"
#include "timer/timer.hpp"

/*!
 * @brief base class used to program a numerical scheme
 */
class Engine {

  public:

    /*!
     * @brief Constructor
     */
    Engine() {};
    /*!
     * @brief Destructor
     */
    ~Engine() {};

    /*!
     * @brief Main function of program, calls init and start function of the
     * inherited engine.
     */
    int main(int argc, char** argv);

    /*!
     * @brief Virtual init function. Program here all necessary init procedures.
     */
    virtual int init() = 0;
    /*!
     * @brief Virtual start function. Program here the iterations of the scheme.
     */
    virtual	int start() = 0;

    /*!
     * @brief Set scheme options : final time and Courant-Friedrichs-Levy
     * condition.
     *
     * @param T final time
     * @param CFL Courant-Friedrichs-Levy condition
     */
    void setOptions(real T, real CFL);

    void updateGlobalUxmax();
    void updateGlobalUymax();

  protected:
    std::string _initpath;
    std::string _outputpath;

    real _T;
    real _CFL;

    Timer _timer;

    int _MPI_rank;
    real _local_uxmax;
    real _local_uymax;
    real _global_uxmax;
    real _global_uymax;
};

#endif
