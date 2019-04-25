#include "bHydro.hpp"

int main(int argc, char **argv)
{
    BHydro scheme;
    int r = scheme.main(argc, argv);
    return r;
}
