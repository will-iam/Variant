#ifndef DOMAIN_HPP
#define DOMAIN_HPP

/*!
 * @file:
 *
 * @brief Defines the Domain class
 */

#include <map>
#include <string>
#include <vector>
#include <array>

#include "SDDistributed.hpp"
#include "number/number.hpp"
#include "exception/exception.hpp"

/*!
 * @brief Domain on which a scheme is executed
 *
 * A domain is the physical discrete set on which a
 * finite volumes scheme is solved.
 * Its space is divided into subdomains on distributed
 * memory (SDD), in order to allow MPI parallel execution on several
 * machines.
 * These subdomains are then split in smaller subdomains (SDS),
 * each one being treated as a task assigned to a thread.
 */
class Domain {

  public:

    /*!
     * @brief Constructor
     */
    Domain();
    /*!
     * @brief Destructor
     */
    ~Domain();

    /*!
     * @brief Initializes domain rectangle.
     *
     * @param lx physical width of the domain
     * @param ly physical width of the domain
     * @param Nx number of cells on the x-axis
     * @param Ny number of cells on the y-axis
     */
    void initRect(real lx, real ly,
                  unsigned int Nx, unsigned int Ny);

    /*!
     * @brief Changes options for building SDDs and SDSs.
     *
     * @param nSDD number of SDDs on the domain
     * @param nSDD_X number of SDDs along the x-axis
     * @param nSDD_Y number of SDDs along the y-axis
     * @param nSDS number of SDS per SDD
     * @param SDSgeom type of SDS split
     * @param nThreads number of threads per SDD
     */
    void setOptions(unsigned int nSDD, unsigned int nSDD_X, unsigned int nSDD_Y,
            unsigned int nSDS, std::string SDSgeom,
            unsigned int nThreads, unsigned int nCommonSDS);

    /*!
     * @brief Returns the non-modifiable width of the domain.
     *
     * @return width of the domain
     */
    inline real getlx() const { return _lx; }
    /*!
     * @brief Returns the non-modifiable height of the domain.
     *
     * @return height of the domain
     */
    inline real getly() const { return _ly; }
    /*!
     * @brief Returns the non-modifiable number of cells on the x-axis.
     *
     * @return number of cells on x-axis
     */
    inline unsigned int getSizeX() const { return _Nx; }
    /*!
     * @brief Returns the non-modifiable number of cells on the y-axis.
     *
     * @return number of cells on y-axis
     */
    inline unsigned int getSizeY() const{ return _Ny; }
    /*!
     * @brief Returns the non-modifiable space step on the x-axis (ie. the width of a cell).
     *
     * @return space step on the x-axis
     */
    inline real getdx() const { return _dx; }
    /*!
     * @brief Returns the non-modifiable space step on the y-axis (ie. the height of a cell).
     *
     * @return space step on the y-axis
     */
    inline real getdy() const { return _dy; }

    inline unsigned int getNumberSDD() const { return _nSDD; }
    inline unsigned int getNumberSDD_X() const { return _nSDD_X; }
    inline unsigned int getNumberSDD_Y() const { return _nSDD_Y; }
    inline unsigned int getNumberSDS() const { return _nSDS; }
    inline std::string getSDSGeometry() const { return _SDSgeom; }
    inline unsigned int getNumberThreads() const  { return _nThreads; }
    inline unsigned int getNumberCommonSDS() const  { return _nCommonSDS; }

    unsigned int getNumberNeighbourSDDs() const;
    unsigned int getNumberPhysicalCells() const;
    unsigned int getNumberOverlapCells() const;
    size_t getNumberBoundaryCells() const;

    void showInfo() const;

    /*!
     * @brief Returns vector containing unique ids of all cells.
     *
     * @return vector of uids of all domain cells (unordered) (unordered)
     */
    std::vector<unsigned int> getUidList() const;

    /*!
     * @brief Gets bottom-left coordinates of SDD given by its id.
     *
     * @param SSDid id of desired SDD, with \f$0 \leq \texttt{SDDid}
     * < \texttt{nSDD}\f$
     *
     * @return coordinates of bottom-left cell of desired SDD
     */
    std::pair<int, int> getBLOfSDD(unsigned int SDDid) const;

    /*!
     * @brief Gets coordinates on computed domain of cell given by its unique id.
     *
     * @param uid unique id of desired cell
     *
     * @return coordinates on domain of desired cell
     */
    std::pair<int, int> getCoordsOnDomain(unsigned int uid) const;

    /*!
     * @brief Returns boundary condition on a cell given by its coordinates on
     * the domain.
     *
     * @param coords on the domain of desired cell
     *
     * @return boundary condition (type and value) assigned to cell
     */
    std::map<char, std::map<std::string, real> > getBoundaryCondition(std::pair<int, int> coordsOnSDD) const;

    /*!
     * @brief Returns non-modifiable unique id of cell given by its
     * coordinates on the domain.
     */
    unsigned int getUid(std::pair<int, int> coordsOnDomain) const;

    /*!
     * @brief Returns boundary side (left, right, top, bottom or inside if not
     * on boundary) of a cell given by its coordinates on the domain.
     */
    int getBoundarySide(std::pair<int, int> coords) const;

    /*!
     * @brief Adds new unique id <-> coords on domain correspondence on a given
     * cell.
     *
     * @param uid unique id of new cell
     * @param coords coordinates of new cell on the domain
     */
    void addCoord(unsigned int uid, std::pair<int, int> coords);

    /*!
     * @brief Adds new unique id <-> coords on domain correspondencPieśnie
     * and boundary condition for a cell on the boundary.
     *
     * @param uid unique id of new cell
     * @param coords coordinates of new cell on the domain
     * @param BCtype boundary condition type
     * @param value boundary condition value
     *
     */
    void addBoundaryCoords(std::pair<int, int> coords, char BCtype, const std::map<std::string, real>& qtyValue);

    /*!
     * @brief Adds new quantity to be managed by the scheme.
     *
     * @param name of new quantity
     */
    void addQuantity(std::string quantityName);
    /*!
     * @brief Adds function that resolves a new equation on a SDS to be computed
     * for each iteration by the domain.
     *
     * @param equation function
     */
    void addEquation(std::string eqName, eqType eqFunc);

    /*!
     * @brief Builds subdomains according to set options.
     *
     * This creates the SDDs and their SDSs according to options set in
     * function setOptions, that has to be called before calling this function.
     */
    void buildSubDomainsMPI(unsigned int neighbourHood, unsigned int boundaryThickness);
    /*!
     * @brief Builds all info needed by the domain to compute the boundary
     * according to the boundary conditions set on boundary cells, and overlap cells.
     * must be called once the boundary conditions are defined.
     */
    void buildCommunicationMap();
    /*!
     * @brief Builds the task pool for each SDD.
     *
     * This can only be called after options were set and subdomains
     * were built.
     */
    void buildThreads();

    /*!
     * @brief Calls all added equations, ie. computes an iteration of
     * the scheme on the domain.
     */
    void execEquation(const std::string& eqName);

    /*!
     * @brief updates overlap cells of all SDDs according to their
     * values on reference cells on other SDDs, for a given quantity.
     *
     */
    void updateOverlapCells();

    /*! @brief Returns non-modifiable id of SDD and coordinates on SDD of cell
     * given by its coordinates on the domain.
     *
     * The returned SDD is the one that owns the cell on its computed area,
     * ie. not as an overlap cell.
     *
     * @param coordinates of desired cell on domain
     *
     * @return id of SDD and coordinates on SDD of desired cell
     */
    std::pair<int, std::pair<int, int> >
        getSDDandCoords(std::pair<int, int> coordsOnDomain) const;
    /*! @brief Returns non-modifiable id of SDD and coordinates on SDD of cell
     * given by its coordinates on the domain.
     *
     * The returned SDD is the one that owns the cell on its computed area,
     * ie. not as an overlap cell.
     *
     * @param coordinates of desired cell on domain
     *
     * @return id of SDD and coordinates on SDD of desired cell
     */
    std::pair<int, std::pair<int, int> >
        getShiftSDDandCoords(std::pair<int, int> coords) const;

    /*!
     * @brief Prints quantity values for all cells.
     *
     * @param quantityName name of quantity to print
     */
    void printState(std::string quantityName);

    /*!
     * @brief Change characteristics of SDD (bottom-left and size)
     *
     * @param BL_X X-coordinate of bottom-left coords on domain
     * @param BL_Y Y-coordinate of bottom-left coords on domain
     * @param Nx width of SDD
     * @param Ny height of SDD
     */
    void setSDDInfo(unsigned int BL_X, unsigned int BL_Y,
            unsigned int Nx, unsigned int Ny);

    /*!
     * @brief Returns reference to SDD possessed by this
     * MPI node
     *
     * @return reference to SDD
     */
    SDDistributed& getSDD();

    /*!
     * @brief Returns const reference to SDD possessed by this
     * MPI node
     *
     * @return const reference to SDD
     */
    const SDDistributed& getSDDconst() const;

    void switchQuantityPrevNext(std::string quantityName);

  private:

    std::vector< std::array<int, 4> > _SDD_BLandSize_List;

    std::map< unsigned int, std::pair<int, int> > _uidToCoords;
    std::map< std::pair<int, int>, unsigned int > _coordsToUid;

    // Uid <-> boundary conditions <type, value>
    std::map< std::pair<int, int>, std::map<char, std::map<std::string, real> > > _SDD_coordsToBC;

    real _lx;
    real _ly;
    unsigned int _Nx;
    unsigned int _Ny;
    real _dx;
    real _dy;

    unsigned int _nSDD = 0;
    unsigned int _nSDD_X = 0;
    unsigned int _nSDD_Y = 0;
    unsigned int _nSDS = 0;
    std::string _SDSgeom;
    unsigned int _nThreads = 0;
    unsigned int _nCommonSDS = 0;

    // MPI Variables
    int _MPI_rank;
    SDDistributed* _sdd; // Each proc possesses one SDD

    int _SDD_BL_X;
    int _SDD_BL_Y;
    unsigned int _SDD_Nx;
    unsigned int _SDD_Ny;
};

/*!
 * @brief If \f$N = r^p\f$, returns \f$p\f$
 *
 * @param N number to test
 * @param r corresponding power
 */
int isPowerOf(unsigned int N, unsigned int r);

#endif
