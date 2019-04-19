#ifndef WEAKFLOAT_HPP
#define WEAKFLOAT_HPP
#include <iostream>
#include <cmath>

#ifndef PRECISION_WEAK_FLOAT
    // Compile with a weak_float as precise as a standard float
    #define PRECISION_WEAK_FLOAT 32
#else
    static_assert(PRECISION_WEAK_FLOAT < 32);
    static_assert(PRECISION_WEAK_FLOAT > 7);
#endif

const unsigned int _trunc[] = {
    0xff000000,
    0xff000000, 0xff000000, 0xff000000, 0xff000000,
    0xff000000, 0xff000000, 0xff000000, 0xff000000,
    0xff800000, 0xffc00000, 0xffe00000, 0xfff00000,
    0xfff80000, 0xfffc0000, 0xfffe0000, 0xffff0000,
    0xffff8000, 0xffffc000, 0xffffe000, 0xfffff000,
    0xfffff800, 0xfffffc00, 0xfffffe00, 0xffffff00,
    0xffffff80, 0xffffffc0, 0xffffffe0, 0xfffffff0,
    0xfffffff8, 0xfffffffc, 0xfffffffe, 0xffffffff };

template<int N>
class weakfloat {
  public:
    weakfloat() : _f(0.f){}
    weakfloat(const float& f) : _f(f) { trunc(_f); }
    weakfloat(const int& i) : _f(i) { trunc(_f); }
    weakfloat(const unsigned int& u) : _f(u) { trunc(_f); }
    //weakfloat(const float&& f) : _f(f){}

    void trunc(float& f) {
        unsigned int *c = reinterpret_cast<unsigned int*>(&f);
        *c &= _trunc[N];
    }

    bool truncated() {
        float f(_f);
        unsigned int *c = reinterpret_cast<unsigned int*>(&f);
        *c &= ~_trunc[N];
        return (*c == 0);
    }

    friend bool operator< (const weakfloat<N>& lhs, const weakfloat<N>& rhs){
        return lhs._f < rhs._f;
    }

    friend bool operator> (const weakfloat<N>& lhs, const weakfloat<N>& rhs){
        return lhs._f > rhs._f;
    }

    friend bool operator== (const weakfloat<N>& lhs, const weakfloat<N>& rhs){
        return lhs._f == rhs._f;
    }

    friend weakfloat<N> operator+ (const weakfloat<N>& lhs, const weakfloat<N>& rhs){
        return weakfloat<N>(lhs._f + rhs._f);
    }

    friend weakfloat<N> operator- (const weakfloat<N>& lhs, const weakfloat<N>& rhs){
        return weakfloat<N>(lhs._f - rhs._f);
    }

    friend weakfloat<N> operator* (const weakfloat<N>& lhs, const weakfloat<N>& rhs){
        return weakfloat<N>(lhs._f * rhs._f);
    }

    friend weakfloat<N> operator/ (const weakfloat<N>& lhs, const weakfloat<N>& rhs){
        return weakfloat<N>(lhs._f / rhs._f);
    }

    friend weakfloat<N> operator/ (const weakfloat<N>& lhs, const unsigned int& rhs){
        return lhs / weakfloat<N>(rhs);
    }

    friend weakfloat<N> rabs(weakfloat<N> w) {
        return weakfloat<N>(fabsf(w._f));
    }

    friend weakfloat<N> rsqrt(weakfloat<N> w) {
        return weakfloat<N>(sqrtf(w._f));
    }

    friend weakfloat<N> rcos(weakfloat<N> w) {
        return weakfloat<N>(cosf(w._f));
    }

    weakfloat<N>& operator=(const float& f) {
      _f = f;
      return *this;
    }

    operator float () const {
        return _f;
    }

    friend std::ostream& operator<< (std::ostream& out, const weakfloat<N>& x) {
        out << x._f;
        return out;
    }

  private:
    float _f;
};

void test_weak_float();

#endif
