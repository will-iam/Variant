#ifndef HYDRO4X2_HPP
#define HYDRO4X2_HPP

/*!
 * @file
 * @brief Defines class of the upwind scheme for the hydrodynamics equations
 */

#include <memory>
#include <cmath>

#include "engine.hpp"
#include "number/number.hpp"
#include "exception/exception.hpp"
#include "SDShared.hpp"
#include "Domain.hpp"
#include "Quantity.hpp"

/*!
 * @brief Donor-cell scheme for the Euler hydrodynamics equations
 */
class Hydro4x2: public Engine {
  public:

    /*!
     * @brief Constructor
     */
    Hydro4x2();
    /*!
     * @brief Destructor
     */
    ~Hydro4x2();

    /*!
     * @brief Writes solution at given time to a text file
     *
     * @param directory: folder path where output files will be written
     */
    void writeState(std::string directory);
    /*!
     * @brief Writes solution at given time to the output file
     *
     * Call right after iteration of the scheme
     * without parameter to write current state
     */
    void writeState();

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

    void advection(const SDShared& sds, const std::map< std::string, Quantity<real>* >& quantityMap);
    void source(const SDShared& sds, const std::map< std::string, Quantity<real>* >& quantityMap);

  private:

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
    int _Nx;
    int _Ny;
    real _dx;
    real _dy;
    real _dt;
    real _t;

    // Physical constants
    real _gamma;

    Domain* _domain;
};

#endif
