#include "SDShared.hpp"

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

void SDShared::addDirichletCell(std::pair < std::pair<int, int>, real > d) {
    _dirichletCellMap[convert(d.first.first, d.first.second)] = d.second;
}

void SDShared::addNeumannCell(std::pair< std::pair<int, int>, std::pair<int, int> > n) {
    _neumannCellMap[convert(n.first.first, n.first.second)] = convert(n.second.first, n.second.second);
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

void SDShared::updateBoundaryCells(Quantity<real>* quantity, bool changeNeumannToOpposite) const {
    updateDirichletCells(quantity);
    updateNeumannCells(quantity, changeNeumannToOpposite);
}

void SDShared::updateDirichletCells(Quantity<real>* quantity) const {

    if (_dirichletCellMap.empty())
        return;

    auto& qty(*quantity);
    for (auto it = _dirichletCellMap.begin(); it != _dirichletCellMap.end(); ++it)
        qty.set0(it->second, it->first);
}

void SDShared::updateNeumannCells(Quantity<real>* quantity, bool changeToOpposite) const {

    if (_neumannCellMap.empty())
        return;

    auto& qty(*quantity);
    if (changeToOpposite) {
        for (auto it = _neumannCellMap.begin(); it != _neumannCellMap.end(); ++it) {
            qty.set0(-qty.get0(it->second), it->first);
        }
    } else {
        for (auto it = _neumannCellMap.begin(); it != _neumannCellMap.end(); ++it) {
            qty.set0(qty.get0(it->second), it->first);
        }
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


