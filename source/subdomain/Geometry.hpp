#ifndef GEOMETRY_HPP
#define GEOMETRY_HPP

/*!
 * @file:
 *
 * @brief Defines Geometry class for SDSs.
 */
#include <vector>
#include <string>

/*!
 * @brief Tool providing various splits of SDDs (rectangular shapes) into SDS (any
 * shape)
 */
class Geometry {

  public:

    /*!
     * Constructor
     *
     * @param bottomLeftX X-coord of bottem-left point of SDD
     * @param bottomLeftX Y-coord of bottem-left point of SDD
     * @param sizeX width of SDD
     * @param sizeY height of SDD
     */
    Geometry(int bottomLeftX, int bottomLeftY,
            unsigned int sizeX, unsigned int sizeY);

    /*!
     * build Geometry according to number and type of shapes
     *
     * @param nShapes number of SDS shapes to create
     * @param geomType type of geometry to build
     */
    std::vector< std::vector< std::pair<int, int> > > buildGeometry(unsigned int nShapes, std::string geomType);

    static const std::string LINE;
    static const std::string RECTANGLE;
    static const std::string RANDOM;
    static const std::string DIAGONAL;
    static const std::string TRIANGLE;
    static const std::string AMR;

  private:

    std::vector< std::pair<int, int> >
        buildRectangle(int bottomLeftX, int bottomLeftY,
            unsigned int sizeX, unsigned int sizeY);

    std::vector< std::pair<int, int> >
        buildLine(int firstX, int firstY, unsigned int length);

    bool inRect(int i, int j);

    int _bottomLeftX;
    int _bottomLeftY;
    int _topRightX;
    int _topRightY;
    unsigned int _sizeX;
    unsigned int _sizeY;
};

#endif

