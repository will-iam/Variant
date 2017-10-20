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
#include <unordered_map>
#include <string>
#include <iostream>
#include <memory>

#include "SDShared.hpp"
#include "Quantity.hpp"
#include "Geometry.hpp"
#include "number/number.hpp"
#include "threadpool/threadpool.hpp"
#include "exception/exception.hpp"

// Boundary indices (sides have to be less than zero)
#define INSIDE 0
#define LEFT -1
#define RIGHT -2
#define TOP -3
#define BOTTOM -4

// Types of ghost cells : boundary condition type (border of the domain),
// or overlap (inside the domain)
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

    bool operator() (const coords_type& c1, const coords_type& c2) const {
        if (c1.second < c2.second)
            return true;
        if (c1.second == c2.second)
            return c1.first < c2.first;
        return false;
    }
};

struct compare_sddandcoords {

    bool operator()(const sddandcoords_type& s1, const sddandcoords_type& s2) const {
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
     * @param sizeX number of cells of subdomain
     * on the X-axis
     * @param sizeY number of cells of subdomain
     * on the Y-axis
     */
    SDDistributed(unsigned int sizeX, unsigned int sizeY,
            int BL_X, int BL_Y,
            unsigned int boundaryThickness,
            unsigned int neighbourHood,
            unsigned int id,
            unsigned int nSDD);
    /*!
     * @brief Destructor
     */
    ~SDDistributed();

    /*!
     * @brief Returns map between coords on SDD and "real cell" on neighbour SDD /
     * boundary side
     */
    std::map< std::pair<int, int>,
        std::pair< int, std::pair<int, int> > > getBoundaryMap();

    /*!
     * @brief Gets physical quantity previously added
     * with method addQuantity.
     *
     * @param name name of the quantity to get
     */
    Quantity<real>* getQuantity(std::string name);

    /*!
     * @brief Gets all SDS on SDD for a read-only
     * access.
     *
     * @return const reference to the array of all
     * subdomains on SDD
     */
    const std::vector<SDShared>& getSDS() const;

    /*!
     * @brief Gets width of SDD, excluding boundary thickness.
     *
     * @return width of SDD
     */
    unsigned int getSizeX() const;

    /*!
     * @brief Gets height of SDD, excluding boundary thickness
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

    unsigned int getNumberNeighbourSDDs() const;
    unsigned int getNumberOverlapCells() const;
    unsigned int getNumberBoundaryCells() const;

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

    /*!
     * @brief Manually set the value on a coordinate, without having to get
     * the quantity.
     *
     * @param quantityName name of quantity to update
     * @param coordX coordinate on X-axis of cell to update
     * @param coordY coordinate on Y-axis of cell to update
     * @param value value to set on the desired cell for the desired quantity
     */
    void setValue(std::string quantityName, int coordX, int coordY, real value);

    /*!
     * @brief Manually set the value on a coordinate, without having to get
     * the quantity.
     *
     * @param quantityName name of quantity to update
     * @param coordX coordinate on X-axis of cell to update
     * @param coordY coordinate on Y-axis of cell to update
     * @param value value to set on the desired cell for the desired quantity
     */
    real getValue(std::string quantityName, int coordX, int coordY) const;

    /*!
     * @brief Builds map of cells to send from this SDD to other SDDs.
     *
     * @param domain parent domain of the SDD
     */
    void buildSendMap();
    /*!
     * @brief Builds map between coords on SDD and "real cell" on neighbour SDD /
     * boundary side
     *
     * @param domain parent domain of the SDD
     */
    void buildRecvMap(const Domain& domain);

    /*!
     * @brief Adds physical quantity (and thus data) used
     * in the scheme.
     *
     * @param name name of the quantity to add, used as reference when getting
     * and setting a value, or when getting the whole quantity data
     */
    template<typename T> void addQuantity(std::string name);

    /*!
     * @brief Build subdomains on shared memory based on
     * geometry type
     *
     * @param nSDS number of subdomains to be built
     * @param geomType geometry type of subdomain (see
     * the Geometry class for possible values)
     */
    void buildAllSDS(unsigned int nSDS,
            std::string geomType);

    /*!
     * @brief Updates overlap cells by communicating through MPI with other SDDs
     *
     * @param qtiesToUpdate list of str. names of quantities to update
     */
    void updateOverlapCells(const std::vector<std::string>& qtiesToUpdate);

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
    void updateNeumannCells(std::string quantityName,
            bool changeToOpposite = false);

    /*!
     * @brief Updates Dirichlet boundary cells of SDD according to values stored
     * in memory.
     *
     * @param quantityName str. name of quantity to update
     */
    void updateDirichletCells(std::string quantityName);

    /*!
     * @brief Adds an equation to the stack of equations to be computed by
     * the scheme.
     *
     * @param eqFunc function to be added to the task
     */
    void addEquation(std::string eqName, eqType eqFunc);

    /*!
     * @brief Computes equation in the order they were added to the task
     * stack.
     */
    void execEquation(std::string eqName);

    /*!
     * @brief Builds thread pool given an amount of threads to build.
     *
     * @param nThreads number of threads to build
     */
    void initThreadPool(unsigned int nThreads);

  private:

    // Attributes

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
     * number of sdds that should be around.
     */
    unsigned int _neighbourHood;

    /*!
     * id of the SDD in Domain
     */
    unsigned int _id;

    /*!
     * geometry tool to build SDSs
     */
    Geometry _geometry;

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
    std::map< std::pair<int, int>, std::pair<int, int> > _neumannCellMap;

    /*!
     * thread pool for executing equation on SDS in parallel
     */
    std::unique_ptr<ThreadPool> _threadPool;

    /*!
     * bottom-left coords on domain
     */
    std::pair<int, int> _BL;

    // Communications between SDDs variables
    /*!
     * mapping between receiving coord on this SDD to sending coords on other SDDs
     */
    std::map< std::pair<int, int>, std::pair<unsigned int, std::pair<int, int> >, compare_coords > _MPIRecv_map;
    /*!
     * mapping between receiving coords on other SDDs to sending coords on this SDD
     */
    std::map< std::pair<unsigned int, std::pair<int, int> >, std::pair<int, int>, compare_sddandcoords > _MPISend_map;

    /*!
     * number of total SDDs
     */
    unsigned int _nSDD;
    std::vector<int> _neighbourSDDVector;

    // Building buffers based on recv and send maps (avoid memory allocation during loop)
    std::unordered_map<int, std::pair< std::vector<real>, std::vector<real> > > _recvSendBuffer;
    MPI_Request* _requestArray;
    MPI_Status* _statusArray;
};

template<typename T> void SDDistributed::addQuantity(std::string name) {

    _quantityMap[name] = new Quantity<T>((_sizeX + 2 * _boundaryThickness) * (_sizeY + 2 * _boundaryThickness), _coordConverter);
}

#endif
