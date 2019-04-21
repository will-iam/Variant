#ifndef WEAKFLOAT_HPP
#define WEAKFLOAT_HPP
#include <iostream>
#include <cmath>
#include <functional>
#include <cfenv>

#ifndef PRECISION_WEAK_FLOAT
    // Compile with a weak_float as precise as a standard float
    #define PRECISION_WEAK_FLOAT 32
#else
    static_assert(PRECISION_WEAK_FLOAT < 33);
    static_assert(PRECISION_WEAK_FLOAT > 7);
#endif

const unsigned int _ulp_table[] = {
    0x00000000,
    0x00000000, 0x00000000, 0x00000000, 0x00000000,
    0x00000000, 0x00000000, 0x00000000, 0x00800000,
    0x00400000, 0x00200000, 0x00100000, 0x00080000,
    0x00040000, 0x00020000, 0x00010000, 0x00008000,
    0x00004000, 0x00002000, 0x00001000, 0x00000800,
    0x00000400, 0x00000200, 0x00000100, 0x00000080,
    0x00000040, 0x00000020, 0x00000010, 0x00000008,
    0x00000004, 0x00000002, 0x00000001, 0x00000000 };

const unsigned int _trunc_table[] = {
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
    weakfloat(const float& f) : _f(f) { _trunc(_f); }
    weakfloat(const int& i) : _f(i) { _trunc(_f); }
    weakfloat(const unsigned int& u) : _f(u) { _trunc(_f); }
    //weakfloat(const float&& f) : _f(f){}
    weakfloat<N>& operator=(const float& f) {
      _f = f;
      _trunc(_f);
      return *this;
    }

    static void init(int rounding_mode) {
        rmode = rounding_mode;
    }

    //static int getRoundingMode() {return rmode;}

    void _trunc(float& f) {
        // nothing to do here.
        if (f == 0.)
            return;

        unsigned int *c = reinterpret_cast<unsigned int*>(&f);
        // Here set the different rounding modes:
        // upward:   if f & 0x00...01 then f += 0x000...01
        // downward: if f & 0x00...01 then f -= 0x000...01
        // etc.
        switch(rmode) {
            case FE_TOWARDZERO:
                // Truncate the same way whatever the sign is.
                break;

            case FE_UPWARD:
                if (f > 0.f) {
                    const unsigned int r = *c & (~_trunc_table[N]);
                    if (r != 0) {
                        const unsigned int tmp1(*c & _trunc_table[0]); // gets only the order.
                        const unsigned int tmp2(tmp1 | _ulp_table[N - 1]); // gets the order and the ulp to add.
                        *c += (tmp2 - tmp1); // Just add a bit, where the precision stops.
                    }
                }
                break;

            case FE_DOWNWARD:
                if (f < 0.f) {
                    const unsigned int r = *c & (~_trunc_table[N]);
                    if (r != 0) {
                        const unsigned int tmp1(*c & _trunc_table[0]); // gets only the order.
                        const unsigned int tmp2(tmp1 | _ulp_table[N - 1]); // gets the order and the ulp to add.
                        *c += (tmp2 - tmp1); // Just substract a bit, where the precision stops.
                    }
                }
                break;

            case FE_TONEAREST:
            default:
                const unsigned int r = *c & (~_trunc_table[N]);
                if (f > 0.f) {
                    if (r >= _ulp_table[N]) {
                        const unsigned int tmp1(*c & _trunc_table[0]); // gets only the order.
                        const unsigned int tmp2(tmp1 | _ulp_table[N - 1]); // gets the order and the ulp to add.
                        *c += (tmp2 - tmp1);
                    }
                } else { // f < 0.f because of the first test at the top of the function.
                    if (r >= _ulp_table[N]) {
                        const unsigned int tmp1(*c & _trunc_table[0]); // gets only the order.
                        const unsigned int tmp2(tmp1 | _ulp_table[N - 1]); // gets the order and the ulp to add.
                        *c += (tmp2 - tmp1);
                    }
                }
                break;
        }

        // This must be done for all.
        *c &= _trunc_table[N];
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

    operator float () const {
        return _f;
    }

    friend std::ostream& operator<< (std::ostream& out, const weakfloat<N>& x) {
        out << x._f;
        return out;
    }

  private:
    static int rmode;
    float _f;
};

template<int N>
int weakfloat<N>::rmode = FE_TONEAREST;
bool test_weak_float();

#endif
