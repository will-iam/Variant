#ifndef QUANTITYAOS_HPP
#define QUANTITYAOS_HPP

/*!
 * @file:
 *
 * @brief Defines class for physical quantities used in a numerical scheme
 *
 * Defines the class Quantity and the interface for multi-types
 * storable Quantity instances
 */

#include <iostream>
#include <map>
#include <vector>
#include <list>
#include <cassert>

#include "CoordConverter.hpp"


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
template<typename T> class Quantity {
  public:

    /*!
     * @brief Constructor
     *
     * @param size : size of the created array
     * @param coordConverter : tool linking coordinates of a
     * cell/node to the corresponding memory index
     */
    void init(std::list<std::string>& quantityList, unsigned int size, const CoordConverter & coordConverter);

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
     */

    void set(T value, unsigned int n, int coordX, int coordY);

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
    size_t set(size_t index, std::vector<T> valueVector, unsigned int n, int coordX, int coordY);

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
    unsigned int _size = 0;

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

    /*!
    * List of names of the quantities stored in this structure.
    */
    std::vector<std::string> _quantityNameVect;
    std::map<std::string, size_t> _nameIndexMap;
    size_t _quantityNumber = 0;
};

template<typename T>
void Quantity<T>::init(std::list<std::string>& quantityList, unsigned int size, const CoordConverter & coordConverter)
{
    assert(_size == 0);
    assert(_quantityVect.empty());
    assert(_quantityNumber == 0);

    _quantityNumber = quantityList.size();

    _quantityNameVect.reserve(_quantityNumber);
    for (const std::string& s : quantityList)
        _quantityNameVect.push_back(s);

    for (size_t i = 0; i < _quantityNameVect.size(); ++i)
        _nameIndexMap[_quantityNameVect[i]] = i;

    _size = size * _quantityNumber;
    _coordConverter = coordConverter;

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

template<typename T>
std::vector<T> Quantity<T>::getVector(unsigned int n, int coordX, int coordY) const
{
    unsigned int i = _coordConverter.convert(coordX, coordY);
    if (n == 0) {
        std::vector<T>::const_iterator first = _prev->begin() + i;
        std::vector<T>::const_iterator last = _prev->begin() + i + _quantityNumber;
        return std::vector<T>(first, last);
    }

    std::vector<T>::const_iterator first = _next->begin() + i;
    std::vector<T>::const_iterator last = _next->begin() + i + _quantityNumber;
    return std::vector<T>(first, last);
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
size_t Quantity<T>::set(size_t index, std::vector<T> valueVector, unsigned int n, int coordX, int coordY) {

    unsigned int i = _coordConverter.convert(coordX, coordY);

    if (n == 0) {
        for (size_t pos(0); pos < _quantityNumber; ++pos)
            (*_prev)[i + pos] = valueVector[index + pos];
    }
    else {
        for (size_t pos(0); pos < _quantityNumber; ++pos)
            (*_next)[i + pos] = valueVector[index + pos];
    }

    return index + _quantityNumber;
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
