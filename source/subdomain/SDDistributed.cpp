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

    return _neumannCellMap.size() + _dirichletCellMap.size();
}

void SDDistributed::buildAllSDS(unsigned int nSDS, std::string geomType) {

    std::vector< std::vector< std::pair<int, int> > >
        geom = _geometry.buildGeometry(nSDS, geomType);
    int i = 0;
    for (auto it = geom.begin(); it != geom.end(); ++it) {
        _SDSList.push_back(SDShared(*it, _coordConverter, i));
        i++;
    }
    /// Shuffling SDS List
    std::random_shuffle(_SDSList.begin(), _SDSList.end());
}

void SDDistributed::addEquation(std::string eqName, eqType eqFunc) {

    for (auto& sds: _SDSList) {

        _threadPool->addTask(eqName, std::bind(&SDShared::execEquation, sds, eqFunc, _quantityMap));
    }

}

const std::vector<SDShared>& SDDistributed::getSDS() const {

    return _SDSList;
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

    /* Original Version with allocation.
    // Send and Receive the data.
    std::map<int, MPI_Status> statusMap;
    for (auto& toSDD: _recvSendBuffer) {
        toSDD.second.first.resize(toSDD.second.second.size());
        // Init recv buffer size
        MPI_Sendrecv(&toSDD.second.second[0], toSDD.second.second.size(),
                        MPI_REALTYPE, toSDD.first, _id * _nSDD + toSDD.first,
                     &toSDD.second.first[0], toSDD.second.first.size(),
                        MPI_REALTYPE, toSDD.first, toSDD.first * _nSDD + _id,
                     MPI_COMM_WORLD, &statusMap[toSDD.first]);
    }*/

    /* Original Version without allocation
    // Send and Receive the data.
    for (auto& toSDD: _recvSendBuffer) {
        toSDD.second.first.resize(toSDD.second.second.size());
        // Init recv buffer size
        MPI_Sendrecv(&toSDD.second.second[0], toSDD.second.second.size(),
                        MPI_REALTYPE, toSDD.first, _id * _nSDD + toSDD.first,
                     &toSDD.second.first[0], toSDD.second.first.size(),
                        MPI_REALTYPE, toSDD.first, toSDD.first * _nSDD + _id,
                     MPI_COMM_WORLD, &status);
    }*/

    /*
    // Version with send and recv split.
    for (auto& toSDD: _recvSendBuffer) {
        toSDD.second.first.resize(toSDD.second.second.size());
        // Init recv buffer size
        MPI_Send(&toSDD.second.second[0], toSDD.second.second.size(),
                        MPI_REALTYPE, toSDD.first, _id * _nSDD + toSDD.first, MPI_COMM_WORLD);

        MPI_Recv(&toSDD.second.first[0], toSDD.second.first.size(),
                        MPI_REALTYPE, toSDD.first, toSDD.first * _nSDD + _id,
                     MPI_COMM_WORLD, &status);
    } */

   /*
   // Version with send and recv split: deadlock ...
    for (const auto& toSDDid: _neighbourSDDVector) {
        auto& data = _recvSendBuffer[toSDDid];

        // Init recv buffer size
        data.first.resize(data.second.size());

        MPI_Recv(&data.first[0], data.first.size(), MPI_REALTYPE,
            toSDDid, toSDDid * _nSDD + _id,
            MPI_COMM_WORLD, &status);

        MPI_Send(&data.second[0], data.second.size(),MPI_REALTYPE,
            toSDDid, _id * _nSDD + toSDDid,
            MPI_COMM_WORLD);
    }*/

    /* Première version avec Isend, Irecv: toujours autant de communications.
    for (auto& toSDD: _recvSendBuffer) {
        // Init recv buffer size
        toSDD.second.first.resize(toSDD.second.second.size());
        MPI_Request revc_request, send_request;

        MPI_Irecv(&toSDD.second.first[0], toSDD.second.first.size(),
                        MPI_REALTYPE, toSDD.first, toSDD.first * _nSDD + _id,
                     MPI_COMM_WORLD, &revc_request);

        MPI_Isend(&toSDD.second.second[0], toSDD.second.second.size(),
            MPI_REALTYPE, toSDD.first, _id * _nSDD + toSDD.first, MPI_COMM_WORLD, &send_request);

        MPI_Wait(&revc_request, &status);
        MPI_Wait(&send_request, &status);
    }
    */

    /*
    size_t i = 0;
    MPI_Request requestArray[8];
    MPI_Status statusArray[8];

    for (auto& toSDD: _recvSendBuffer) {
        // Init recv buffer size
        toSDD.second.first.resize(toSDD.second.second.size());
        MPI_Request revc_request, send_request;

        MPI_Irecv(&toSDD.second.first[0], toSDD.second.first.size(),
                        MPI_REALTYPE, toSDD.first, toSDD.first * _nSDD + _id,
                     MPI_COMM_WORLD, &requestArray[i++]);

        MPI_Isend(&toSDD.second.second[0], toSDD.second.second.size(),
            MPI_REALTYPE, toSDD.first, _id * _nSDD + toSDD.first, MPI_COMM_WORLD, &requestArray[i++]);
    }
    MPI_Waitall(i, requestArray, statusArray);*/

    size_t i = 0;
    for (const auto& toSDDid: _neighbourSDDVector) {
        auto& data = _recvSendBuffer[toSDDid];

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
    //MPI_Barrier(MPI_COMM_WORLD);
}

void SDDistributed::updateNeumannCells(std::string quantityName, bool changeToOpposite) {

    if (_neumannCellMap.empty())
        return;

    Quantity<real>* quantity = getQuantity(quantityName);

    for (auto it = _neumannCellMap.begin(); it != _neumannCellMap.end(); ++it) {
        std::pair<int, int> coords = it->first;
        std::pair<int, int> targetCoords = it->second;

        if (changeToOpposite) {
            quantity->set(-quantity->get(0, targetCoords.first, targetCoords.second),
                    0, coords.first, coords.second);
        }
        else {
            quantity->set(quantity->get(0, targetCoords.first, targetCoords.second),
                    0, coords.first, coords.second);
        }
    }
}

void SDDistributed::updateDirichletCells(std::string quantityName) {

    if (_dirichletCellMap.empty())
        return;

    Quantity<real>* quantity = _quantityMap[quantityName];

    for (auto it = _dirichletCellMap.begin();
            it != _dirichletCellMap.end(); ++it) {

        std::pair<int, int> coords = it->first;
        quantity->set(it->second, 0, coords.first, coords.second);
    }
}

void SDDistributed::execEquation(std::string eqName) {

    _threadPool->start(eqName);
}

void SDDistributed::initThreadPool(unsigned int nThreads) {

    assert(nThreads > 0);
    _threadPool = std::unique_ptr<ThreadPool>(new ThreadPool(std::forward<unsigned int>(nThreads)));
}

void SDDistributed::setValue(std::string quantityName,
        int coordX, int coordY, real value) {

    _quantityMap.at(quantityName)->set(value, 0, coordX, coordY);
}

real SDDistributed::getValue(std::string quantityName,
        int coordX, int coordY) const {

    return _quantityMap.at(quantityName)->get(0, coordX, coordY);
}
