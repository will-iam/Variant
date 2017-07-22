#ifndef IO_HPP
#define IO_HPP

/*!
 * @file:
 *
 * @brief Input/Output tools
 *
 * Contains tools to read and write domain, physical quantities,
 * scheme info, etc.
 */
#include <string>
#include <vector>
#include <iostream>

#include "Domain.hpp"
#include "SDDistributed.hpp"
#include "engine.hpp"

void stor(std::string tmpStr, float& target);
void stor(std::string tmpStr, double& target);
void stor(std::string tmpStr, long double& target);

/*!
 * @brief Namespace containing all input/output tools
 */
namespace IO {

    /*!
     * @brief Loads domain info and writes all necessary
     *
     * Data is written into file directory/domain.dat
     *
     * @param directory input folder
     * @param domain domain to be updated with read data
     *
     * @return 0 if loading succeeded, -1 otherwise
     */
    int loadDomainInfo(std::string directory, Domain& domain);
    /*!
     * @brief Writes domain info to output directory
     *
     * Data is written into file directory/domain.dat
     *
     * @param directory destination folder
     * @param domain domain data
     *
     * @return 0 if writing succeeded, -1 otherwise
     */
    int writeDomain(std::string directory, const Domain& domain); 

    /*!
     * @brief Loads scheme info 
     *
     * Loaded parameters are:
     *  - final time T
     *  - CFL condition
     *
     *  @param directory input folder
     *  @param engine scheme engine 
     *
     * @return 0 if loading succeeded, -1 otherwise
     */
    int loadSchemeInfo(std::string directory, Engine& engine);

    /*!
     * @brief Loads execution options
     *
     * Loaded parameters are:
     *  - number of SDDs
     *  - number of SDSs
     *  - SDS geometry
     *
     *  @param directory input folder
     *  @param domain domain
     *
     * @return 0 if loading succeeded, -1 otherwise
     */
    int loadExecOptions(std::string directory, Domain& domain);

    /*!
     *
     */ 
    int loadSDDInfo(std::string directory, Domain& domain);

    /*!
     * @brief Loads quantity data from file directory/quantityName.dat
     *
     * @param directory input folder
     * @param quantityName string name of quantity to be written
     * @param domain domain
     */
    int loadQuantity(std::string directory,
            std::string quantityName,
            Domain& domain,
            bool constant = false);
    /*!
     * @brief Writes quantity data into output file
     *
     * @param directory destination folder
     * @param quantityName  name of the quantity to output
     * @param domain  domain data
     *
     * @return 0 if writing succeeded, -1 otherwise
     */
    int writeQuantity(std::string directory,
            std::string quantityName,
            const Domain& domain);

    /*!
     * @brief Loads boundary conditions
     *
     * @param directory destination folder
     * @param domain domain data
     */
    int loadBoundaryConditions(std::string directory,
            Domain& domain);
    /*!
     * @brief Writes boundary conditions for quantity
     *
     * @param directory destination folder
     * @param quantityName name of the quantity to output
     * @param domain domain data
     *
     * @return 0 if writing succeeded, -1 otherwise
     */
    //int writeBoundaryConditions(std::string directory,
    //        std::string quantityName, const Domain& domain);
    
    int writePerfResults(std::string directory,
            const std::map<std::string, double> results);

}

#endif
