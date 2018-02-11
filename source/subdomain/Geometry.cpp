#include "Geometry.hpp"

#include <iostream>
#include <algorithm>
#include <cstdlib>
#include <cmath>
#include <cassert>

const std::string Geometry::LINE = "line";
const std::string Geometry::RECTANGLE = "rectangle";
const std::string Geometry::RANDOM = "random";
const std::string Geometry::DIAGONAL = "diagonal";
const std::string Geometry::TRIANGLE = "triangle";
const std::string Geometry::AMR = "amr";

Geometry::Geometry(int bottomLeftX, int bottomLeftY,
            unsigned int sizeX, unsigned int sizeY):
    _bottomLeftX(bottomLeftX),
    _bottomLeftY(bottomLeftY),
    _topRightX(bottomLeftX + sizeX - 1),
    _topRightY(bottomLeftY + sizeY - 1),
    _sizeX(sizeX),
    _sizeY(sizeY) {
}

std::vector< std::vector< std::pair<int, int> > >
Geometry::buildGeometry(unsigned int nShapes, std::string geomType) {

    nShapes = std::min<unsigned int>(nShapes, _sizeX * _sizeY);

    std::vector< std::vector< std::pair<int, int> > > geometry;
    geometry.reserve(nShapes);

    if(geomType == RANDOM) {
        // Building whole rectangle and shuffling it
        // to get random coords
        unsigned int shapeSize = (_sizeX * _sizeY) / nShapes;
        std::vector<std::pair <int, int> >
            allRect = buildRectangle(_bottomLeftX, _bottomLeftY,
                    _sizeX, _sizeY);
        std::random_shuffle(allRect.begin(), allRect.end());

        std::vector< std::pair<int, int> > randomShape;
        for (unsigned int i = 0; i < nShapes - 1; i++) {
            for (unsigned int j = 0; j < shapeSize; j++) {
                randomShape.push_back(allRect.back());
                allRect.pop_back();
            }
            geometry.push_back(randomShape);
            randomShape.clear();
        }
        // For the last line, we push it all the way
        int i = 0;
        for (std::vector< std::pair<int, int> >::reverse_iterator
                it = allRect.rbegin(); it != allRect.rend(); ++it) {
            randomShape.push_back(*it);
            ++i;
        }
        geometry.push_back(randomShape);

        int totalSize = 0;
        for (unsigned int i = 0; i < geometry.size(); i++) {
            totalSize += geometry[i].size();
        }
    } else {
        // build lines

        // In order to have balance between shapes, we
        // build lines of shape :
        //      Ncells = L * n + (L - 1) * m
        // With n + m = nShapes
        // Which gives
        //      Ncells = nShapes * (L - 1) + n
        unsigned int L = _sizeX * _sizeY / nShapes + 1;
        unsigned int n = _sizeX * _sizeY % nShapes;
        unsigned int m = nShapes - n;
        int firstX = _bottomLeftX;
        int firstY = _bottomLeftY;

        // First n lines : length L
        for (unsigned int i = 0; i < n; i++) {
            geometry.push_back(buildLine(firstX, firstY, L));
            // Determine next firstX and firstY
            for (unsigned int k = 0; k < L; k++) {
                firstX++;
                if (firstX > _topRightX) {
                    firstX = _bottomLeftX;
                    firstY++;
                }
            }
        }

        // Last m lines : length L - 1
        for (unsigned int i = 0; i < m; i++) {
            geometry.push_back(buildLine(firstX, firstY, L - 1));
            // Determine next firstX and firstY
            for (unsigned int k = 0; k < L - 1; k++) {
                firstX++;
                if (firstX > _topRightX) {
                    firstX = _bottomLeftX;
                    firstY++;
                }
            }
        }
    }

    return geometry;

}

std::vector< std::pair<int, int> > Geometry::buildRectangle(int bottomLeftX, int bottomLeftY,
        unsigned int sizeX, unsigned int sizeY) {

    std::vector< std::pair<int, int> > rect;
    for (unsigned int j = 0; j < sizeY; j++) {
        for (unsigned int i = 0; i < sizeX; i++) {
            rect.push_back(std::pair<int, int>(i + bottomLeftX, j + bottomLeftY));
        }
    }
    return rect;
}

std::vector< std::pair<int, int> >
Geometry::buildLine(int firstX, int firstY, unsigned int length) {

    std::vector< std::pair<int, int> > line;
    // Return empty vector if first point is not in rectangle
    if (!inRect(firstX, firstY))
        return line;
    int i = firstX;
    int j = firstY;
    length = std::min<unsigned int>(_topRightX - firstX + _sizeX * (_topRightY - firstY) + 1, length);
    for (unsigned int k = 0; k < length; k++) {
        line.push_back(std::pair<int, int>(i, j));
        i++;
        if (i > _topRightX) {
            i = _bottomLeftX;
            j++;
        }
    }
    return line;
}

bool Geometry::inRect(int i, int j) {

    return (i >= _bottomLeftX && i <= _topRightX
         && j >= _bottomLeftY && j <= _topRightY);
}
