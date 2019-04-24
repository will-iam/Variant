#include "SDDistributed.hpp"
#include <iostream>
#include <cassert>
#include <algorithm>

SDDistributed::SDDistributed(unsigned int sizeX,
                             unsigned int sizeY,
                             int BL_X, int BL_Y,
                             unsigned int boundaryThickness,
                             unsigned int neighbourHood,
                             unsigned int id,
                             unsigned int nSDD):
    _coordConverter(sizeX, sizeY, boundaryThickness),
    _sizeX(sizeX), _sizeY(sizeY),
    _boundaryThickness(boundaryThickness), _neighbourHood(neighbourHood), _id(id),
    _geometry(0, 0, sizeX, sizeY),
    _BL(BL_X, BL_Y),
    _nSDD(nSDD)
    {

    assert(boundaryThickness >= 1);
}

SDDistributed::~SDDistributed() {
    for (const auto& it : _bufferSize) {
        if (_sendBuffer[it.first] != nullptr)
            delete[] _sendBuffer[it.first];

        if (_recvBuffer[it.first] != nullptr)
            delete[] _recvBuffer[it.first];
    }

    _bufferSize.clear();
    _sendBuffer.clear();
    _recvBuffer.clear();

    #ifndef SEQUENTIAL
    delete[] _requestArray;
    delete[] _statusArray;
    #endif

    for (auto it = _quantityMap.begin(); it != _quantityMap.end(); ++it)
        delete (it->second);
}

unsigned int SDDistributed::getSizeX() const {

    return _sizeX;
}

unsigned int SDDistributed::getSizeY() const {

    return _sizeY;
}

unsigned int SDDistributed::getId() const {

    return _id;
}

unsigned int SDDistributed::getNumberNeighbourSDDs() const {

    return _neighbourSDDVector.size();
}

unsigned int SDDistributed::getNumberOverlapCells() const {

    return _MPIRecv_map.size();
}

unsigned int SDDistributed::getNumberBoundaryCells() const {
    size_t s(0);
    for (auto& sds: _SDSVector)
        s += sds.getNumberBoundaryCells();

    return s;
}

void SDDistributed::buildAllSDS(unsigned int nSDS, std::string geomType) {

    std::vector< std::vector< std::pair<int, int> > > geom = _geometry.buildGeometry(nSDS, geomType);
    int i = 0;
    for (auto it = geom.begin(); it != geom.end(); ++it) {
        _SDSVector.push_back(SDShared(*it, _coordConverter, i));
        i++;
    }

    /// Shuffling SDS List
    std::random_shuffle(_SDSVector.begin(), _SDSVector.end());
}

void SDDistributed::dispatchBoundaryCell(const std::map< std::pair<int, int>, std::map<std::string, real> >& dirichletCellMap,
        const std::map< std::pair<int, int>, std::map<std::string, real> >& timeVaryingCellMap,
        const std::map< std::pair<int, int>, std::pair< std::pair<int, int>, std::map<std::string, real> > >& neumannCellMap) {
    if (_SDSVector.empty())
        exitfail("You must initialize the SDS list before splitting the boundary cell");

    // This is a uniform ditribution of the cells, the boundary cells in each sds does not correspond the geometric position of the cell.
    size_t s = neumannCellMap.size() / _SDSVector.size();
    size_t counter = 0;
    size_t cursor = 0;
    for (auto it = neumannCellMap.begin(); it != neumannCellMap.end(); ++it) {
        if (counter >= s) {
            counter = 0;
            ++cursor;
        }

        if (cursor >= _SDSVector.size()) {
            cursor = 0;
            counter = 0;
            s = 1;
        }

        _SDSVector[cursor].addNeumannCell(*it);
        ++counter;
    }


    s = dirichletCellMap.size() / _SDSVector.size();
    counter = 0;
    cursor = 0;
    for (auto it = dirichletCellMap.begin(); it != dirichletCellMap.end(); ++it) {
        if (counter >= s) {
            counter = 0;
            ++cursor;
        }

        if (cursor >= _SDSVector.size()) {
            cursor = 0;
            counter = 0;
            s = 1;
        }

        _SDSVector[cursor].addDirichletCell(*it);
        ++counter;
    }


    s = timeVaryingCellMap.size() / _SDSVector.size();
    counter = 0;
    cursor = 0;
    for (auto it = timeVaryingCellMap.begin(); it != timeVaryingCellMap.end(); ++it) {
        if (counter >= s) {
            counter = 0;
            ++cursor;
        }

        if (cursor >= _SDSVector.size()) {
            cursor = 0;
            counter = 0;
            s = 1;
        }

        _SDSVector[cursor].addTimeVaryingCell(*it);
        ++counter;
    }
    //for (size_t i = 0; i < _SDSVector.size(); ++i)
    //    std::cout << "SDS: " << i << " has " << _SDSVector[i].getNumberBoundaryCells() << " boundary cells.\n";
}

void SDDistributed::dispatchOverlapCell() {

    // Don't take into account self periodic cells.
    if (_nSDD == 1)
        return;

    if (_quantityMap.empty())
        exitfail("At this point, the quantities must be loaded in the map.");

    if (_sendIndexVector.empty())
        exitfail("Zero overlap cells in parallel configuration.");

    if (_sendIndexVector.size() != _recvIndexVector.size())
        exitfail("Size problem in speed-up structures: neighbour numbers are different.");

    size_t totalSize = 0;
    for (const auto& SDDid: _neighbourSDDVector) {
        //std::cout << "[" << _id << "] to " << SDDid << " overlapCells = " << _sendIndexVector[SDDid].size() << std::endl;
        totalSize += _sendIndexVector[SDDid].size();
        if (_sendIndexVector[SDDid].size() != _recvIndexVector[SDDid].size())
            exitfail("Size problem in speed-up structures: different vector size.");
    }

    if (totalSize == 0)
        exitfail("Zero overlap cells in parallel configuration.");

    // This is a uniform ditribution of the cells, the boundary cells in each sds does not correspond the geometric position of the cell.
    size_t s = totalSize / _SDSVector.size();
    size_t counter = 0;
    size_t cursor = 0;

    auto SDDit = _neighbourSDDVector.begin();
    size_t i_vector = 0;
    for (size_t i = 0; i < totalSize && SDDit != _neighbourSDDVector.end(); ++i) {

        if (counter >= s) {
            counter = 0;
            if (++cursor >= _SDSVector.size()) {
                cursor = 0;
                s = 1;
            }
        }

        //if (_id == 2)
        //    std::cout << "[" << _id << "] to " << *SDDit << " " << i_vector << " in SDS " << cursor << std::endl;

        _SDSVector[cursor].addOverlapCell(*SDDit, _sendIndexVector[*SDDit][i_vector], _recvIndexVector[*SDDit][i_vector]);
        ++counter;

        // Move among the different vectors.
        if (++i_vector >= _sendIndexVector[*SDDit].size()){
            i_vector = 0;
            ++SDDit;
        }
    }

    // Now set the pos in the buffer to start to copy/read the data.
    //std::cout << "[" << _id << "] Total Size: " << totalSize << " in " << _neighbourSDDVector.size() << " neighbour(s)." << std::endl;
    size_t check = 0;
    for (const auto& SDDid: _neighbourSDDVector) {
        //if (_id == 2)
        //    std::cout << "[" << _id << "] to SDDid: " << SDDid << " current total " << check << std::endl;

        size_t pos(0);
        for(size_t i = 0; i < _SDSVector.size(); ++i){
            // If it has no cells fot this SDDid, then move to next SDD.
            size_t n = _SDSVector[i].getOverlapCellNumber(SDDid);
            if (n != 0) {
                _SDSVector[i].setBufferPos(SDDid, pos);

                //if (_id == 2)
                //    std::cout << "[" << _id << "] SDS: " << i << ", to SDDid: " << SDDid << " start at pos " << pos << " contains " << n << std::endl;

                pos += n;
            }
        }
        check += pos;
    }

    if (check != totalSize) {
        std::cout << "[" << _id << "] check: " << check << " vs " << totalSize << "\n";
        exitfail("All overlap cells have not been dispatched among the SDS.");
    }

    eqType eqWrite = std::bind(&SDDistributed::writeBuffer, this, std::placeholders::_1, std::placeholders::_2);
    eqType eqRead = std::bind(&SDDistributed::readBuffer, this, std::placeholders::_1, std::placeholders::_2);

    for (auto& sds: _SDSVector) {
        _threadPool->addTask("writeBuffer", std::bind(&SDShared::execEquation, sds, eqWrite, _quantityMap));
        _threadPool->addTask("readBuffer", std::bind(&SDShared::execEquation, sds, eqRead, _quantityMap));
    }
}

void SDDistributed::writeBuffer(const SDShared& sds, const std::map< std::string, Quantity<real>* >& quantityMap) {
    sds.copyOverlapCellIn(quantityMap, _sendBuffer);
}

void SDDistributed::readBuffer(const SDShared& sds, const std::map< std::string, Quantity<real>* >& quantityMap) {
    sds.copyOverlapCellFrom(quantityMap, _recvBuffer);
}

void SDDistributed::addEquation(std::string eqName, eqType eqFunc) {

    for (auto& sds: _SDSVector)
        _threadPool->addTask(eqName, std::bind(&SDShared::execEquation, sds, eqFunc, _quantityMap));
}

const std::vector<SDShared>& SDDistributed::getSDS() const {

    return _SDSVector;
}

Quantity<real>* SDDistributed::getQuantity(std::string name) {

    return _quantityMap[name];
}

void SDDistributed::copyOverlapCell() {
    #ifndef SEQUENTIAL
    _threadPool->start("writeBuffer");
    #endif
}

void SDDistributed::sendOverlapCell() {
    #ifndef SEQUENTIAL
    _lastRequestArraySize = 0;
    for (const auto& toSDDid: _neighbourSDDVector) {
        real* dataToSend = _sendBuffer[toSDDid];
        real* dataToRecv = _recvBuffer[toSDDid];
        size_t bufferSize = _bufferSize[toSDDid];

        MPI_Irecv(dataToRecv, bufferSize,
                  MPI_REALTYPE, toSDDid, toSDDid * _nSDD + _id,
                  MPI_COMM_WORLD, &_requestArray[_lastRequestArraySize++]);

        MPI_Isend(dataToSend, bufferSize,
                  MPI_REALTYPE, toSDDid, _id * _nSDD + toSDDid,
                  MPI_COMM_WORLD, &_requestArray[_lastRequestArraySize++]);
    }
    #endif
}

void SDDistributed::waitOverlapCell() {
    #ifndef SEQUENTIAL
    MPI_Waitall(_lastRequestArraySize, _requestArray, _statusArray);
    #endif
}

void SDDistributed::parseOverlapCell() {
    #ifndef SEQUENTIAL
    _threadPool->start("readBuffer");
    #endif

    // Special case: parsing data for periodic boundary condition with itself.
    for (auto const& it: _selfIndexMap) {
        size_t indexHere(it.first), indexThere(it.second);
        for (const auto p: _quantityMap) {
            auto& qty(*p.second);
            qty.set0(qty.get0(indexThere), indexHere);
        }
    }
}



void SDDistributed::execEquation(std::string eqName) {

    _threadPool->start(eqName);
}

void SDDistributed::initThreadPool(unsigned int nThreads, unsigned int nCommonSDS) {

    assert(nThreads > 0);
    _threadPool = std::unique_ptr<ThreadPool>(new ThreadPool(std::forward<unsigned int>(nThreads), std::forward<unsigned int>(nCommonSDS)));
}

void SDDistributed::setValue(std::string quantityName,
        int coordX, int coordY, real value) {

    _quantityMap.at(quantityName)->set(value, 0, coordX, coordY);
}

real SDDistributed::getValue(std::string quantityName,
        int coordX, int coordY) const {

    return _quantityMap.at(quantityName)->get(0, coordX, coordY);
}
