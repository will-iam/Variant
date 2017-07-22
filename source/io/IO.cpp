#include "IO.hpp"
#include "exception/exception.hpp"
#include <fstream>
#include <iomanip>

void stor(std::string tmpStr, float& target) {
    target = std::stof(tmpStr);
}

void stor(std::string tmpStr, double& target) {
    target = std::stod(tmpStr);
}

void stor(std::string tmpStr, long double& target) {
    target = std::stold(tmpStr);
}

int IO::loadSDDInfo(std::string directory,
        Domain& domain) {

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

int IO::loadDomainInfo(std::string directory,
                   Domain& domain) {

    // Read exec options
    std::ifstream ifs(directory + "/domain.dat", std::ios::in);
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

int IO::writeDomain(std::string directory,
        const Domain& domain) {

    std::ofstream ofs(directory + "/domain.dat");

    ofs << "2D ";
    ofs << "cartesian ";
    ofs << domain.getlx() << " ";
    ofs << domain.getly() << " ";
    ofs << domain.getSizeX() << " ";
    ofs << domain.getSizeY() << std::endl;

    // /!\ Also contains boundary cells
    std::vector<unsigned int> uidList = domain.getUidList();
    for (std::vector<unsigned int>::iterator it = uidList.begin();
            it != uidList.end(); ++it) {
        std::pair<int, int> coords = domain.getCoordsOnDomain(*it);
        if (domain.getBoundarySide(coords) != INSIDE)
            continue;
        ofs << *it << " ";
        ofs << domain.getCoordsOnDomain(*it).first << " ";
        ofs << domain.getCoordsOnDomain(*it).second << std::endl;
    }

    ofs.close();

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

int IO::loadExecOptions(std::string directory,
        Domain& domain) {

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
    std::getline(ifs, tmpStr);
    unsigned int nThreads = std::stoi(tmpStr);

    ifs.close();

    domain.setOptions(nSDD, nSDD_X, nSDD_Y, nSDS, SDSgeom, nThreads);

    return 0;
}

int IO::loadQuantity(std::string directory,
        std::string quantityName, Domain& domain, bool constant) {

    SDDistributed& sdd = domain.getSDD();

    domain.addQuantity(quantityName, constant);

    std::ostringstream oss;
    oss << sdd.getId();
    std::ifstream ifs(directory + "/sdd" + oss.str() + "/" + quantityName + ".dat",
                      std::ios::in);
    std::string tmpStr;

    //sdd.buildQuantity(quantityName); 
    for (int i = 0; i < sdd.getSizeX(); i++) {
        for (int j = 0; j < sdd.getSizeY(); j++) {
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

int IO::writeQuantity(std::string directory,
        std::string quantityName, const Domain& domain) {

    const SDDistributed& sdd = domain.getSDDconst();

    std::ostringstream oss;
    oss << sdd.getId();
    std::ofstream ofs(directory + "/sdd" + oss.str() + "/" + quantityName + ".dat",
            std::ios::out);
    if (!ofs)
        std::cerr << "Failed to open file: " << std::endl;

    for (int i = 0; i < sdd.getSizeX(); i++) {
        for (int j = 0; j < sdd.getSizeY(); j++) {
            ofs << i << " " << j << " " << sdd.getValue(quantityName, i, j) << std::endl;
        }
    }

    ofs.close();
    return 0;
}

int IO::loadBoundaryConditions(std::string directory,
        Domain& domain) {

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

        domain.addBoundaryCoords(uid,
                std::pair<int, int>(iCoord, jCoord),
                BCtype, value);
    }
    ifs.close();

    // Build domain boundary before leaving
    domain.buildBoundaryMap();
    return 0;
}

/*
int IO::writeBoundaryConditions(std::string directory,
        std::string quantityName,
        const Domain& domain) {

    std::ofstream ofs(directory + "/" + quantityName + "_bc.dat", std::ios::out);
    if (!ofs)
        std::cerr << "Failed to open file: " << std::endl;

    std::vector<unsigned int> boundaryUidList = domain.getBoundaryUidList();
    for (std::vector<unsigned int>::iterator it = boundaryUidList.begin(); it != boundaryUidList.end(); ++it) {
        std::pair<int, int> coords = domain.getCoordsOnDomain(*it);
        std::pair<char, real> bc = domain.getBoundaryCondition(*it);
        ofs << *it << " ";
        ofs << coords.first << " " << coords.second << " ";
        ofs << bc.first << " ";
        ofs << std::scientific << std::setprecision(16) << bc.second << std::endl;
        ofs.flush();
    }

    ofs.close();

    return 0;
}
*/

int IO::writePerfResults(std::string directory, const std::map<std::string, double> results) {

    std::ofstream ofs(directory + "/perfs.dat");

    for (auto const& r: results)
        ofs << r.first << " " << r.second << std::endl;
    
    ofs.close();
    return 0;
}
