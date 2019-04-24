#include <iomanip>
#include <cassert>
#include "SDShared.hpp"
#include "exception/exception.hpp"

SDShared::SDShared(const std::vector< std::pair<int, int> >& coords,
        const CoordConverter& coordConverter,
        unsigned int index):
    std::vector< std::pair<int ,int> >(coords),
    _coordConverter(coordConverter),
    _id(index) {
}

void SDShared::execEquation(eqType& eqFunc,
        const std::map< std::string, Quantity<real>* >& quantityMap) {

    eqFunc(*this, quantityMap);
}

void SDShared::addDirichletCell(std::pair < std::pair<int, int>, std::map<std::string, real> > d) {
    for (auto p : d.second)
        _dirichletCellMap[p.first][convert(d.first.first, d.first.second)] = p.second;
}

void SDShared::addTimeVaryingCell(std::pair < std::pair<int, int>, std::map<std::string, real> > d) {
    for (auto p : d.second)
        _timeVaryingCellMap[p.first][convert(d.first.first, d.first.second)] = p.second;
}

void SDShared::addNeumannCell(std::pair< std::pair<int, int>, std::pair< std::pair<int, int>, std::map<std::string, real> > > n) {
    for (auto p : n.second.second)
        _neumannCellMap[p.first][convert(n.first.first, n.first.second)] = std::make_pair(convert(n.second.first.first, n.second.first.second), p.second);
}

size_t SDShared::getOverlapCellNumber(unsigned int sddId) const {
    if (_sendIndexMap.find(sddId) == _sendIndexMap.end())
        return 0;

    return _sendIndexMap.at(sddId).size();
}

void SDShared::addOverlapCell(unsigned int sddId, size_t sendIndex, size_t recvIndex) {
    _sendIndexMap[sddId].push_back(sendIndex);
    _recvIndexMap[sddId].push_back(recvIndex);
}

void SDShared::updateBoundaryCells(Quantity<real>* quantity, const real& t) const {
    updateDirichletCells(quantity);
    updateNeumannCells(quantity);
    updateTimeVaryingCells(quantity, t);
}

void SDShared::updateDirichletCells(Quantity<real>* quantity) const {
    auto& qty(*quantity);

    // No dirichlet values stored for this quantity.
    std::map<std::string, std::unordered_map< size_t, real >>::const_iterator it = _dirichletCellMap.find(qty.getName());
    if (it == _dirichletCellMap.end())
        return;

    const std::unordered_map< size_t, real>& dirichletValue = it->second;

    // This cannot be.
    assert(dirichletValue.size() != 0);

    for (auto it = dirichletValue.begin(); it != dirichletValue.end(); ++it)
        qty.set0(it->second, it->first);
}

void SDShared::updateTimeVaryingCells(Quantity<real>* quantity, const real& t) const {
    auto& qty(*quantity);

    // No dirichlet values stored for this quantity.
    std::map<std::string, std::unordered_map< size_t, real >>::const_iterator it = _timeVaryingCellMap.find(qty.getName());
    if (it == _timeVaryingCellMap.end())
        return;

    const std::unordered_map< size_t, real>& parameterValue = it->second;

    // This cannot be.
    assert(parameterValue.size() != 0);

    for (auto it = parameterValue.begin(); it != parameterValue.end(); ++it) {
        real v = 1. + it->second * t;
        //std::cout << "v: " << std::defaultfloat << std::setprecision(Number::max_digits10) << v << std::endl;
        qty.set0(v, it->first);
    }
}

void SDShared::updateNeumannCells(Quantity<real>* quantity) const {

    auto& qty(*quantity);

    // No dirichlet values stored for this quantity.
    std::map<std::string, std::unordered_map< size_t, std::pair<size_t, real>>>::const_iterator cit = _neumannCellMap.find(qty.getName());
    if (cit == _neumannCellMap.end())
        return;

    const std::unordered_map< size_t, std::pair<size_t, real>>& neumannCoeff = cit->second;

    // This cannot be.
    assert(neumannCoeff.size() != 0);

    for (auto it = neumannCoeff.begin(); it != neumannCoeff.end(); ++it) {
        qty.set0(it->second.second * qty.get0(it->second.first), it->first);
    }
}

void SDShared::copyOverlapCellIn(const std::map< std::string, Quantity<real>* >& quantityMap, const std::unordered_map<unsigned int, real* >& buffer) const {

    const size_t plus(quantityMap.size());
    for (auto const& it: _sendIndexMap) {
        size_t startPos(_bufferStartPos.at(it.first) * quantityMap.size());
        real* sddBuffer(buffer.at(it.first));
        for (const auto p: quantityMap) {
            auto& qty(*p.second);
            size_t index(startPos++);
            for (const unsigned int i : it.second) {
                sddBuffer[index] = qty.get0(i);
                index += plus;
            }
        }
    }
}

void SDShared::copyOverlapCellFrom(const std::map< std::string, Quantity<real>* >& quantityMap, const std::unordered_map<unsigned int, real* >& buffer) const {
    const size_t plus(quantityMap.size());
    for (auto const& it: _recvIndexMap) {
        real* sddBuffer(buffer.at(it.first));
        size_t startPos(_bufferStartPos.at(it.first) * plus);
        for (const auto p: quantityMap) {
            auto& qty(*p.second);
            size_t index(startPos++);
            for (const unsigned int i : it.second) {
                qty.set0(sddBuffer[index], i);
                index += plus;
            }
        }
    }
}
