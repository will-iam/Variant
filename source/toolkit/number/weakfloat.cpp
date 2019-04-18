#include "weakfloat.hpp"
#include <limits>
#include <iomanip>

void test_weak_float() {
    std::cout << "TEST WEAK FLOAT: " << PRECISION_WEAK_FLOAT << std::endl;

    srand (time(NULL));
    float f = static_cast <float> (rand());
    //unsigned char *c = reinterpret_cast<unsigned char *>(&f);
    float m = std::numeric_limits<float>::max();
    weakfloat<32> w32(m);

    weakfloat<31> w31(m);
    weakfloat<30> w30(m);
    weakfloat<29> w29(m);
    weakfloat<28> w28(m);

    weakfloat<27> w27(m);
    weakfloat<26> w26(m);
    weakfloat<25> w25(m);
    weakfloat<24> w24(m);
    weakfloat<23> w23(m);
    weakfloat<20> w20(m);
    weakfloat<16> w16(m);

    weakfloat<8> w8(m);

    std::cout << std::setprecision(std::numeric_limits<float>::max_digits10);
    std::cout << "XX: " << std::hexfloat << m << " = " << std::defaultfloat << m << std::endl;
    std::cout << "32: " << std::hexfloat << w32 << " = " << std::defaultfloat << w32 << std::endl;
    std::cout << "31: " << std::hexfloat << w31 << " = " << std::defaultfloat << w31 << std::endl;
    std::cout << "30: " << std::hexfloat << w30 << " = " << std::defaultfloat << w30 << std::endl;
    std::cout << "29: " << std::hexfloat << w29 << " = " << std::defaultfloat << w29 << std::endl;
    std::cout << "28: " << std::hexfloat << w28 << " = " << std::defaultfloat << w28 << std::endl;
    std::cout << "27: " << std::hexfloat << w27 << " = " << std::defaultfloat << w27 << std::endl;
    std::cout << "26: " << std::hexfloat << w26 << " = " << std::defaultfloat << w26 << std::endl;
    std::cout << "25: " << std::hexfloat << w25 << " = " << std::defaultfloat << w25 << std::endl;
    std::cout << "24: " << std::hexfloat << w24 << " = " << std::defaultfloat << w24 << std::endl;

    std::cout << "23: " << std::hexfloat << w23 << " = " << std::defaultfloat << w23 << std::endl;

    std::cout << "20: " << std::hexfloat << w20 << " = " << std::defaultfloat << w20 << std::endl;

    std::cout << "16: " << std::hexfloat << w16 << " = " << std::defaultfloat << w16 << std::endl;

    std::cout << "8: " << std::hexfloat << w8 << " = " << std::defaultfloat << w8 << std::endl;
    std::cout << "8 + 8: " << std::hexfloat << w8 + w8 << " = " << std::defaultfloat << w8 + w8 << std::endl;

    weakfloat<PRECISION_WEAK_FLOAT> w(f);
    std::cout << std::endl << std::endl << "XX: " << std::hexfloat << f << " = " << std::defaultfloat << f << std::endl;
    std::cout << PRECISION_WEAK_FLOAT << ": " << std::hexfloat << w << " = " << std::defaultfloat << w << std::endl;
    auto w2 = w + w;
    if (w2.truncated() == false)
        std::cout << "EXIT." << std::endl;
    std::cout << PRECISION_WEAK_FLOAT << " + : " << std::hexfloat << w2 << " = " << std::defaultfloat << w2 << std::endl;

    std::cout << std::endl;
}
