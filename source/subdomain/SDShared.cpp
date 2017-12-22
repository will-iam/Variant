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
    _dirichletCellMap[d.first] = d.second;
}

void SDShared::addNeumannCell(std::pair< std::pair<int, int>, std::pair<int, int> > n) {
    _neumannCellMap[n.first] = n.second;
}

void SDShared::updateBoundaryCells(Quantity<real>* quantity, bool changeNeumannToOpposite) const {

    updateDirichletCells(quantity);
    updateNeumannCells(quantity, changeNeumannToOpposite);
}

void SDShared::updateDirichletCells(Quantity<real>* quantity) const {

    if (_dirichletCellMap.empty())
        return;

    for (auto it = _dirichletCellMap.begin(); it != _dirichletCellMap.end(); ++it) {
        const auto coords = it->first;
        quantity->set(it->second, 0, coords.first, coords.second);
    }
}

void SDShared::updateNeumannCells(Quantity<real>* quantity, bool changeToOpposite) const {

    if (_neumannCellMap.empty())
        return;

    if (changeToOpposite) {
        for (auto it = _neumannCellMap.begin(); it != _neumannCellMap.end(); ++it) {
            const auto& coords = it->first;
            const auto& targetCoords = it->second;
            quantity->set(-quantity->get(0, targetCoords.first, targetCoords.second), 0, coords.first, coords.second);
        }
    } else {
        for (auto it = _neumannCellMap.begin(); it != _neumannCellMap.end(); ++it) {
            const auto& coords = it->first;
            const auto& targetCoords = it->second;
            quantity->set(quantity->get(0, targetCoords.first, targetCoords.second), 0, coords.first, coords.second);
        }
   }
}
