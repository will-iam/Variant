#ifndef TRANSPORT_UPWIND_HPP
#define TRANSPORT_UPWIND_HPP

/*!
 * @file
 * @brief Defines class of the upwind scheme for the transport equation
 */

#include <memory>
#include <cmath>
#include <mpi.h>

#include "engine.hpp"
#include "number/number.hpp"
#include "exception/exception.hpp"
#include "SDShared.hpp"
#include "Domain.hpp"
#include "Quantity.hpp"

/*!
 * @brief Upwind scheme for the transport equation
 *
 * We solve the transport equation
 * \f$\partial_t \rho + u \nabla \cdot \rho = 0\f$
 * for \f$u\f$ constant speed
 *
 * The upwind scheme is a scheme of order one that
 * is stable under CFL condition, although very
 * diffusive.
 */
class TransportUpwind: public Engine {
  public:

    /*!
     * @brief Constructor
     */
    TransportUpwind();
    /*!
     * @brief Destructor
     */
    ~TransportUpwind();

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
     //void massEquation(int i, int j,
     //       std::map< std::string, Quantity<real>* > quantityMap);

    void massEquation(const SDShared& sds,
            std::map< std::string, Quantity<real>* > quantityMap);

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

    // Scheme implementation
    void computeDT();

    /*!
     * @brief Applies boundary conditions on current
     * mass data according to input received
     * by the engine
     */
    //void boundaryConditionsOnMass();

    /*
     * @brief Applies Dirichlet boundary
     * conditions on the border:
     * \f$ \rho = \text{value} \f$ 
     */
    //void dirichlet(Quantity<real>& rho, int i, int j,
    //        real value, int onNext);
    /*
     * @brief Applies Neumann
     * boundary conditions on the border:
     * \f$ \frac{\partial \rho}{\partial n} = 0 \f$
     */
    //void neumann(Quantity<real>& rho, int i, int j,
    //        int onNext);
    /*
     * @brief Applies periodic
     * boundary conditions on the border:
     * \f$ \rho_{\text{left}} = \rho_{\text{right}}\f$ and
     * \f$ \rho_{\text{top}} = \rho_{\text{bottom}}\f$
     */
    //void periodic(Quantity<real>& rho, int i, int j,
    //        int onNext);

    /*!
     * @brief Applies boundary conditions on the
     * speed, according to the boundary conditions on
     * the mass
     */
    void boundaryConditionsOnSpeed();

    // Variables
    //real _lx;
    //real _ly;
    int _Nx;
    int _Ny;
    real _dx;
    real _dy;
    real _dt;
    real _t;

    Domain* _domain;
};

#endif

