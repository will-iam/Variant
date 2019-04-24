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
#include <unordered_map>
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
     * /!\ This has to be called AFTER updating overlap cells, since boundary
        _umax = std::max(_umax, std::abs(uy.get(0, i, j)));

     * cells may be updated with values on overlap cells.
     * The boolean parameter is optional and can be used for some physical
     * quantities that require the Neumann boundary condition to be opposite.
     *
     * @param quantityName name of quantity to update
     * @param changeNeumannToOpposite if true, this changes the value into its
     * opposite on cells that have Neumann BC.
     */
    void updateBoundaryCells(Quantity<real>* quantity, const real& t) const;

    void addTimeVaryingCell(std::pair < std::pair<int, int>, std::map<std::string, real> > d);
    void addDirichletCell(std::pair < std::pair<int, int>, std::map<std::string, real> > d);
    void addNeumannCell(std::pair< std::pair<int, int>, std::pair< std::pair<int, int>, std::map<std::string, real> > > n);
    size_t getNumberBoundaryCells() const {
        size_t s(0);
        for (auto m : _neumannCellMap)
             s += m.second.size();

        for (auto m : _dirichletCellMap)
            s += m.second.size();

        return s;
    }

    inline unsigned int convert(int coordX, int coordY) const {return _coordConverter.convert(coordX, coordY);}

    void setBufferPos(unsigned int sddId, size_t pos) { _bufferStartPos[sddId] = pos; }
    size_t getOverlapCellNumber(unsigned int sddId) const;
    void addOverlapCell(unsigned int sddId, size_t sendIndex, size_t recvIndex);

    void copyOverlapCellIn(const std::map< std::string, Quantity<real>* >& quantityMap, const std::unordered_map<unsigned int, real* >& buffer) const;
    void copyOverlapCellFrom(const std::map< std::string, Quantity<real>* >& quantityMap, const std::unordered_map<unsigned int, real* >& buffer) const;

  private:
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
      void updateNeumannCells(Quantity<real>* quantity) const;

      /*!
       * @brief Updates Dirichlet boundary cells of SDD according to values stored
       * in memory.
       *
       * @param quantityName str. name of quantity to update
       */
      void updateDirichletCells(Quantity<real>* quantity) const;

      /*!
       * @brief Updates Dirichlet boundary cells of SDD according to values stored
       * in memory.
       *
       * @param quantityName str. name of quantity to update
       */
      void updateTimeVaryingCells(Quantity<real>* quantity, const real& t) const;

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
    std::map<std::string, std::unordered_map< size_t, real >> _dirichletCellMap;

    /*!
     * mapping between coords of cells on which are
     * set time varying boundary conditions, and the
     * values of one parameter.
     */
    std::map<std::string, std::unordered_map< size_t, real >> _timeVaryingCellMap;

    /*!
     * mapping between coords of cells on which are set
     * Neumann boundary conditions, and the associated
     * cells
     */
    std::map<std::string, std::unordered_map< size_t, std::pair<size_t, real>>> _neumannCellMap;

    /* Buffer start position */
    std::unordered_map<unsigned int, size_t > _bufferStartPos;
    std::unordered_map<unsigned int, std::vector<size_t> > _sendIndexMap;
    std::unordered_map<unsigned int, std::vector<size_t> > _recvIndexMap;
};

#endif
