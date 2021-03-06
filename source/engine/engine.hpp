#ifndef ENGINE_HPP
#define ENGINE_HPP

/*!
 * @file:
 *
 * @brief define the base Engine class for a numerical scheme
 */
#include <string>
#include <vector>

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
    virtual int start() = 0;

    virtual int finalize() = 0;

    /*!
     * @brief Set scheme options : final time and Courant-Friedrichs-Levy
     * condition.
     *
     * @param T final time
     * @param CFL Courant-Friedrichs-Levy condition
     */
    void setOptions(real T, real CFL, real _gamma);

    void updateDomainUmax();
    void updateDomainUxmax();
    void updateDomainUymax();
    real reduceMin(const real& v);

  protected:
    void printStatus(bool force = false);
    
    std::string _initpath;
    std::string _outputpath;
    int _testFlag;
    int _dryFlag;

    real _t, _T;
    real _CFL;
    real _gamma;

    // Members for profiling
    Timer _timerIteration;
    Timer _timerComputation;
    Timer _timerGlobal;

    int _MPI_rank;

    std::vector<real> _SDS_uxmax;
    std::vector<real> _SDS_uymax;
    real _SDD_uxmax;
    real _SDD_uymax;
    real _Domain_uxmax;
    real _Domain_uymax;
    unsigned int _nIterations;
  private:
    int iPrintStatus = 0;
};

#endif
