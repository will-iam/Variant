#include "CoordConverter.hpp"
#include <iostream>

CoordConverter::CoordConverter(unsigned int sizeSDD_X,
        unsigned int sizeSDD_Y,
        unsigned int boundaryThickness):
    _sizeSDD_X(sizeSDD_X),
    _sizeSDD_Y(sizeSDD_Y),
    _boundaryThickness(boundaryThickness) {

}

CoordConverter::CoordConverter(const CoordConverter& coordConverter):
    _sizeSDD_X(coordConverter._sizeSDD_X),
    _sizeSDD_Y(coordConverter._sizeSDD_Y),
    _boundaryThickness(coordConverter._boundaryThickness) {

}

unsigned int CoordConverter::convert(int coordX, int coordY) const {

    return (coordX + _boundaryThickness) + (coordY + _boundaryThickness) * (_sizeSDD_X + 2 * _boundaryThickness);
    //return (coordY + _boundaryThickness) + (coordX + _boundaryThickness) * _sizeSDD_Y;
}

