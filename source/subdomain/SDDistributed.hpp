#ifndef SDDISTRIBUTED_HPP
#define SDDISTRIBUTED_HPP

/*!
 * @file:
 *
 * @brief Defines the class of subdomain on
 * distributed memory (SDD)
 *
 */

#include <map>
#include <string>
#include <iostream>
#include <memory>

#include "SDShared.hpp"
#include "Quantity.hpp"
#include "Geometry.hpp"
#include "number/number.hpp"
#include "threadpool/threadpool.hpp"
#include "exception/exception.hpp"

#define OVERLAP 0
#define DIRICHLET 1
#define PERIODIC 2
#define NEUMANN 3

// Forward declaration
class Domain;

// Custom order for the MPI Recv and Send maps
typedef std::pair<int, std::pair<int, int> > sddandcoords_type;
typedef std::pair<int, int> coords_type;

struct compare_coords {

    bool operator() (const coords_type& c1, const coords_type& c2) {
        if (c1.second < c2.second)
            return true;
        if (c1.second == c2.second)
            return c1.first < c2.first;
        return false;
    }
};

struct compare_sddandcoords {

    bool operator()(const sddandcoords_type& s1, const sddandcoords_type& s2) {
        if (s1.first < s2.first)
            return true;
        if (s1.first == s2.first) 
            return compare_coords()(s1.second, s2.second);

        return false;
    }
};


/*!
 * @brief Subdomain on distributed memory (SDD)
 *
 * Defines a subdomain on distributed memory. It represents
 * a part of a domain available as a single block of memory,
 * hence its definition as a rectangle.
 * It will then be sliced on geometric subdomains on this
 * block of shared memory (SDShared). 
 */
class SDDistributed {

  public:

    /*!
     * @brief Constructor
     *
     * @param sizeX : number of cells of subdomain
     * on the X-axis
     * @param sizeY : number of cells of subdomain
     * on the Y-axis
     */
    SDDistributed(unsigned int sizeX, unsigned int sizeY,
            int BL_X, int BL_Y,
            unsigned int boundaryThickness, 
            unsigned int id,
            unsigned int nSDD);
    /*!
     * @brief Destructor
     */
    ~SDDistributed();

    /*!
     * @brief Builds map between coords on SDD and "real cell" on neighbour SDD /
     * boundary side
     */
    void buildSendMap(const Domain& domain);
    void buildRecvMap(const Domain& domain);

    /*!
     * @brief Returns map between coords on SDD and "real cell" on neighbour SDD /
     * boundary side
     */
    std::map< std::pair<int, int>,
        std::pair< int, std::pair<int, int> > > getBoundaryMap();

    /*!
     * @brief Adds physical quantity (and thus data) used 
     * in the scheme.
     * 
     * @param name : name of the quantity to add
     */
    template<typename T> void addQuantity(std::string name);

    /*!
     * @brief Gets physical quantity previously added 
     * with method addQuantity. 
     * 
     * @param name : name of the quantity to get
     */
    Quantity<real>* getQuantity(std::string name);

    /*!
     * @brief Build subdomains on shared memory based on
     * geometry type
     *
     * @param nSDS : number of subdomains to be built
     * @param geomType : geometry type of subdomain (see
     * the Geometry class for possible values)
     */
    void buildAllSDS(unsigned int nSDS,
            std::string geomType);

    /*!
     * @brief Gets all SDS on SDD for a read-only
     * access.
     *
     * @return const reference to the array of all
     * subdomains on SDD
     */
    const std::vector<SDShared>& getSDS() const;

    /*!
     * @brief Gets width of SDD.
     *
     * @return width of SDD
     */
    unsigned int getSizeX() const;

    /*!
     * @brief Gets height of SDD
     *
     * @return height of SDD
     */
    unsigned int getSizeY() const;

    /*!
     * @brief Gets unique id of SDD
     *
     * @return id of SDD
     */
    unsigned int getId() const;

    /*!
     * @brief Returns mapping between overlap cells
     * and corresponding "real cells" on other SDDs.
     * 
     * Used by the domain to communicate between SDDs
     * when updating overlap cells
     */
    const std::map< std::pair<int, int>,
        std::pair< int, std::pair<int, int> > >&
            getOverlapCellMap() const;

    void updateOverlapCells(const std::vector<std::string>& qtiesToUpdate);
    void updateNeumannCells(std::string quantityName,
            bool changeToOpposite = false);
    void updateDirichletCells(std::string quantityName);

    void addEquation(eqType eqFunc);
    void execEquation();

    void initThreadPool(unsigned int nThreads);

    void setValue(std::string quantityName, int coordX, int coordY, real value);
    real getValue(std::string quantityName, int coordX, int coordY) const;
    void addBoundaryCoords(unsigned int uid, std::pair<int, int> coords, char BCtype, real value);

  private:


    /*!
     * map storing physical quantities in correspondance
     * with their names
     * storing pointers for allocation at any time
     */
    //std::map<std::string, QuantityInterface*> _quantityMap;
    std::map< std::string, Quantity<real>* > _quantityMap;

    /*!
     * array of all subdomains of the SDD
     */
    std::vector<SDShared> _SDSList;

    /*!
     * tool specific to a subdomain to convert 2D coordinates
     * to memory indices of data
     */
    CoordConverter _coordConverter;

    /*!
     * width of SDD
     */
    unsigned int _sizeX;
    /*!
     * height of SDD
     */
    unsigned int _sizeY;

    /*!
     * boundary thickness (number of cells)
     */
    unsigned int _boundaryThickness;

    /*!
     * id of the SDD in Domain
     */
    unsigned int _id;

    /*!
     * geometry tool to build SDSs
     */
    Geometry _geometry;

    /*!
     * mapping between overlap cells on this SDD to
     * the corresponding neighbours with "real cell" values,
     * with the associated pair (SDDid, coordsOnCorrespondingSDDid)
     */
    std::map< std::pair<int, int>,
        std::pair< int, std::pair<int, int> > >
            _overlapCellMap;
    /*!
     * mapping between coords of cells on which are
     * set Dirichlet boundary conditions, and the
     * values of the BC
     */
    std::map< std::pair<int, int>, real >
            _dirichletCellMap;

    /*!
     * mapping between coords of cells on which are set
     * Neumann boundary conditions, and the associated
     * cells
     */
    std::map< std::pair<int, int>,
        std::pair<int, int> >
            _neumannCellMap;

    /*!
     * thread pool for executing equation on SDS in parallel
     */
    std::unique_ptr<ThreadPool> _threadPool;

    /*!
     * bottom-left coords on domain
     */
    std::pair<int, int> _BL;

    // Communications between SDDs variables
    std::map< std::pair<int, int>, std::pair<int, std::pair<int, int> >, compare_coords > _MPIRecv_map;
    std::map< std::pair<int, std::pair<int, int> >, std::pair<int, int>, compare_sddandcoords > _MPISend_map;

    unsigned int _nSDD;


};

template<typename T> void SDDistributed::addQuantity(std::string name) {

    _quantityMap[name] = new Quantity<T>((_sizeX + 2 * _boundaryThickness) * (_sizeY + 2 * _boundaryThickness), _coordConverter);
}

#endif
