#include "SDShared.hpp"

SDShared::SDShared(unsigned int bottomLeft_X, unsigned int bottomLeft_Y,
                   unsigned int sizeX, unsigned int sizeY,
                   const CoordConverter& coordConverter,
                   unsigned int id):
    std::vector< std::pair<int, int> >(),
    _coordConverter(coordConverter),
    _id(id)
{
    reserve(sizeX * sizeY);
    // Building coordinates contained by SDS
    for (unsigned int i = 0; i < sizeX; i++) {
        for (unsigned int j = 0; j < sizeY; j++) {
            push_back(std::pair<int, int>(bottomLeft_X + i, bottomLeft_Y + j));
        }
    }
}

SDShared::SDShared(const std::vector< std::pair<int, int> >& coords,
        const CoordConverter& coordConverter,
        unsigned int index):
    std::vector< std::pair<int ,int> >(coords),
    _coordConverter(coordConverter),
    _id(index) {
}

unsigned int SDShared::getMemIndex(int i, int j) const {

    return _coordConverter.convert(i, j);
}

unsigned int SDShared::getId() const {

    return _id;
}

void SDShared::execEquation(eqType eqFunc,
        const std::map< std::string, Quantity<real>* >& quantityMap) {

    eqFunc(*this, quantityMap);
}
