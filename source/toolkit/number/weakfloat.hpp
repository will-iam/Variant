#ifndef WEAKFLOAT_HPP
#define WEAKFLOAT_HPP
#include <iostream>
#include <cmath>
#include <functional>
#include <cfenv>

//! The number of significant bits in the mantissa is PRECISION_WEAK_FLOAT - 9

#ifndef PRECISION_WEAK_FLOAT
    // Compile with a weak_float as precise as a standard float
    #define PRECISION_WEAK_FLOAT 32
#else
    static_assert(PRECISION_WEAK_FLOAT < 33);
    static_assert(PRECISION_WEAK_FLOAT > 8);
#endif

const unsigned int _ulp_table[] = {
    0x00000000,
    0x00000000, 0x00000000, 0x00000000, 0x00000000,
    0x00000000, 0x00000000, 0x00000000, 0x00000000,
    0x00400000, 0x00200000, 0x00100000, 0x00080000,
    0x00040000, 0x00020000, 0x00010000, 0x00008000,
    0x00004000, 0x00002000, 0x00001000, 0x00000800,
    0x00000400, 0x00000200, 0x00000100, 0x00000080,
    0x00000040, 0x00000020, 0x00000010, 0x00000008,
    0x00000004, 0x00000002, 0x00000001, 0x00000000 };

const unsigned int _trunc_table[] = {
    0xff800000,
    0xff800000, 0xff800000, 0xff800000, 0xff800000,
    0xff800000, 0xff800000, 0xff800000, 0xff800000,
    0xff800000, 0xffc00000, 0xffe00000, 0xfff00000,
    0xfff80000, 0xfffc0000, 0xfffe0000, 0xffff0000,
    0xffff8000, 0xffffc000, 0xffffe000, 0xfffff000,
    0xfffff800, 0xfffffc00, 0xfffffe00, 0xffffff00,
    0xffffff80, 0xffffffc0, 0xffffffe0, 0xfffffff0,
    0xfffffff8, 0xfffffffc, 0xfffffffe, 0xffffffff };


#pragma GCC push_options
#pragma GCC optimize("O0")

template<int N, int R>
struct Trunc {
    Trunc() = default;
    Trunc(const Trunc&) = default;
    void operator()(float &) const;
};

template<int N, int R>
void Trunc<N, R>::operator()(float& f) const{
    std::cout << "Warning...";
    /*
    // nothing to do here.
    if (f == 0.f)
        return;

    unsigned int *c = reinterpret_cast<unsigned int*>(&f);

    // Truncate the same way whatever the sign is.
    // case FE_TOWARDZERO: break;
    if (R == FE_DOWNWARD) {
        if (f > 0.f) {
            *c &= _trunc_table[N];
            return;
        }

        const unsigned int r = *c & (~_trunc_table[N]);
        if (r == 0)
            return;

        float tmpf1(f);
        unsigned int *tmpc1 = reinterpret_cast<unsigned int*>(&tmpf1);
        *tmpc1 &= _trunc_table[0]; // to get the order only
        float tmpf2(tmpf1);
        unsigned int *tmpc2 = reinterpret_cast<unsigned int*>(&tmpf2);
        *tmpc2 |= _ulp_table[N-1]; // gets the order and the ulp to add.
        f += tmpf2;
        f -= tmpf1;

        *c &= _trunc_table[N];
        return;
    }

    if (R == FE_UPWARD) {
        if (f < 0.f) {
            *c &= _trunc_table[N];
            return;
        }

        const unsigned int r = *c & (~_trunc_table[N]);
        if (r == 0)
            return;

        float tmpf1(f);
        unsigned int *tmpc1 = reinterpret_cast<unsigned int*>(&tmpf1);
        *tmpc1 &= _trunc_table[0]; // to get the order only
        float tmpf2(tmpf1);
        unsigned int *tmpc2 = reinterpret_cast<unsigned int*>(&tmpf2);
        *tmpc2 |= _ulp_table[N-1]; // gets the order and the ulp to add.
        f += tmpf2;
        f -= tmpf1;
        *c &= _trunc_table[N];
        return;
    }

    if (R == FE_TONEAREST) {
       const unsigned int r = *c & (~_trunc_table[N]);
        if (r == 0)
            return;

        if (r >= _ulp_table[N]) {
            float tmpf1(f);
            unsigned int *tmpc1 = reinterpret_cast<unsigned int*>(&tmpf1);
            *tmpc1 &= _trunc_table[0]; // to get the order only
            float tmpf2(tmpf1);
            unsigned int *tmpc2 = reinterpret_cast<unsigned int*>(&tmpf2);
            *tmpc2 |= _ulp_table[N]; // gets the order and the ulp to add.
            f += tmpf2;
            f -= tmpf1;
        }

        *c &= _trunc_table[N];
        return;
    }

    // This must be done for all.
    *c &= _trunc_table[N];
    */
}

template<int N>
struct Trunc<N, FE_UPWARD> {
    void operator()(float &f) const {
        unsigned int *c = reinterpret_cast<unsigned int*>(&f);
        if (f <= 0.f) {
            *c &= _trunc_table[N];
            return;
        }

        const unsigned int r = *c & (~_trunc_table[N]);
        if (r == 0)
            return;

        float tmpf1(f);
        unsigned int *tmpc1 = reinterpret_cast<unsigned int*>(&tmpf1);
        *tmpc1 &= 0xff800000; // to get the order only
        float tmpf2(tmpf1);
        unsigned int *tmpc2 = reinterpret_cast<unsigned int*>(&tmpf2);
        *tmpc2 |= _ulp_table[N-1]; // gets the order and the ulp to add.
        f -= tmpf1;
        f += tmpf2;
        *c &= _trunc_table[N];
    }
};

template<int N>
struct Trunc<N, FE_DOWNWARD> {
    void operator()(float &f) const {
        unsigned int *c = reinterpret_cast<unsigned int*>(&f);
        if (f >= 0.f) {
            *c &= _trunc_table[N];
            return;
        }

        const unsigned int r = *c & (~_trunc_table[N]);
        if (r == 0)
            return;

        float tmpf1(f);
        unsigned int *tmpc1 = reinterpret_cast<unsigned int*>(&tmpf1);
        *tmpc1 &= 0xff800000; // to get the order only
        float tmpf2(tmpf1);
        unsigned int *tmpc2 = reinterpret_cast<unsigned int*>(&tmpf2);
        *tmpc2 |= _ulp_table[N-1]; // gets the order and the ulp to add.
        f -= tmpf1;
        f += tmpf2;
        *c &= _trunc_table[N];
    }
};

template<int N>
struct Trunc<N, FE_TOWARDZERO> {
    void operator()(float &f) const {
        unsigned int *c = reinterpret_cast<unsigned int*>(&f);
        *c &= _trunc_table[N];
    }
};

template<int N>
struct Trunc<N, FE_TONEAREST> {
    void operator()(float &f) const {

        // nothing to do here.
        //if (f == 0.f)
        //    return;

        unsigned int *c = reinterpret_cast<unsigned int*>(&f);
        const unsigned int r = *c & (~_trunc_table[N]);

        if (r < _ulp_table[N]) {
            *c &= _trunc_table[N];
            return;
        }

        float tmpf1(f);
        unsigned int *tmpc1 = reinterpret_cast<unsigned int*>(&tmpf1);
        *tmpc1 &= 0xff800000; // to get the order only
        float tmpf2(tmpf1);
        unsigned int *tmpc2 = reinterpret_cast<unsigned int*>(&tmpf2);
        *tmpc2 |= _ulp_table[N]; // gets the order and the ulp to add.
        f -= tmpf1;
        f += tmpf2;
        *c &= _trunc_table[N];
    }
};

/*
template<>
struct Trunc<32, FE_UPWARD> {
    void operator()(float &) const {}
};

template<>
struct Trunc<32, FE_DOWNWARD> {
    void operator()(float &) const {}
};

template<>
struct Trunc<32, FE_TOWARDZERO> {
    void operator()(float &) const {}
};

template<>
struct Trunc<32, FE_TONEAREST> {
    void operator()(float &) const {}
};
*/
#pragma GCC pop_options


template<int N, int R>
class weakfloat {
  public:
    weakfloat() : _f(0.f){}
    weakfloat(const float& f) : _f(f) { _trunc(_f); }
    weakfloat(const int& i) : _f(i) { _trunc(_f); }
    weakfloat(const unsigned int& u) : _f(u) { _trunc(_f); }
    //weakfloat(const float&& f) : _f(f){}
    weakfloat<N, R>& operator=(const float& f) {
      _f = f;
      _trunc(_f);
      return *this;
    }

    bool truncated() {
        float f(_f);

        if (f == std::numeric_limits<float>::infinity())
            return true;

        if (-f == std::numeric_limits<float>::infinity())
            return true;

        unsigned int *c = reinterpret_cast<unsigned int*>(&f);
        *c &= ~_trunc_table[N];
        return (*c == 0);
    }

    friend bool operator< (const weakfloat<N, R>& lhs, const weakfloat<N, R>& rhs){
        return lhs._f < rhs._f;
    }

    friend bool operator> (const weakfloat<N, R>& lhs, const weakfloat<N, R>& rhs){
        return lhs._f > rhs._f;
    }

    friend bool operator== (const weakfloat<N, R>& lhs, const weakfloat<N, R>& rhs){
        return lhs._f == rhs._f;
    }

    friend weakfloat<N, R> operator+ (const weakfloat<N, R>& lhs, const weakfloat<N, R>& rhs){
        return weakfloat<N, R>(lhs._f + rhs._f);
    }

    friend weakfloat<N, R> operator- (const weakfloat<N, R>& lhs, const weakfloat<N, R>& rhs){
        return weakfloat<N, R>(lhs._f - rhs._f);
    }

    friend weakfloat<N, R> operator* (const weakfloat<N, R>& lhs, const weakfloat<N, R>& rhs){
        return weakfloat<N, R>(lhs._f * rhs._f);
    }

    friend weakfloat<N, R> operator/ (const weakfloat<N, R>& lhs, const weakfloat<N, R>& rhs){
        return weakfloat<N, R>(lhs._f / rhs._f);
    }

    friend weakfloat<N, R> operator/ (const weakfloat<N, R>& lhs, const unsigned int& rhs){
        return lhs / weakfloat<N, R>(rhs);
    }

    friend weakfloat<N, R> rabs(weakfloat<N, R> w) {
        return weakfloat<N, R>(fabsf(w._f));
    }

    friend weakfloat<N, R> rsqrt(weakfloat<N, R> w) {
        return weakfloat<N, R>(sqrtf(w._f));
    }

    friend weakfloat<N, R> rcos(weakfloat<N, R> w) {
        return weakfloat<N, R>(cosf(w._f));
    }

    operator float () const {
        return _f;
    }

    friend std::ostream& operator<< (std::ostream& out, const weakfloat<N, R>& x) {
        out << x._f;
        return out;
    }

  private:
    Trunc<N, R> _trunc;
    float _f;
};



bool test_weak_float();

#endif
