#include "weakfloat.hpp"
#include <limits>
#include <iomanip>

#ifndef ROUNDING
#define ROUNDING FE_TONEAREST;
#endif

typedef weakfloat<PRECISION_WEAK_FLOAT, ROUNDING> wfloat;

bool unit_test() {
    float fa(31.999999);
    float fb(32.000003);
    float fc = 32.0 + 32.0 * pow(2, (8 - PRECISION_WEAK_FLOAT));
    float ulp32 = 32.0 * (1 + pow(2, (9 - PRECISION_WEAK_FLOAT)));
    float ulp16 = 16.0 * pow(2, (9 - PRECISION_WEAK_FLOAT));

    wfloat wfa(fa);
    wfloat wfb(fb);
    wfloat wfc(fc);

    if (PRECISION_WEAK_FLOAT == 32) {
        float f1 = static_cast <float> (200. * (rand() / (float)RAND_MAX) - 2.0);
        float f2 = static_cast <float> (200. * (rand() / (float)RAND_MAX) - 2.0);
        unsigned int u = rand();
        wfloat w1(f1), w2(f2);

        if (w1 != f1 || w2 != f2) {
            std::cout << "32: " << w1 << " != " << f1 << " || " << w2 << " != " << f2 << std::endl;
            return false;
        }

        if (w1 + w2 != f1 + f2) {
            std::cout << "32: " << w1 << " + " << w2 << " != " << f1 << " + " << f2 << std::endl;
            return false;
        }

        if (w1 - w2 != f1 - f2) {
            std::cout << "32: " << w1 << " - " << w2 << " != " << f1 << " - " << f2 << std::endl;
            return false;
        }

        if (w1 * w2 != f1 * f2) {
            std::cout << "32: " << w1 << " * " << w2 << " != " << f1 << " * " << f2 << std::endl;
            return false;
        }

        if (w1 / w2 != f1 / f2) {
            std::cout << "32: " << w1 << " / " << w2 << " != " << f1 << " / " << f2 << std::endl;
            return false;
        }

        if (w1 / u != f1 / u) {
            std::cout << "32: " << w1 << " / " << u << " != " << f1 << " / " << u << std::endl;
            return false;
        }

        if (rabs(w1 * w2) != fabsf(f1 * f2)) {
            std::cout << "32: |" << w1 << " * " << w2 << "| != |" << f1 << " * " << f2 << "|"<< std::endl;
            return false;
        }

        if (rsqrt(w1) != sqrtf(f1)) {
            std::cout << "32: sqrt(" << w1 << ")" << " != sqrt(" << f1 << ")" << std::endl;
            return false;
        }

        if (rcos(w2) != cosf(f2)) {
            std::cout << "32: " << w1 << " + " << w2 << " != " << f1 << " + " << f2 << std::endl;
            return false;
        }

        return true;
    }

    //FE_UPWARD, FE_DOWNWARD, FE_TONEAREST, FE_TOWARDZERO
    if (ROUNDING == FE_TONEAREST) {
        if (wfa != 32.f) {
            std::cout << "ut+: " << fa << " -> " << wfa << " != " << 32.f << std::endl;
            return false;
        }

        if (PRECISION_WEAK_FLOAT == 31 && wfb != ulp32) {
            return false;
        }

        if (PRECISION_WEAK_FLOAT != 31 && wfb != 32.f) {
            std::cout << "ut+b: " << fb << " -> " << wfb << " != " << 32.f << std::endl;
            return false;
        }

        if (wfc != ulp32) {
            std::cout << "ut+c: " << fc << " -> " << wfc << " != " << ulp32 << std::endl;
            return false;
        }

        wfa = -fa;
        wfb = -fb;
        wfc = -fc;

        if (wfa != -32.f) {
            std::cout << "ut-: " << fa << " -> " << wfa << " != " << -32.f << std::endl;
            return false;
        }

        if (PRECISION_WEAK_FLOAT == 31 && wfb != -ulp32) {
            return false;
        }

        if (PRECISION_WEAK_FLOAT != 31 && wfb != -32.f) {
            std::cout << "ut-: " << fb << " -> " << wfb << " != " << -32.f << std::endl;
            return false;
        }

        if (wfc != -ulp32) {
            std::cout << "ut-: " << fc << " -> " << wfc << " != " << -ulp32 << std::endl;
            return false;
        }
    }

    if (ROUNDING == FE_UPWARD) {
        if (wfa != 32.f) {
            std::cout << "ut+a: " << fa << " -> " << wfa << " != " << 32.f << std::endl;
            return false;
        }

        if (wfb != ulp32) {
            std::cout << "ut+b: " << fb << " -> " << wfb << " != " << ulp32 << std::endl;
            return false;
        }

        if (wfc != ulp32) {
            std::cout << "ut+c: " << fc << " -> " << wfc << " != " << ulp32 << std::endl;
            return false;
        }

        wfa = -fa;
        wfb = -fb;
        wfc = -fc;

        if (wfa != -32.f + ulp16) {
            std::cout << "ut-: " << fa << " -> " << wfa << " != " << -32.f + ulp16<< std::endl;
            return false;
        }

        if (wfb != -32.f) {
            std::cout << "ut-: " << fb << " -> " << wfb << " != " << -32.f << std::endl;
            return false;
        }

        if (wfc != -32.f) {
            std::cout << "ut-: " << fc << " -> " << wfc << " != " << 32.f << std::endl;
            return false;
        }
    }

    if (ROUNDING == FE_DOWNWARD) {
        if (wfa != 32.f - ulp16) {
            std::cout << "ut: " << fa << " -> " << wfa << " != " << 32.f - ulp16 << std::endl;
            return false;
        }

        if (wfb != 32.f)
            return false;

        if (wfc != 32.f)
            return false;

        wfa = -fa;
        wfb = -fb;
        wfc = -fc;

        if (wfa != -32.f) {
            std::cout << "ut-: " << fa << " -> " << wfa << " != " << -32.f << std::endl;
            return false;
        }

        if (wfb != -ulp32) {
            std::cout << "ut-: " << fb << " -> " << wfb << " != " << -ulp32 << std::endl;
            return false;
        }

        if (wfc != -ulp32) {
            std::cout << "ut-: " << fc << " -> " << wfc << " != " << -ulp32 << std::endl;
            return false;
        }
    }

    if (ROUNDING == FE_TOWARDZERO) {
        if (wfa != 32.f - ulp16) {
            std::cout << "ut: " << fa << " -> " << wfa << " != " << 32.f - ulp16 << std::endl;
            return false;
        }

        if (wfb != 32.f)
            return false;

        if (wfc != 32.f)
            return false;

        wfa = -fa;
        wfb = -fb;
        wfc = -fc;

        if (wfa != -32.f + ulp16) {
            std::cout << "ut: " << fa << " -> " << wfa << " != " << -32.f + ulp16 << std::endl;
            return false;
        }

        if (wfb != -32.f)
            return false;

        if (wfc != -32.f)
            return false;
    }

    return true;
}

bool test_weak_float() {

    std::cout << "     !~ ------------  Weak float " << PRECISION_WEAK_FLOAT << " test ------------ ~! " << std::endl;
    constexpr int max_digits10 = std::min(std::numeric_limits<float>::max_digits10, (int)std::ceil((PRECISION_WEAK_FLOAT - 9) * std::log10(2) + 2));
    srand (time(NULL));
    float m = std::numeric_limits<float>::max();
    wfloat w1(m);
    std::cout << std::setprecision(std::numeric_limits<float>::max_digits10);
    std::cout << "\tXX | " << std::defaultfloat << m << " | " << std::hexfloat << m << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::defaultfloat << w1 << " | " << std::hexfloat << w1 << std::endl;

    float f1 = static_cast <float> (100. * rand() / (float)RAND_MAX);
    float f2 = static_cast <float> (100. * rand() / (float)RAND_MAX);
    float f3 = static_cast <float> (-100. * rand() / (float)RAND_MAX);
    float f4 = static_cast <float> (-100. * rand() / (float)RAND_MAX);
    unsigned int u = rand();

    w1 = f1;
    wfloat w2(f2);
    wfloat wr3(f3);
    wfloat wr4(f4);

    std::cout << "\tXX | " << std::defaultfloat << f1 << " | " << std::hexfloat << f1 << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::defaultfloat << w1 << " | " << std::hexfloat << w1 << std::endl;

    std::cout << "\tXX | " << std::defaultfloat << f2 << " | " << std::hexfloat << f2 << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::defaultfloat << w2 << " | " << std::hexfloat << w2 << std::endl;

    std::cout << "\tXX | " << std::defaultfloat << f3 << " | " << std::hexfloat << f3 << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::defaultfloat << wr3 << " | " << std::hexfloat << wr3 << std::endl;

    std::cout << "\tXX | " << std::defaultfloat << f4 << " | " << std::hexfloat << f4 << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::defaultfloat << wr4 << " | " << std::hexfloat << wr4 << std::endl;



    std::cout << "\tXX | " << std::defaultfloat << f1 << " + " << f2 << " = " << (f1 + f2) << " | " << std::hexfloat << (f1 + f2) << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::defaultfloat << w1 << " + " << w2 << " = " << (w1 + w2) << " | " << std::hexfloat << (w1 + w2) << std::endl;

    auto w3 = w1 + w2;
    if (w3.truncated() == false)
        return false;

    std::cout << "\tXX | " << std::defaultfloat << f1 << " - " << f2 << " = " << (f1 - f2) << " | " << std::hexfloat << (f1 - f2) << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::defaultfloat << w1 << " - " << w2 << " = " << (w1 - w2) << " | " << std::hexfloat << (w1 - w2) << std::endl;

    w3 = w1 - w2;
    if (w3.truncated() == false)
        return false;

    std::cout << "\tXX | " << std::defaultfloat << f1 << " * " << f2 << " = " << (f1 * f2) << " | " << std::hexfloat << (f1 * f2) << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::defaultfloat << w1 << " * " << w2 << " = " << (w1 * w2) << " | " << std::hexfloat << (w1 * w2) << std::endl;

    w3 = w1 * w2;
    if (w3.truncated() == false)
        return false;

    std::cout << "\tXX | " << std::defaultfloat << f1 << " / " << f2 << " = " << (f1 / f2) << " | " << std::hexfloat << (f1 / f2) << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::defaultfloat << w1 << " / " << w2 << " = " << (w1 / w2) << " | " << std::hexfloat << (w1 / w2) << std::endl;

    w3 = w1 / w2;
    if (w3.truncated() == false)
        return false;

    std::cout << "\tXX | " << std::defaultfloat << f1 << " / " << u << " = " << (f1 / u) << " | " << std::hexfloat << (f1 / u) << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::defaultfloat << w1 << " / " << u << " = " << (w1 / u) << " | " << std::hexfloat << (w1 / u) << std::endl;

    w3 = w1 * w2;
    if (w3.truncated() == false)
        return false;

    std::cout << std::defaultfloat;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::setprecision(max_digits10) << w1 << "(" << max_digits10 << ") | " << std::setprecision(std::numeric_limits<float>::max_digits10) << w1 << "(" << std::numeric_limits<float>::max_digits10 << ")" << std::endl;
    std::cout << "\t" << PRECISION_WEAK_FLOAT << " | " << std::setprecision(max_digits10) << w2 << "(" << max_digits10 << ") | " << std::setprecision(std::numeric_limits<float>::max_digits10) << w2 << "(" << std::numeric_limits<float>::max_digits10 << ")" << std::endl;

    float fa(31.999999);
    float fb(32.000003);
    float fc = 32.0 + 32.0 * pow(2, (8 - PRECISION_WEAK_FLOAT));

    std::cout << "\tROUNDING<" << PRECISION_WEAK_FLOAT << ">: " << std::setprecision(std::numeric_limits<float>::max_digits10) << fa << " -> " << std::setprecision(max_digits10) << wfloat(fa);
    std::cout << ", h:" << std::hexfloat << fa <<" -> " << wfloat(fa) << std::endl;
    std::cout << std::defaultfloat;
    std::cout << "\tROUNDING<" << PRECISION_WEAK_FLOAT << ">: " << std::setprecision(std::numeric_limits<float>::max_digits10) << 44.f << " -> " << std::setprecision(max_digits10) << wfloat(44.f);
    std::cout << ", h:" << std::hexfloat << 44.f <<" -> " << wfloat(44.f) << std::endl;
    std::cout << std::defaultfloat;
    std::cout << "\tROUNDING<" << PRECISION_WEAK_FLOAT << ">: " << std::setprecision(std::numeric_limits<float>::max_digits10) << fb << " -> " << std::setprecision(max_digits10) << wfloat(fb);
    std::cout << ", h:" << std::hexfloat << fb <<" -> " << wfloat(fb) << std::endl;
    std::cout << std::defaultfloat;
    std::cout << "\tROUNDING<" << PRECISION_WEAK_FLOAT << ">: " << std::setprecision(std::numeric_limits<float>::max_digits10) << fc << " -> " << std::setprecision(max_digits10) << wfloat(fc);
    std::cout << ", h:" << std::hexfloat << fc <<" -> " << wfloat(fc) << std::endl;
    std::cout << std::defaultfloat;
    std::cout << "\tROUNDING<" << PRECISION_WEAK_FLOAT << ">: " << std::setprecision(std::numeric_limits<float>::max_digits10) << -fa << " -> " << std::setprecision(max_digits10) << wfloat(-fa);
    std::cout << ", h:" << std::hexfloat << -fa <<" -> " << wfloat(-fa) << std::endl;
    std::cout << std::defaultfloat;
    std::cout << "\tROUNDING<" << PRECISION_WEAK_FLOAT << ">: " << std::setprecision(std::numeric_limits<float>::max_digits10) << -fb << " -> " << std::setprecision(max_digits10) << wfloat(-fb);
    std::cout << ", h:" << std::hexfloat << -fb <<" -> " << wfloat(-fb) << std::endl;
    std::cout << std::defaultfloat;
    std::cout << "\tROUNDING<" << PRECISION_WEAK_FLOAT << ">: " << std::setprecision(std::numeric_limits<float>::max_digits10) << -fc << " -> " << std::setprecision(max_digits10) << wfloat(-fc);
    std::cout << ", h:" << std::hexfloat << -fc <<" -> " << wfloat(-fc) << std::endl;
    std::cout << std::defaultfloat;

    fa = 1.999999e29;
    fb = 2.000003e29;
    fc = (2. + pow(2, (8 - PRECISION_WEAK_FLOAT))) * powf(2.0, 29);

    std::cout << "\tROUNDING<" << PRECISION_WEAK_FLOAT << ">: " << std::setprecision(std::numeric_limits<float>::max_digits10) << fa << " -> " << std::setprecision(max_digits10) << wfloat(fa) << std::endl;
    std::cout << "\tROUNDING<" << PRECISION_WEAK_FLOAT << ">: " << std::setprecision(std::numeric_limits<float>::max_digits10) << fb << " -> " << std::setprecision(max_digits10) << wfloat(fb) << std::endl;
    std::cout << "\tROUNDING<" << PRECISION_WEAK_FLOAT << ">: " << std::setprecision(std::numeric_limits<float>::max_digits10) << fc << " -> " << std::setprecision(max_digits10) << wfloat(fc) << std::endl;

    std::cout << "\tROUNDING<" << PRECISION_WEAK_FLOAT << ">: " << std::setprecision(std::numeric_limits<float>::max_digits10) << -fa << " -> " << std::setprecision(max_digits10) << wfloat(-fa) << std::endl;
    std::cout << "\tROUNDING<" << PRECISION_WEAK_FLOAT << ">: " << std::setprecision(std::numeric_limits<float>::max_digits10) << -fb << " -> " << std::setprecision(max_digits10) << wfloat(-fb) << std::endl;
    std::cout << "\tROUNDING<" << PRECISION_WEAK_FLOAT << ">: " << std::setprecision(std::numeric_limits<float>::max_digits10) << -fc << " -> " << std::setprecision(max_digits10) << wfloat(-fc) << std::endl;

    fa = 1.999999e-29;
    fb = 2.000003e-29;
    fc = (2. + pow(2, (8 - PRECISION_WEAK_FLOAT))) * powf(2.0, -29);

    std::cout << "\tROUNDING<" << PRECISION_WEAK_FLOAT << ">: " << std::setprecision(std::numeric_limits<float>::max_digits10) << fa << " -> " << std::setprecision(max_digits10) << wfloat(fa) << std::endl;
    std::cout << "\tROUNDING<" << PRECISION_WEAK_FLOAT << ">: " << std::setprecision(std::numeric_limits<float>::max_digits10) << fb << " -> " << std::setprecision(max_digits10) << wfloat(fb) << std::endl;
    std::cout << "\tROUNDING<" << PRECISION_WEAK_FLOAT << ">: " << std::setprecision(std::numeric_limits<float>::max_digits10) << fc << " -> " << std::setprecision(max_digits10) << wfloat(fc) << std::endl;

    std::cout << "\tROUNDING<" << PRECISION_WEAK_FLOAT << ">: " << std::setprecision(std::numeric_limits<float>::max_digits10) << -fa << " -> " << std::setprecision(max_digits10) << wfloat(-fa) << std::endl;
    std::cout << "\tROUNDING<" << PRECISION_WEAK_FLOAT << ">: " << std::setprecision(std::numeric_limits<float>::max_digits10) << -fb << " -> " << std::setprecision(max_digits10) << wfloat(-fb) << std::endl;
    std::cout << "\tROUNDING<" << PRECISION_WEAK_FLOAT << ">: " << std::setprecision(std::numeric_limits<float>::max_digits10) << -fc << " -> " << std::setprecision(max_digits10) << wfloat(-fc) << std::endl;

    std::cout << std::endl;

    /*
    std::cout << "float::digits = " << std::numeric_limits<float>::digits << std::endl;
    std::cout << "float::digits10 = " << std::numeric_limits<float>::digits10 << std::endl;
    std::cout << "float::max_digits10 = " << std::numeric_limits<float>::max_digits10 << std::endl;
    std::cout << "(PRECISION_WEAK_FLOAT - 8) * std::log10(2) + 1 = " << (PRECISION_WEAK_FLOAT - 8) << " * " << std::log10(2) << " + 1 = ";
    std::cout << (PRECISION_WEAK_FLOAT - 8) * std::log10(2) + 1 << std::endl;
    std::cout << "Number::max_digits10 = " << max_digits10 << std::endl;
    */

    /*
    for (int i = 10; i < 33; ++i) {
        int p = std::min(std::numeric_limits<float>::max_digits10, (int)std::ceil((i - 9) * std::log10(2) + 2));
        std::cout << i << " -> " << p << std::endl;
    } */

    return unit_test();

    std::cout << "     !~ ------------  Weak float " << PRECISION_WEAK_FLOAT << " end  ------------ ~! " << std::endl;
    return true;
}
