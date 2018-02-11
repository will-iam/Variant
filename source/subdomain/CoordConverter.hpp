#ifndef COORDCONVERTER_HPP
#define COORDCONVERTER_HPP

/*!
 * @file
 * @brief Defines class for the converter
 * 2D-coordinates -> memory index
 */

/*!
 * @brief Converts 2D-coordinates to memory index for
 * given SDD size
 *
 * The data on the SDD is stored as a one-dimensional
 * array, hence the need of a converter.
 */
class CoordConverter {
  public:
    CoordConverter() = default;

    /*!
     * @brief Constructor
     *
     * @param sizeSDD_X : width of SDD
     * @param sizeSDD_Y : height of SDD
     */
    CoordConverter(unsigned int sizeSDD_X, unsigned int sizeSDD_Y,
            unsigned int boundaryThickness);
    /*!
     * @brief Copy constructor
     *
     * @param coordConverter : coordinates converter to copy
     */
    CoordConverter(const CoordConverter& coordConverter);

    /*!
     * @brief convert 2D-coordinates to the memory index of
     * the data on the SDD
     */
    unsigned int convert(int coordX, int coordY) const;

  private:

    /*!
     * width of SDD
     */
    unsigned int _sizeSDD_X;
    /*!
     * height of SDD
     */
    unsigned int _sizeSDD_Y;
    unsigned int _boundaryThickness;

};

#endif
