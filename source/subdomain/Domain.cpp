#include "Domain.hpp"
#include "IO.hpp"
#include "Geometry.hpp"

#include <fstream>
#include <cassert>
#include <algorithm>

Domain::Domain() {

}

Domain::~Domain() {

    delete _sdd;
}

void Domain::initRect(real lx, real ly,
                      unsigned int Nx, unsigned int Ny) {

    _lx = lx;
    _ly = ly;
    _Nx = Nx;
    _Ny = Ny;

    _dx = _lx / Nx;
    _dy = _ly / Ny;
}

void Domain::setOptions(unsigned int nSDD, unsigned int nSDD_X, unsigned int nSDD_Y,
        unsigned int nSDS, std::string SDSgeom,
        unsigned int nThreads, unsigned int nCommonSDS) {

    _nSDD = nSDD;
    _nSDD_X = nSDD_X;
    _nSDD_Y = nSDD_Y;
    _nSDS = nSDS;
    _SDSgeom = SDSgeom;
    _nThreads = nThreads;
    _nCommonSDS = nCommonSDS;
}

unsigned int Domain::getNumberNeighbourSDDs() const {

    return _sdd->getNumberNeighbourSDDs();
}

unsigned int Domain::getNumberPhysicalCells() const {

    return _sdd->getSizeX() * _sdd->getSizeY();
}

unsigned int Domain::getNumberOverlapCells() const {

    return _sdd->getNumberOverlapCells();
}

size_t Domain::getNumberBoundaryCells() const {

    return _sdd->getNumberBoundaryCells();
}

std::vector<unsigned int> Domain::getUidList() const {

    std::vector<unsigned int> uidList;
    for (std::map< unsigned int, std::pair<int, int> >::const_iterator it = _uidToCoords.begin();
            it != _uidToCoords.end(); ++it) {
        uidList.push_back(it->first);
    }
    return uidList;
}

std::pair<int, int> Domain::getCoordsOnDomain(unsigned int uid) const {

    return _uidToCoords.at(uid);
}

void Domain::addCoord(unsigned int uid, std::pair<int, int> coords) {

    assert(_uidToCoords.find(uid) == _uidToCoords.end());
    _uidToCoords[uid] = coords;
    _coordsToUid[coords] = uid;
}

void Domain::addBoundaryCoords(std::pair<int, int> coordsOnSDD, char BCtype, real value) {

    _SDD_coordsToBC[coordsOnSDD] = std::pair<char, real>(BCtype, value);
}

void Domain::addQuantity(std::string quantityName, bool constant) {

    if (!constant)
        _nonCstQties.push_back(quantityName);
    _sdd->addQuantity<real>(quantityName);
}

void Domain::addEquation(std::string eqName, eqType eqFunc) {

    _sdd->addEquation(eqName, eqFunc);
}

void Domain::buildSubDomainsMPI(unsigned int neighbourHood, unsigned int boundaryThickness) {

    MPI_Comm_size(MPI_COMM_WORLD, &_MPI_size);
    MPI_Comm_rank(MPI_COMM_WORLD, &_MPI_rank);

    assert((_nSDD_X * _nSDD_Y) == _nSDD);
    assert(_Nx % _nSDD_X == 0);
    assert(_Ny % _nSDD_Y == 0);

    _sdd = new SDDistributed(_SDD_Nx, _SDD_Ny, _SDD_BL_X, _SDD_BL_Y, boundaryThickness, neighbourHood, _MPI_rank, _nSDD);

    _sdd->buildAllSDS(_nSDS, _SDSgeom);

    // Communicating size and coords of SDD
    _SDD_BLandSize_List.resize(_nSDD);
    std::array<int, 4> BLandSize;
    BLandSize[0] = _SDD_BL_X;
    BLandSize[1] = _SDD_BL_Y;
    BLandSize[2] = _SDD_Nx;
    BLandSize[3] = _SDD_Ny;
    _SDD_BLandSize_List[_MPI_rank] = BLandSize;
    for (unsigned int id = 0; id < _nSDD; ++id)
        MPI_Bcast(&_SDD_BLandSize_List[id], 4, MPI_INT, id, MPI_COMM_WORLD);
}

void Domain::buildBoundaryMap() {

    std::map< std::pair<int, int>, real > dirichletCellMap;
    std::map< std::pair<int, int>, std::pair<int, int> > neumannCellMap;

    _sdd->buildRecvMap(*this, dirichletCellMap, neumannCellMap);
    MPI_Barrier(MPI_COMM_WORLD);
    _sdd->buildSendMap();

    // Once we have the boundary cells, dispatch them among the SDS available.
    _sdd->dispatchBoundaryCell(dirichletCellMap, neumannCellMap);
}

void Domain::execEquation(const std::string& eqName) {

    _sdd->execEquation(eqName);
}

int Domain::getBoundarySide(std::pair<int, int> coords) const {

    if (coords.first < 0)
        return LEFT;
    else if (coords.first >= (int) _Nx)
        return RIGHT;
    else if (coords.second < 0)
        return BOTTOM;
    else if (coords.second >= (int) _Ny)
        return TOP;
    else
        return INSIDE;
}

std::pair<int, std::pair<int, int> >
Domain::getSDDandCoords(std::pair<int, int> coordsOnDomain) const {

    int boundarySide = getBoundarySide(coordsOnDomain);

    if (boundarySide == INSIDE) {
        // In case it is an overlap cell
        // Getting SDDid and coords of "real" cell
        // corresponding to the coords on domain

        // Finding the correct SDD
        for (unsigned int i = 0; i < _nSDD; i++) {

            // If coord is in rectangle then it is found
            std::array<int, 4> BLandSize = _SDD_BLandSize_List.at(i);
            std::pair<int, int> BL(BLandSize[0], BLandSize[1]);
            std::pair<int, int> SDDsize(BLandSize[2], BLandSize[3]);
            if (coordsOnDomain.first >= BL.first &&
                coordsOnDomain.first < BL.first + SDDsize.first &&
                coordsOnDomain.second >= BL.second &&
                coordsOnDomain.second < BL.second + SDDsize.second) {

                std::pair<int, int>
                coordsOnCorrectSDD(coordsOnDomain.first - BL.first,
                                   coordsOnDomain.second - BL.second);
                return std::pair< int, std::pair<int, int> >(i, coordsOnCorrectSDD);
            }
        }
    }

    // If it is on boundary, then we return the boundary side
    // and the same coords on domain
    return std::pair< int, std::pair<int, int> >(boundarySide, coordsOnDomain);
}

std::pair<int, std::pair<int, int> >
Domain::getShiftSDDandCoords(std::pair<int, int> coords) const {

    // Coords on domain
    // The SDD is supposed to be a rectangle so the
    // conversion only needs the bottom left coords of
    // the SDD
    std::pair<int, int> coordsOnDomain(coords.first + _SDD_BL_X, coords.second + _SDD_BL_Y);

    return getSDDandCoords(coordsOnDomain);
}

std::pair<int, int> Domain::getBLOfSDD(unsigned int SDDid) const {
    std::array<int, 4> BLandSize = _SDD_BLandSize_List[SDDid];
    return std::pair<int, int>(BLandSize[0], BLandSize[1]);
}

std::pair<char, real> Domain::getBoundaryCondition(std::pair<int, int> coordsOnSDD) const {
    if (_SDD_coordsToBC.find(coordsOnSDD) == _SDD_coordsToBC.end())
        exitfail("Boundary conditions not found on proc: %", _MPI_rank);

    return _SDD_coordsToBC.at(coordsOnSDD);
}

// Because it needs a method from the class Domain, we
// define this function from SDDistributed here
void SDDistributed::buildRecvMap(const Domain& domain,
        std::map< std::pair<int, int>, real >& dirichletCellMap,
        std::map< std::pair<int, int>, std::pair<int, int> >& neumannCellMap) {

    // Init boundary cells of SDD
    std::vector< std::pair<int, int> > boundaryCellList;
    for (unsigned int k = 1; k <= _boundaryThickness; ++k) {

        // --------------------------------------------------------
        // Left
        for (unsigned int j = 0; j < _sizeY; j++) {
            boundaryCellList.push_back(std::pair<int, int>(-k, j));
        }
        // Top
        for (unsigned int i = 0; i < _sizeX; i++) {
            boundaryCellList.push_back(std::pair<int, int>(i, _sizeY + k - 1));
        }
        // Right
        for (int j = _sizeY - 1; j >= 0; j--) {
            boundaryCellList.push_back(std::pair<int, int>(_sizeX + k - 1, j));
        }
        // Bottom
        for (int i = _sizeX - 1; i >= 0; i--) {
            boundaryCellList.push_back(std::pair<int, int>(i, -k));
        }

        // --------------------------------------------------------
        if (_neighbourHood == 4)
            continue;

        // WITH CORNERS VERSION
        // upper left
        for (unsigned int j = _sizeY; j < _sizeY + _boundaryThickness; ++j) {
            boundaryCellList.push_back(std::pair<int, int>(-k, j));
        }

        // upper right
        for (unsigned int j = _sizeY; j < _sizeY + _boundaryThickness; ++j) {
            boundaryCellList.push_back(std::pair<int, int>(_sizeX - 1 + k, j));
        }

        // bottom right
        for (int j = 0 - _boundaryThickness; j < 0; ++j) {
            boundaryCellList.push_back(std::pair<int, int>(_sizeX - 1 + k, j));
        }

        // bottom left
        for (int j = 0 - _boundaryThickness; j < 0; ++j) {
            boundaryCellList.push_back(std::pair<int, int>(-k, j));
        }

    }

    // Now mapping all cells to SDD and corresponding
    // coords on SDD, or to boundary
    for (std::vector< std::pair<int, int> >::iterator it = boundaryCellList.begin(); it != boundaryCellList.end(); ++it) {

        // For each boundary cell we check its type : either a
        // boundary cell of the domain, or an overlap cell
        std::pair< int, std::pair<int, int> > SDDandCoords = domain.getShiftSDDandCoords(*it);

        // If it is an overlap cell, we simply add it to the list of
        // overlap cells
        if (SDDandCoords.first >= 0) {

            _MPIRecv_map[*it] = SDDandCoords;
            // Adding the SDD to the list of neighbours
            if (_nSDD > 1 && find(_neighbourSDDVector.begin(), _neighbourSDDVector.end(), SDDandCoords.first) == _neighbourSDDVector.end())
                _neighbourSDDVector.push_back(SDDandCoords.first);
        }

        // If it is a real boundary cell, it depends on the boundary type
        else {

            // In this case SDDandCoords.second is the coords
            // of the cell on the domain

            std::pair<int, int> coordsOnDomain = SDDandCoords.second;
            std::pair<char, double> bc = domain.getBoundaryCondition(*it);

            if (bc.first == 'D') {
                // Dirichlet BC
                dirichletCellMap[*it] = bc.second;
            }

            else if (bc.first == 'N') {
                // This is a little more complicated since
                // it depends on the boundary side and coordinates
                int boundarySide = SDDandCoords.first;
                std::pair<int, int> targetCell(coordsOnDomain);
                switch (boundarySide) {
                    case LEFT:
                        targetCell.first = -coordsOnDomain.first - 1;
                        break;

                    case BOTTOM:
                        targetCell.second = -coordsOnDomain.second - 1;
                        break;

                    case RIGHT: {
                        unsigned int sizeX = domain.getSizeX();
                        targetCell.first = -(coordsOnDomain.first - sizeX) + sizeX - 1;
                        break;
                    }

                    case TOP: {
                        unsigned int sizeY = domain.getSizeY();
                        targetCell.second = -(coordsOnDomain.second - sizeY) + sizeY - 1;
                        break;
                    }

                    default:
                        assert(false);
                        break;
                }

                // Reconvert coords of target cell FROM DOMAIN TO SDD
                std::pair<int, int> thisSDDBL = domain.getBLOfSDD(_id);
                std::pair<int, int> coordsOfTargetCell;
                coordsOfTargetCell.first = targetCell.first - thisSDDBL.first;
                coordsOfTargetCell.second = targetCell.second - thisSDDBL.second;

                // Finally add target cell as neumann cell
                neumannCellMap[*it] = coordsOfTargetCell;
            }

            else if (bc.first == 'P') {
                // Periodic BC
                // cells with periodic BC are actually the same
                // as overlap cells targetted to the other side !
                std::pair<int, int> targetCell(coordsOnDomain);
                if (targetCell.first < 0) {
                    targetCell.first += domain.getSizeX();
                }
                else if (targetCell.first >= (int)(domain.getSizeX())) {
                    targetCell.first -= domain.getSizeX();
                }

                if (targetCell.second < 0) {
                    targetCell.second += domain.getSizeY();
                }
                else if (targetCell.second >= (int)(domain.getSizeY())) {
                    targetCell.second -= domain.getSizeY();
                }

                // Determine SDD and coords on SDD of target cell
                std::pair< int, std::pair<int, int> >
                SDDandCoordsOfTargetCell = domain.getSDDandCoords(targetCell);
                // Finally add target cell as overlap cell
                // If target cell still is on the boudary, then we ignore it
                if (SDDandCoordsOfTargetCell.first >= 0) {
                    _MPIRecv_map[*it] = SDDandCoordsOfTargetCell;
                    //std::cerr <<  "coordsOnDomain.first: " << coordsOnDomain.first << ", coordsOnDomain.second: " << coordsOnDomain.second << std::endl;
                    //std::cerr <<  "targetCell.first: " << targetCell.first << ", targetCell.second: " << targetCell.second << std::endl;
                    //std::cerr <<  "SDDandCoordsOfTargetCell.first: " << SDDandCoordsOfTargetCell.first << std::endl;
                    // Adding the SDD to the list of neighbours
                    if (_nSDD > 1 && find(_neighbourSDDVector.begin(), _neighbourSDDVector.end(), SDDandCoordsOfTargetCell.first) == _neighbourSDDVector.end())
                        _neighbourSDDVector.push_back(SDDandCoordsOfTargetCell.first);
                }
            }

            else {
                assert(false);
            }
        }

        //std::cout << it->first << "..." << it->second << std::endl;
    }
}

void SDDistributed::buildSendMap() {

    unsigned int nSDD = _nSDD;
    std::vector<int> numberOfCellsToRecv(nSDD, 0); // data sent to other SDDs
    std::vector<int> numberOfCellsToSend(nSDD, 0); // data recved from other SDDs
    std::vector<MPI_Status> statuses(nSDD);

    // Counting number of cells to receive based on recv map
    for (auto const &it : _MPIRecv_map)
        numberOfCellsToRecv[it.second.first]++;

    // Sending and receiving the number of cells needed
    for (unsigned int SDDto = 0; SDDto < nSDD; ++SDDto) {

        // Not sending messages to oneself...
        if (SDDto == _id)
            continue;

        // Tag: SDDfrom * nSDD + SDDto
        MPI_Sendrecv(&numberOfCellsToRecv[SDDto], 1, MPI_INT, SDDto, _id * nSDD + SDDto,
                &numberOfCellsToSend[SDDto], 1, MPI_INT, SDDto, SDDto * nSDD + _id, MPI_COMM_WORLD, &statuses[SDDto]);
        //std::cout << _id << " -> " << SDDto << " --- " << numberOfCellsToRecv[SDDto] << " ; " << numberOfCellsToSend[SDDto] << std::endl;
    }

    // Now that we know how many cells we have to receive and send, we can...
    // receive and send

    // data recved from other SDDs, used to build the Send map
    std::vector< std::vector< std::array<int, 4> > > cellsToRecv(nSDD);
    // data sent to other SDDs, based on the Recv map
    std::vector< std::vector< std::array<int, 4> > > cellsToSend(nSDD);

    // Initializing cells to receive based on Recv map, and arrays for Send
    // map
    for (unsigned int SDDto = 0; SDDto < nSDD; ++SDDto) {

        // Not sending messages to oneself...
        if (SDDto == _id)
            continue;

        // Array sizes should be EXACTLY what is reserved
        // and not more, since arrays were just initialized to default
        // capacity, ie. 0
        cellsToSend[SDDto].resize(numberOfCellsToSend[SDDto]);
        cellsToRecv[SDDto].reserve(numberOfCellsToRecv[SDDto]);
    }

    for (auto const &it : _MPIRecv_map) {

        // Init correspondence here
        std::array<int, 4> coordsCorresp;
        coordsCorresp[0] = it.first.first;
        coordsCorresp[1] = it.first.second;
        coordsCorresp[2] = it.second.second.first;
        coordsCorresp[3] = it.second.second.second;
        cellsToRecv[it.second.first].push_back(coordsCorresp);
    }

    // Send messages
    for (unsigned int SDDto = 0; SDDto < nSDD; ++SDDto) {

        // Not sending messages to oneself...
        if (SDDto == _id)
            continue;

        // Tag: SDDfrom * nSDD + SDDto
        MPI_Sendrecv(&cellsToRecv[SDDto][0], 4 * numberOfCellsToRecv[SDDto],
                    MPI_INT, SDDto, _id * nSDD + SDDto,
                &cellsToSend[SDDto][0], 4 * numberOfCellsToSend[SDDto],
                    MPI_INT, SDDto, SDDto * nSDD + _id,
                MPI_COMM_WORLD, &statuses[SDDto]);

        // Parse the received message
        for (int i = 0; i < numberOfCellsToSend[SDDto]; ++i) {

            std::array<int, 4> coordsCorresp = cellsToSend[SDDto][i];
            std::pair<int, std::pair<int, int> >
                thereCoordsAndSDD(SDDto,
                        std::pair<int, int>(coordsCorresp[0], coordsCorresp[1]));
            std::pair<int, int> hereCoords(coordsCorresp[2], coordsCorresp[3]);
            _MPISend_map[thereCoordsAndSDD] = hereCoords;
            //std::cout << thereCoordsAndSDD << " -> " <<  _MPISend_map[thereCoordsAndSDD] << std::endl;
        }

        // To reserve the size of the buffer init for 4 quantities.
        if (numberOfCellsToSend[SDDto] > 0) {
            _recvSendBuffer[SDDto].first.reserve(4 * numberOfCellsToSend[SDDto]);
            _recvSendBuffer[SDDto].second.reserve(4 * numberOfCellsToSend[SDDto]);
        }
    }

    if (_recvSendBuffer.size() != _neighbourSDDVector.size()) {
        std::cerr << std::endl << "neighbourSDDVector: ";
        for (auto& v : _neighbourSDDVector)
            std::cerr << v << " ";
        std::cerr << std::endl << "recvSendBuffer: ";
        for (auto& p : _recvSendBuffer)
            std::cerr << p.first << " ";
        std::cerr << std::endl;
        exitfail("Buffer does not contain all the neighbours.");
    }

    for (const auto& sddId : _neighbourSDDVector) {
        if (_recvSendBuffer.find(sddId) == _recvSendBuffer.end())
            exitfail("Could not find SDD in neighbourhood.");
    }

    // shuffle vector to dilute the effect of always start with the lower ranking.
    std::random_shuffle(_neighbourSDDVector.begin(), _neighbourSDDVector.end());

    _requestArray = new MPI_Request[_neighbourSDDVector.size() * 2];
    _statusArray = new MPI_Status[_neighbourSDDVector.size() * 2];

    // Sync processes
    MPI_Barrier(MPI_COMM_WORLD);
    //std::cout << "Sync done" << std::endl;
}

unsigned int Domain::getUid(std::pair<int, int> coordsOnDomain) const {

    return _coordsToUid.at(coordsOnDomain);
}

void Domain::updateOverlapCells(const std::string& qtyName) {
    _sdd->updateOverlapCells(std::vector<std::string>(1, qtyName));
}

void Domain::updateOverlapCells() {
    // For each SDD...
    _sdd->updateOverlapCells(_nonCstQties);
}

void Domain::printState(std::string quantityName) {

    for (unsigned int i = 0; i < _SDD_Nx; i++) {
        for (unsigned int j = 0; j < _SDD_Ny; j++) {
            // Manually get value
            const Quantity<real>& _qty = *_sdd->getQuantity(quantityName);
            std::cout << "(" << i << " ; " << j << ") --> " << _qty.get(0, i, j) << std::endl;
        }
    }
    std::cout << "\n" << std::endl;
}

void Domain::buildThreads() {

    _sdd->initThreadPool(_nThreads, _nCommonSDS);
}

void Domain::setSDDInfo(unsigned int BL_X, unsigned int BL_Y,
        unsigned int Nx, unsigned Ny) {

    _SDD_BL_X = BL_X;
    _SDD_BL_Y = BL_Y;
    _SDD_Nx = Nx;
    _SDD_Ny = Ny;
}

SDDistributed& Domain::getSDD() {

    return *_sdd;
}

const SDDistributed& Domain::getSDDconst() const {

    return *_sdd;
}

void Domain::switchQuantityPrevNext(std::string quantityName) {

    _sdd->getQuantity(quantityName)->switchPrevNext();
}


int isPowerOf(unsigned int N, unsigned int reason) {

    unsigned int power = 0;
    while ((N % reason) == 0 && N > 1) {
        ++power;
        N /= reason;
    }

    if (N == 1)
        return power;
    return -1;
}
