#ifndef QUANTITY_HPP
#define QUANTITY_HPP

/*!
 * @file:
 *
 * @brief Defines class for physical quantities used in a numerical scheme
 *
 */


#ifdef QUANTITY_SoA
#include "QuantitySoA.tcc"
#endif

#ifdef QUANTITY_AoS
#include "QuantityAoS.tcc"
#endif

#endif
