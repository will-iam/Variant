#include "IO.hpp"
#include "exception/exception.hpp"
#include "number/number.hpp"
#include <fstream>
#include <iomanip>
#include <limits>

void stor(std::string tmpStr, float& target) {
    target = std::stof(tmpStr);
}

void stor(std::string tmpStr, double& target) {
    target = std::stod(tmpStr);
}

void stor(std::string tmpStr, long double& target) {
    target = std::stold(tmpStr);
}

int IO::loadSDDInfo(std::string directory, Domain& domain) {

    int SDDid;
    MPI_Comm_rank(MPI_COMM_WORLD, &SDDid);
    std::ostringstream oss;
    oss << SDDid;

    std::ifstream ifs(directory + "/sdd" + oss.str() + "/sdd.dat", std::ios::in);
    std::string tmpStr;
    std::getline(ifs, tmpStr, ' ');
    unsigned int BL_X = std::stoi(tmpStr);
    std::getline(ifs, tmpStr);
    unsigned int BL_Y = std::stoi(tmpStr);
    std::getline(ifs, tmpStr, ' ');
    unsigned int Nx = std::stoi(tmpStr);
    std::getline(ifs, tmpStr);
    unsigned int Ny = std::stoi(tmpStr);

    domain.setSDDInfo(BL_X, BL_Y, Nx, Ny);

    return 0;
}

int IO::loadDomainInfo(std::string directory, Domain& domain) {

    // Read exec options
    std::ifstream ifs(directory + "/domain.info", std::ios::in);
    if (!ifs)
        std::cerr << "Failed to load domain info" << std::endl;
    std::string tmpStr;

    // First infos
    std::getline(ifs, tmpStr, ' ');
    real lx; stor(tmpStr, lx);
    std::getline(ifs, tmpStr, ' ');
    real ly; stor(tmpStr, ly);
    std::getline(ifs, tmpStr, ' ');
    unsigned int Nx = std::stoi(tmpStr);
    std::getline(ifs, tmpStr);
    unsigned int Ny = std::stoi(tmpStr);

    domain.initRect(lx, ly, Nx, Ny);
    ifs.close();

    return 0;
}

int IO::loadSchemeInfo(std::string directory, Engine& engine) {

    std::ifstream ifs(directory + "/scheme_info.dat", std::ios::in);
    std::string tmpStr;

    std::getline(ifs, tmpStr, ' ');
    real T; stor(tmpStr, T);
    std::getline(ifs, tmpStr);
    real CFL; stor(tmpStr, CFL);

    ifs.close();

    engine.setOptions(T, CFL);

    return 0;
}

int IO::loadExecOptions(std::string directory, Domain& domain) {

    std::ifstream ifs(directory + "/exec_options.dat", std::ios::in);
    if (!ifs) {
        std::cerr << "Could not load execution options" << std::endl;
        return 1;
    }
    std::string tmpStr;

    std::getline(ifs, tmpStr, ' ');
    unsigned int nSDD = std::stoi(tmpStr);
    std::getline(ifs, tmpStr, ' ');
    unsigned int nSDD_X = std::stoi(tmpStr);
    std::getline(ifs, tmpStr, ' ');
    unsigned int nSDD_Y = std::stoi(tmpStr);
    std::getline(ifs, tmpStr, ' ');
    unsigned int nSDS = std::stoi(tmpStr);
    std::getline(ifs, tmpStr, ' ');
    std::string SDSgeom = tmpStr;
    std::getline(ifs, tmpStr, ' ');
    unsigned int nThreads = std::stoi(tmpStr);
    std::getline(ifs, tmpStr, ' ');
    unsigned int nCommonSDS = std::stoi(tmpStr);
    ifs.close();

    domain.setOptions(nSDD, nSDD_X, nSDD_Y, nSDS, SDSgeom, nThreads, nCommonSDS);

    return 0;
}

int IO::loadQuantity(std::string directory, std::string quantityName, Domain& domain) {
    SDDistributed& sdd = domain.getSDD();
    domain.addQuantity(quantityName);

    std::ostringstream oss;
    oss << sdd.getId();

    std::ifstream ifs(directory + "/sdd" + oss.str() + "/" + quantityName + ".dat", std::ios::in);

    // If the file does not exist, SDD quantity will be initialized to 0.
    if (!ifs.is_open())
        return 0;
    
    std::string tmpStr;

    for (unsigned int i = 0; i < sdd.getSizeX(); ++i) {
        for (unsigned int j = 0; j < sdd.getSizeY(); ++j) {
            std::getline(ifs, tmpStr, ' ');
            int coordX = std::stoi(tmpStr);
            std::getline(ifs, tmpStr, ' ');
            int coordY = std::stoi(tmpStr);
            std::getline(ifs, tmpStr);
            real value; stor(tmpStr, value);

            sdd.setValue(quantityName, coordX, coordY, value);
        }
    }

    ifs.close();

    return 0;
}

int IO::loadBoundaryConditions(std::string directory, Domain& domain) {

    SDDistributed& sdd = domain.getSDD();
    std::ostringstream oss;
    oss << sdd.getId();
    std::ifstream ifs(directory + "/sdd" + oss.str() + "/bc.dat");
    if (!ifs)
        std::cerr << "Failed to open boundary conditions file" << std::endl;
    std::string tmpStr;

    // Reading unique id <-> coords correspondence
    while (std::getline(ifs, tmpStr)) {

        std::istringstream iss(tmpStr);
        unsigned int uid;   iss >> uid;
        int iCoord;         iss >> iCoord;
        int jCoord;         iss >> jCoord;
        char BCtype;        iss >> BCtype;
        real value;         iss >> value;

        domain.addBoundaryCoords(std::pair<int, int>(iCoord, jCoord), BCtype, value);
    }
    ifs.close();

    return 0;
}


int IO::writeQuantity(std::string directory,
        std::string quantityName, const Domain& domain) {

    const SDDistributed& sdd = domain.getSDDconst();

    std::ostringstream oss;
    oss << sdd.getId();
    std::ofstream ofs(directory + "/sdd" + oss.str() + "/" + quantityName + ".dat",
            std::ios::out);
    if (!ofs)
        std::cerr << "Failed to open file: " << std::endl;

    for (unsigned int i = 0; i < sdd.getSizeX(); ++i) {
        for (unsigned int j = 0; j < sdd.getSizeY(); ++j) {
            ofs << i << " " << j << " ";
#if defined(PRECISION_FLOAT)
            ofs << std::setprecision(std::numeric_limits<float>::digits10 + 1) << sdd.getValue(quantityName, i, j) << std::endl;
#endif
#if defined(PRECISION_DOUBLE)
            ofs << std::setprecision(std::numeric_limits<double>::digits10 + 1) << sdd.getValue(quantityName, i, j) << std::endl;
#endif
#if defined(PRECISION_LONG_DOUBLE)
            ofs << std::setprecision(std::numeric_limits<long double>::digits10 + 1) << sdd.getValue(quantityName, i, j) << std::endl;
#endif
        }
    }

    ofs.close();
    return 0;
}

int IO::writePerfResults(std::string directory, const std::map<std::string, int>& results) {

    std::ofstream ofs(directory + "/perfs.dat");

    for (auto const& r: results)
        ofs << r.first << " " << r.second << std::endl;

    ofs.close();
    return 0;
}

int IO::writeSDDPerfResults(std::string directory, const Domain& domain, const std::map<std::string, int>& results) {

    const SDDistributed& sdd = domain.getSDDconst();
    std::ostringstream oss;
    oss << sdd.getId();
    std::ofstream ofs(directory + "/sdd" + oss.str() + "/perfs.dat", std::ios::out);

    for (auto const& r: results)
        ofs << r.first << " " << r.second << std::endl;

    ofs.close();
    return 0;
}

int IO::writeSDDTime(std::string directory, const Domain& domain, const std::string& timerName, const std::deque<unsigned long int>& timeDeque) {

    const SDDistributed& sdd = domain.getSDDconst();
    std::ostringstream oss;
    oss << sdd.getId();
    std::ofstream ofs(directory + "/sdd" + oss.str() + "/timer-" + timerName + ".dat", std::ios::out);

    for (auto const& r: timeDeque)
        ofs << r << std::endl;

    ofs.close();
    return 0;
}

int IO::writeVariantInfo(std::string directory, const Domain& domain) {

    const SDDistributed& sdd = domain.getSDDconst();
    std::ostringstream oss;
    oss << sdd.getId();
    std::ofstream ofs(directory + "/sdd" + oss.str() + "/" + "variant_info.dat", std::ios::out);
    ofs << domain.getSizeX() << " " << domain.getSizeY() << std::endl;
    ofs << domain.getNumberSDD() << " " << domain.getNumberSDD_X() << " " << domain.getNumberSDD_Y() << std::endl;
    ofs << domain.getNumberNeighbourSDDs() << " " << domain.getNumberPhysicalCells() << " " << domain.getNumberOverlapCells() << " " << domain.getNumberBoundaryCells() << std::endl;
    ofs << domain.getNumberSDS() << " " << domain.getSDSGeometry() << " " << domain.getNumberThreads() << " " << domain.getNumberCommonSDS() << std::endl;
    ofs << "free_stack" << " " << "SoA" << std::endl;
    ofs.close();
    return 0;
}
