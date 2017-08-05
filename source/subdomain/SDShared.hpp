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

typedef std::function< void(const SDShared&, std::map< std::string, Quantity<real>* >) > eqType;

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
     * @brief Constructor (rectangle-shaped SDS)
     *
     * @param bottomLeft_X : X-coord of the bottom-left corner
     * @param bottomLeft_Y : Y-coord of the bottom-left corner
     * @param sizeX : width of the SDS
     * @param sizeY : height of the SDS
     * @param coordConverter : reference coordConverter
     * of which the SDS will own a copy (should be the
     * coordConverter of the parent SDS)
     */
    SDShared(unsigned int bottomLeft_X, unsigned int bottomLeft_Y,
             unsigned int sizeX, unsigned int sizeY,
             const CoordConverter & coordConverter);

    /*!
     * @brief Copy constructor based on vector of coords
     */
    SDShared(const std::vector< std::pair<int, int> >& coords,
            const CoordConverter& coordConverter,
            unsigned int index);

    /*!
     * @brief Gets memory index corresponding to given
     * 2D coordinates. Calls the convert method of the
     * coord converter of the SDS.
     *
     * @param i : X-coord
     * @param j : Y-coord
     *
     * @return corresponding memory index
     */
    unsigned int getMemIndex(int i, int j) const;

    /*!
     * @brief Returns SDS id
     *
     * @return id of SDS
     */
    unsigned int getId() const;

    /*!
     * exec equation on SDS
     * to be added as thread task
     */
    void execEquation(eqType eqFunc,
            const std::map< std::string, Quantity<real>* >& quantityMap);

  private:

    /*!
     * own coordinates converter (should be a copy of
     * the converter of the parent SDD
     */
    CoordConverter _coordConverter;
    unsigned int _id;

};

#endif

