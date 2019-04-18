#ifndef WEAKFLOAT_HPP
#define WEAKFLOAT_HPP

static_assert(PRECISION_WEAK_FLOAT < 32);
static_assert(PRECISION_WEAK_FLOAT > 1);

template<int N>
class weakfloat {
  public:
    weakfloat() : _f(0.f){}
    weakfloat(const float& f) : _f(f) { trunc(_f); }
    weakfloat(const int& i) : _f(i) { trunc(_f); }
    weakfloat(const unsigned int& u) : _f(u) { trunc(_f); }
    //weakfloat(const float&& f) : _f(f){}

    void trunc(float& f) {
        unsigned char *c = reinterpret_cast<unsigned char *>(&f);
        // 0xff000000 
        *c &= 0xff000000;
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

#endif
