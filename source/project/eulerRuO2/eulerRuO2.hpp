#ifndef EULERRUO1_HPP
#define EULERRUO1_HPP

/*!
 * @file
 * @brief Defines class of the upwind scheme for the hydrodynamics equations
 */

#include <memory>
#include "engine.hpp"
#include "number/number.hpp"
#include "exception/exception.hpp"
#include "SDShared.hpp"
#include "Domain.hpp"
#include "Quantity.hpp"

/*!
 * @brief Rusanov Order 1 scheme for the Euler hydrodynamics equations
 */
class EulerRuO2: public Engine {
  public:

    /*!
     * @brief Constructor
     */
    EulerRuO2();
    /*!
     * @brief Destructor
     */
    ~EulerRuO2();

  private:

    /*!
     * @brief Solves mass/transport equation on given
     * subdomain
     *
     * This function computes one iteration in time of
     * the transport equation on a given subdomain on
     * shared memory. Solving on a "small" portion of
     * the global domain such as a SDS leaves control to
     * the user on how the computations are done (parallel
     * threads, geometrical shape of the computed domain,
     * etc.)
     */

    real computePressure(real Ek, real E);
    real computeSoundSpeed(const real& rho, const real& P);
    void speed(const SDShared& sds, const std::map< std::string, Quantity<real>* >& quantityMap);
    void flux(const SDShared& sds, const std::map< std::string, Quantity<real>* >& quantityMap);
    void updateBoundary(const SDShared& sds, const std::map< std::string, Quantity<real>*>& quantityMap);
    void updatePressure(const SDShared& sds, const std::map< std::string, Quantity<real>*>& quantityMap);
    real minmod(real a, real b);
    /*!
     * @brief Initialize transport upwind scheme engine
     *
     * @return success/failure integer
     */
    int init() final;
    /*!
     * @brief Start iteration loop of the scheme
     *
     * @return success/failure integer
     */
    int start() final;

    int finalize() final;

    // Scheme implementation
    void computeDT();

    // Variables
    unsigned int _Nx;
    unsigned int _Ny;
    real _dx;
    real _dy;
    real _dt;
    real _t_err;
    real _last_dt;
    real _min_dt;

    // The Famous Domain
    Domain* _domain;

    /*!
     * @brief Writes solution at given time to a text file
     *
     * @param directory: folder path where output files will be written
     */
    void writeState(std::string directory);
};

#endif
