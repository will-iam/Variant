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

    delete[] _requestArray;
    delete[] _statusArray;

    for (auto it =
         _quantityMap.begin(); it != _quantityMap.end(); ++it)
        delete(it->second);
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
    // std::random_shuffle(_SDSVector.begin(), _SDSVector.end());
}

void SDDistributed::dispatchBoundaryCell(const std::map< std::pair<int, int>, real >& dirichletCellMap,
        const std::map< std::pair<int, int>, std::pair<int, int> >& neumannCellMap) {
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

    //for (size_t i = 0; i < _SDSVector.size(); ++i)
    //    std::cout << "SDS: " << i << " has " << _SDSVector[i].getNumberBoundaryCells() << " boundary cells.\n";
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

void SDDistributed::updateOverlapCells(const std::vector<std::string>& qtiesToUpdate) {

    // Clear and reserve here
    for (auto& toSDD: _recvSendBuffer) {
	    toSDD.second.first.clear();
        toSDD.second.second.clear();
    }

    // Copy data to send in the buffer.
    for (auto const& it: _MPISend_map) {
        unsigned int SDDid = it.first.first;
        for (const auto& qtyName: qtiesToUpdate) {
            const Quantity<real>& qty = *_quantityMap[qtyName];
            std::pair<int, int> coordsHere = it.second;
            _recvSendBuffer[SDDid].second.push_back(qty.get(0, coordsHere.first, coordsHere.second));
        }
    }

    size_t i = 0;
    for (const auto& toSDDid: _neighbourSDDVector) {
        auto& data = _recvSendBuffer[toSDDid];

        //if (_id == 1)
        //    std::cout << "numberOfCellsToSend: " << data.second.size() << " from 1 to " << toSDDid << std::endl;

        // Init recv buffer size
        data.first.resize(data.second.size());

        MPI_Irecv(&data.first[0], data.first.size(),
                  MPI_REALTYPE, toSDDid, toSDDid * _nSDD + _id,
                  MPI_COMM_WORLD, &_requestArray[i++]);

        MPI_Isend(&data.second[0], data.second.size(),
                  MPI_REALTYPE, toSDDid, _id * _nSDD + toSDDid,
                  MPI_COMM_WORLD, &_requestArray[i++]);
    }
    MPI_Waitall(i, _requestArray, _statusArray);

    // Parsing recved message: updating cells
    std::map<int, int> bufIndices;
    for (auto const& it: _MPIRecv_map) {
        std::pair<int, int> coordsHere = it.first;
        unsigned int SDDid = it.second.first;
        if (_id == SDDid) {
            for (auto const& qtyName: qtiesToUpdate) {
                Quantity<real>& qty = *_quantityMap[qtyName];
                std::pair<int, int> coordsThere(it.second.second);
                qty.set(qty.get(0, coordsThere.first, coordsThere.second), 0, coordsHere.first, coordsHere.second);
            }
        }
        else {
            auto& v(_recvSendBuffer[SDDid].first);
            for (auto const& qtyName: qtiesToUpdate) {
                Quantity<real>& qty = *_quantityMap[qtyName];
                qty.set(v[bufIndices[SDDid]], 0, coordsHere.first, coordsHere.second);
                ++bufIndices[SDDid];
            }
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
