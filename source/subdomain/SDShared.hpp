#ifndef SDSHARED_HPP
#define SDSHARED_HPP

/*!
 * @file
 *
 * @brief Defines class for subdomains on shared memory (SDS)
 */

#include "CoordConverter.hpp"
#include "Quantity.hpp"
#include "engine.hpp"

#include <vector>
#include <utility>
#include <map>
#include <functional>

class SDShared;

typedef std::function< void(const SDShared&, const std::map< std::string, Quantity<real>* >&) > eqType;

/*!
 * @brief Subdomain on shared memory (SDS)
 *
 * Defines a subdomain on shared memory. Since the data
 * is stored as one block on the SDD, a SDS is only an
 * array of 2D-coordinates referencing to cells of the SDD.
 */
class SDShared: public std::vector< std::pair<int,int> > {
  public:

    /*!
     * @brief Copy constructor based on vector of coords
     */
    SDShared(const std::vector< std::pair<int, int> >& coords,
            const CoordConverter& coordConverter,
            unsigned int index);

    /*!
     * @brief Returns SDS id
     *
     * @return id of SDS
     */
    inline unsigned int getId() const { return _id; }

    /*!
     * exec equation on SDS
     * to be added as thread task
     */
    void execEquation(eqType& eqFunc,
            const std::map< std::string, Quantity<real>* >& quantityMap);

    /*!
     * @brief updates boundary of all SDDs according to their
     * values on reference cells on other SDDs, for a given quantity.
     *
     * /!\ This has to be called AFTER updating overlap cells, since boundary        // Updating umax for computation of the next dt
        _umax = std::max(_umax, std::abs(ux.get(0, i, j)));
        _umax = std::max(_umax, std::abs(uy.get(0, i, j)));

     * cells may be updated with values on overlap cells.
     * The boolean parameter is optional and can be used for some physical
     * quantities that require the Neumann boundary condition to be opposite.
     *
     * @param quantityName name of quantity to update
     * @param changeNeumannToOpposite if true, this changes the value into its
     * opposite on cells that have Neumann BC.
     */
    void updateBoundaryCells(Quantity<real>* quantity, bool changeNeumannToOpposite = false) const;

    /*!
     * @brief Updates Neumann boundary cells of SDD according to values
     * stored in memory.
     *
     * This does not require communication with other SDDs
     * as long as overlap cells were update before.
     *
     * @param quantityName str. name of quantity to update
     * @param changeToOpposite change to opposite value of reference
     * according to value. This depends on the boundary and is useful for
     * quantities traditionnally defined on edges.
     */
    void updateNeumannCells(Quantity<real>* quantity, bool changeToOpposite = false) const;

    /*!
     * @brief Updates Dirichlet boundary cells of SDD according to values stored
     * in memory.
     *
     * @param quantityName str. name of quantity to update
     */
    void updateDirichletCells(Quantity<real>* quantity) const;


    void addDirichletCell(std::pair < std::pair<int, int>, real > d);
    void addNeumannCell(std::pair< std::pair<int, int>, std::pair<int, int> > n);

    size_t getNumberBoundaryCells() const { return _neumannCellMap.size() + _dirichletCellMap.size(); }

    inline unsigned int convert(int coordX, int coordY) const {return _coordConverter.convert(coordX, coordY);}
  private:

    /*!
     * own coordinates converter (should be a copy of
     * the converter of the parent SDD
     */
    CoordConverter _coordConverter;
    unsigned int _id;

    /*!
     * mapping between coords of cells on which are
     * set Dirichlet boundary conditions, and the
     * values of the BC
     */
    std::map< std::pair<int, int>, real > _dirichletCellMap;

    /*!
     * mapping between coords of cells on which are set
     * Neumann boundary conditions, and the associated
     * cells
     */
    std::map< std::pair<int, int>, std::pair<int, int> > _neumannCellMap;


};

#endif

