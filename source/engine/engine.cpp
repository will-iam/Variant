#include <iostream>
#include <iomanip>
#include <sstream>
#include <getopt.h>
#include <cstdlib>
#include <cstring>
#include <algorithm>
#include "timestamp/timestamp.hpp"
#include "exception/exception.hpp"
#include "IO.hpp"
#include "engine.hpp"
#ifndef SEQUENTIAL
#include <mpi.h>
#endif
//#include <scorep/SCOREP_User.h>

using namespace std;

int Engine::main(int argc, char** argv) {

    // Init the rand system
    srand(1337);

    #ifdef SEQUENTIAL
    _MPI_rank = 0;
    #else
    // Init MPI
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &_MPI_rank);
        #ifndef NDEBUG
        int mpi_comm_size(0);
        MPI_Comm_size(MPI_COMM_WORLD, &mpi_comm_size);
        std::cerr << "Hello world from process " << _MPI_rank << " of " << mpi_comm_size << std::endl;
        #endif
    #endif

    int flag;
    const int stringsize = 180;
    char initfile[ stringsize ];
    char outputpath[ stringsize ];
    bool outputpathSet = false;
    _testFlag = 0;
    _dryFlag = 0;
    struct option long_options[] = {
        {"test", 0, &_testFlag, true},
        {"dry", 0, &_dryFlag, true},
        {NULL, 0, NULL, 0}
    };

    std::map<std::string, int> perfResults;

    int option_index = 0;
    while ((flag = getopt_long(argc, argv, "i:o:h", long_options, &option_index)) != EOF) {
        switch(flag){

            case 0:
                //printf ("option %s", long_options[option_index].name);
                //if (optarg)
                //    printf (" with arg %s", optarg);
                //printf ("\n");
                break;

            case 'i':
                strncpy(initfile, optarg, stringsize);
                break;

            case 'o':
                strncpy(outputpath, optarg, stringsize);
                outputpathSet = true;
                break;

            case 'h': default:
                cout << "-i to define input file path" << endl;
                cout << "-o to define output path" << endl;
                cout << "-h this menu" << endl;
                cout << "Example:\n\t./scheme-debug-intel -i input.var -o /tmp\n";
                return EXIT_SUCCESS;
        }
    }

    if (_MPI_rank == 0) {

#ifndef NDEBUG
        cout << Console::_yellow << "Rules for developer:" << endl;
        cout << "\t- no Warnings." << endl;
        cout << "\t- no cast of any sort (dynamic, static, const, reinterpret, ...)." << endl;
        cout << "\t- comment every class, function, method, member, variable with doxygen style." << endl;
        cout << "\t- commit regularly." << endl;
        cout << "\t- think simple." << endl;
        cout << "\t- think modular: encapsulate as much as possible and put every member private." << endl;
        cout << "\t- and most important ......... think category theory." << Console::_normal << endl;
#endif

        #if defined (PRECISION_FLOAT)
        std::cout << Console::_green << "Precision set to " << Console::_bold << "float." << Console::_normal << std::endl;
        #endif
        #if defined (PRECISION_DOUBLE)
        std::cout << Console::_green << "Precision set to " << Console::_bold << "double." << Console::_normal << std::endl;
        #endif
        #if defined (PRECISION_LONG_DOUBLE)
        std::cout << Console::_green << "Precision set to " << Console::_bold << "long double." << Console::_normal << std::endl;
        #endif

        std::cout << Console::_blue;
        std::cout << "Show cosinus value to test libm exclusion: << -3.9998531498835127e-01 = " << std::scientific;
        std::cout << std::setprecision(std::numeric_limits<double>::max_digits10);
        std::cout << Console::_bold << cos(42.) << std::endl;
        std::cout << std::setprecision(2) << std::fixed << Console::_normal;
        //std::cout << std::setprecision(6) << std::defaultfloat << Console::_normal;
        /*
        if (-3.9998531498835127e-01 != cos(42.)) {
            std::cout << Console::_normal << "Cosinus computation is wrong.";
            return EXIT_FAILURE;
        } */

        if (!outputpathSet){
            cout << "Output path argument missing. Exit." << endl;
            return EXIT_FAILURE;
        }

        if (initfile[0] == '\0'){
            cout << "Init file name missing. Exit." << endl;
            return EXIT_FAILURE;
        }

        #ifndef NDEBUG
        if (_testFlag != 0)
            cout << "Test flag is on." << endl;

        if (_dryFlag != 0)
            cout << "Dry flag is on." << endl;
        #endif
    }

    _initpath = initfile;
    _outputpath = outputpath;

    if (_MPI_rank == 0) {

        cout << Console::_green;
        TimeStamp::printLocalTime();
        cout << ": Initialize Engine" << Console::_normal << endl;

        _timer.begin();
    }

    // Check return of initialize, if ok nothing to do
    int result = init();

    if (result < 0) {
        cout << Console::_red << "Engine init() failed with return: ";
        cout << result << Console::_normal << endl;
        return EXIT_FAILURE;
    }
    #ifndef SEQUENTIAL
    MPI_Barrier(MPI_COMM_WORLD);
    #endif
    if (_MPI_rank == 0) {

        _timer.end();

        _timer.reportLast();

        perfResults["initTime"] = _timer.getLastSteadyDuration();

        cout << Console::_green;
        TimeStamp::printLocalTime();
        cout << ": Engine starts" << Console::_normal << endl;

        _timer.begin();
    }

    // Check return of start, if ok nothing to do
    //SCOREP_USER_REGION_DEFINE( my_region_handle )
    //SCOREP_USER_OA_PHASE_BEGIN( my_region_handle, "mainRegion", SCOREP_USER_REGION_TYPE_COMMON )
    result = start();
    //SCOREP_USER_OA_PHASE_END( my_region_handle )

    if(result < 0) {
        cout << Console::_red << "Engine start() failed with return: ";
        cout << result << Console::_normal << endl;
        return EXIT_FAILURE;
    }

    #ifndef SEQUENTIAL
    MPI_Barrier(MPI_COMM_WORLD);
    #endif
    if (_MPI_rank == 0) {
        _timer.end();
        cout << Console::_green;
        TimeStamp::printLocalTime();
        cout << ": Engine stopped normally." << endl;
        _timer.reportLast();

        perfResults["loopTime"] = _timer.getLastSteadyDuration();
        perfResults["nIterations"] = _nIterations;

	    cout << Console::_green;
	    TimeStamp::printLocalTime();
	    cout << ": Engine finalizes" << Console::_normal << endl;
	    _timer.begin();
    }

    finalize();

    #ifndef SEQUENTIAL
    MPI_Barrier(MPI_COMM_WORLD);
    #endif
    if (_MPI_rank == 0) {
	    _timer.end();
	    _timer.reportLast();
	    perfResults["finalizeTime"] = _timer.getLastSteadyDuration();
	    IO::writePerfResults(_outputpath, perfResults);
    }

    #ifndef SEQUENTIAL
    MPI_Finalize();
    #endif

    return EXIT_SUCCESS;
}

void Engine::setOptions(real T, real CFL) {

    _T = T;
    _CFL = CFL;
}

void Engine::updateDomainUmax() {

    #ifndef SEQUENTIAL
    _SDD_uxmax = *std::max_element(_SDS_uxmax.begin(), _SDS_uxmax.end());
    _SDD_uymax = *std::max_element(_SDS_uymax.begin(), _SDS_uymax.end());
    real _SDD_umax[] = {_SDD_uxmax, _SDD_uymax};
    real _Domain_umax[] = {0., 0.};
    MPI_Allreduce(&_SDD_umax, &_Domain_umax, 2, MPI_REALTYPE, MPI_MAX, MPI_COMM_WORLD);
    _Domain_uxmax = _Domain_umax[0];
    _Domain_uymax = _Domain_umax[1];
    #else
    _Domain_uxmax = *std::max_element(_SDS_uxmax.begin(), _SDS_uxmax.end());
    _Domain_uymax = *std::max_element(_SDS_uymax.begin(), _SDS_uymax.end());
    #endif
}

void Engine::updateDomainUxmax() {

    #ifndef SEQUENTIAL
    _SDD_uxmax = *std::max_element(_SDS_uxmax.begin(), _SDS_uxmax.end());
    MPI_Allreduce(&_SDD_uxmax, &_Domain_uxmax, 1, MPI_REALTYPE, MPI_MAX, MPI_COMM_WORLD);
    #else
    _Domain_uxmax = *std::max_element(_SDS_uxmax.begin(), _SDS_uxmax.end());
    #endif
}

void Engine::updateDomainUymax() {

    #ifndef SEQUENTIAL
    _SDD_uymax = *std::max_element(_SDS_uymax.begin(), _SDS_uymax.end());
    MPI_Allreduce(&_SDD_uymax, &_Domain_uymax, 1, MPI_REALTYPE, MPI_MAX, MPI_COMM_WORLD);
    #else
    _Domain_uymax = *std::max_element(_SDS_uymax.begin(), _SDS_uymax.end());
    #endif
}

real Engine::reduceMin(const real& v) {
    #ifndef SEQUENTIAL
    real min_value(0.);
    MPI_Allreduce(&v, &min_value, 1, MPI_REALTYPE, MPI_MIN, MPI_COMM_WORLD);
    return min_value;
    #else
    return v;
    #endif
}
