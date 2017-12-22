#ifndef QUANTITY_HPP
#define QUANTITY_HPP

/*!
 * @file:
 *
 * @brief Defines class for physical quantities used in a numerical scheme
 *
 * Defines the class Quantity and the interface for multi-types
 * storable Quantity instances
 */

#include <iostream>
#include <vector>

#include "CoordConverter.hpp"
//#include "SDShared.hpp"

/*!
 * @brief Interface for storing multi-type quantity in the same array.
 */
class QuantityInterface {
  public:
    /*!
     * Virtual destructor
     */
    virtual ~QuantityInterface() {};
};

template<typename T> class Quantity;

/*!
 * @brief Physical quantity used in numerical schemes.
 *
 * Templated class defining a physical quantity of a certain
 * size to be defined on the discrete domain, and its storage
 * in memory. The typename defines the type of the stored
 * values.
 * It contains two arrays of data as required by a scheme
 * of order 1 in time, and switches between them to avoid
 * unnecesary writing.
 */
template<typename T> class Quantity:public QuantityInterface {
  public:

    /*!
     * @brief Constructor
     *
     * @param size : size of the created array
     * @param coordConverter : tool linking coordinates of a 
     * cell/node to the corresponding memory index
     */
    Quantity(unsigned int size, const CoordConverter & coordConverter);

    /*!
     * @brief Returns desired data available for reading
     * and writing using the SDD's coord converter
     *
     * @param n : returns current data if n == 0, next data if n == 1 
     * @param coordX : X-axis coordinate on domain
     * @param coordY : Y-axis coordinate on domain
     *
     * @return reference to the desired data
     */
    const T& get(unsigned int n, int coordX, int coordY) const;

    /*!
     * @brief Returns desired data available for reading
     * and writing using a specific SDS's coord converter
     * (see class SDShared)
     *
     * @param n : returns previous data if n == 0, next data if n == 1 
     * @param coordX : X-axis coordinate on domain
     * @param coordY : Y-axis coordinate on domain
     *
     * @return reference to the desired data
     */
    //const T& get(unsigned int n, int coordX, int coordY, const SDShared & sds) const;

    void set(T value, unsigned int n, int coordX, int coordY);
    //void set(T value, unsigned int n, int coordX, int coordY, const SDShared & sds);

    /*!
     * @brief To be called when an iteration is done to switch between
     * arrays of data.
     */
    void switchPrevNext();

    int currentPrev() const;

    
    const T& get0(unsigned int pos) const;
    const T& get1(unsigned int pos) const;
    void set1(T value, unsigned int pos);

  private:

    /*!
     * size of data array
     */
    unsigned int _size;

    /*!
     * pointer to the current data (t = t)
     * (read only)
     */
    std::vector<T> *_prev;
    /*!
     * pointer to the next data (t = t + dt)
     */
    std::vector<T> *_next;

    /*!
     * first array of data containing either
     * current or next data
     */
    std::vector<T> _dataLeft;
    /*!
     * second array of data containing either
     * current or next data
     */
    std::vector<T> _dataRight;

    /*!
     * Copy of coordinates converter owned by the SDD
     */
    CoordConverter _coordConverter;
};

template<typename T>
Quantity<T>::Quantity(unsigned int size,
        const CoordConverter & coordConverter):_size(size), _coordConverter(coordConverter)
{
    _dataLeft.resize(_size);
    _dataRight.resize(_size);

    _prev = &_dataLeft;
    _next = &_dataRight;
}

template<typename T>
int Quantity<T>::currentPrev() const {
    return (_prev == &_dataLeft) ? 0 : 1;
}

template<typename T> void Quantity<T>::switchPrevNext()
{
    std::vector<T>* _tmp = _prev;
    _prev = _next;
    _next = _tmp;
}

template<typename T>
const T& Quantity<T>::get(unsigned int n, int coordX, int coordY) const
{
    unsigned int i = _coordConverter.convert(coordX, coordY);
    return (n == 0) ? (*_prev)[i] : (*_next)[i];
}

template<typename T> void Quantity<T>::set(T value,
        unsigned int n, int coordX, int coordY) {

    unsigned int i = _coordConverter.convert(coordX, coordY);

    if (n == 0)
        (*_prev)[i] = value;
    else
        (*_next)[i] = value;
}

template<typename T>
const T& Quantity<T>::get0(unsigned int pos) const {
    return (*_prev)[pos];
}

template<typename T>
const T& Quantity<T>::get1(unsigned int pos) const {
    return (*_next)[pos];
}

template<typename T>
void Quantity<T>::set1(T value, unsigned int pos) {
    (*_next)[pos] = value;
}

#endif
