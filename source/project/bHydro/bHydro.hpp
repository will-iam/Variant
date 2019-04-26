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
 * @brief Binary scheme for the Euler hydrodynamics equations
 */
class BHydro: public Engine {
  public:

    /*!
     * @brief Constructor
     */
    BHydro();
    /*!
     * @brief Destructor
     */
    ~BHydro();

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

    void flux(const SDShared& sds, const std::map< std::string, Quantity<real>* >& quantityMap);
    void updateBoundary(const SDShared& sds, const std::map< std::string, Quantity<real>*>& quantityMap);

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

    // Variables
    unsigned int _Nx;
    unsigned int _Ny;
    unsigned int _Nt;
    real _dx;
    real _dy;
    real _dt;

    // The Famous Domain
    Domain* _domain;

    /*!
     * @brief Writes solution at given time to a text file
     *
     * @param directory: folder path where output files will be written
     */
    void writeState(std::string directory);


    // Temporary for prototype design
    void initial_condition();
    void convolution();
    void emulate();
    void fluxion();
    const unsigned int convolution_support = 64;
    const unsigned int bunitsize = 64;
    typedef unsigned long int bline; // binary line

    bline* _mass0;
    bline* _mass1;
    bline* _uxr0;
    bline* _uxr1;
    bline* _uxl0;
    bline* _uxl1;
    size_t _bsize;

    inline void algo(const bline& mass_in, const bline& uxr_in,
        bline& mass_out, bline& uxr_out, bline& bit_from_left) const;
    void test_algo() const;
};

#endif
