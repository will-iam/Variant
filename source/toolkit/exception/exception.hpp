#ifndef EXCEPTION_H
#define EXCEPTION_H
#include <stdexcept>
#include <cstring>

#define EXCEPTION(...) throw Exception(__FILE__, __LINE__, __VA_ARGS__)
#define WARNING(...) _warning(__FILE__, __LINE__, __VA_ARGS__)
#define exitfail(...) _fail(__FILE__, __LINE__, __VA_ARGS__)

#define STRING2(x) #x
#define STRING(x) STRING2(x)

#define DO_PRAGMA(x) _Pragma (#x)
#define MAKEMESSAGE(x,f,l) DO_PRAGMA(message("In file " f " at " STRING(l) ":" #x))
#define ADDWARNING(x) MAKEMESSAGE(x, __FILE__ , __LINE__)

#ifdef NDEBUG
#define DEBUG(i,...)
#else
#define DEBUG(i,...) if(i <= VERBOSE) {_debug(__FILE__, __LINE__,__VA_ARGS__);}
#endif

#include <iostream>
#include "timestamp/timestamp.h"

class Console {
    public:
        static const int esc = 27;

        static void color(char c)       {printf("%c[%dm", esc, c);} /* couleur de 30 a 47 */
        static void bell(int n)         {do {printf("%c", 7) ; n-- ;} while (n > 0);}
        static void bold()              {printf ("%c[1m", esc) ;} /* -- couleur -- */
        static void clreol()            {printf ("%c[0K", esc) ;} /* -- clear eol -- */
        static void clrscreen()         {printf ("%c[2J%c[H", esc, esc) ;}
        static void cursoff()           {printf ("%c[?25l", esc) ;}
        static void curson()            {printf ("%c[?25h", esc) ;}
        static void home()              {printf ("%c[H", esc)  ;}
        static void insert()            {printf ("%c[4h", esc) ;}
        static void normal()            {printf ("%c[0;24m", esc) ;}  /* retour de bold , overstrike , underline */
        static void poscur(int l,int c) {printf ("%c[%1d;%1dH", esc, l, c);}
        static void replace()           {printf ("%c[4l", esc) ;}
        static void underline()         {printf ("%c[4m", esc) ;}
        static void videoff()           {printf ("%c[27m", esc);}
        static void videon()            {printf ("%c[7m", esc) ;}
        static void blink()             {printf ("%c[5m", esc);}

        enum Mode { _normal, _bold, _black, _red, _green, _yellow, _blue, _pink, _cyan };
        friend std::ostream& operator<< (std::ostream& os, const Mode& mode);

    private:
        Console(){}
    };

void convert(std::ostream& o, const char *s);

template <typename T1, typename T2>
std::ostream& operator<<(std::ostream& os, std::pair<T1, T2> p) {
    os << "(" << p.first << " ; " << p.second << ")";
}

template<typename T, typename... Args>
void convert(std::ostream& o, const char *s, T& value, Args... args) {
    while (*s) {
        if (*s == '%') {
            if (*(s + 1) == '%') {
                ++s;
            }
            else {
                o << value;
                convert(o, s + 1, args...); // call even when *s == 0 to detect extra arguments
                return;
            }
        }
        o << *s++;
    }
    static const int size = sizeof...(Args);
    std::cerr << Console::_red << "And by the way extra arguments provided to printf." << Console::_normal;
    std::cerr << "convert: \"" << s << "\", #" << size + 1 << std::endl;
}

template<typename T>
void _fail(const char* fil, int lin, T const& msg) {
    std::cerr << Console::_bold << Console::_red << TimeStamp::localStamp(time(NULL)) << " - Failure : in file " << fil << " at line number " << lin << ":" << Console::_normal << Console::_red << std::endl;
    std::cerr << msg << std::endl << Console::_normal;

    exit(EXIT_FAILURE);
}

template<typename T, typename... Args>
void _fail(const char* fil, int lin, const char* message, const T& value, Args... args) {

    std::cerr << Console::_bold << Console::_red << TimeStamp::localStamp(time(NULL)) << " - Failure : in file " << fil << " at line number " << lin << ":" << Console::_normal << Console::_red << std::endl;
    std::stringstream ss;
    while (*message) {
        if (*message == '%') {
            if (*(message + 1) == '%') {
                ++message;
            }
            else {
                ss << value;
                convert(ss, message + 1, args...); // call even when *s == 0 to detect extra arguments
                std::cerr << ss.str() << std::endl << Console::_normal;
                exit(EXIT_FAILURE);
            }
        }
        ss << *message++;
    }

    static const int size = sizeof...(Args);
    std::cerr << Console::_red << "And by the way extra arguments provided to printf." << Console::_normal;
    std::cerr << "In File: " << fil << " l." << lin << ": \"" << message << "\", #" << size + 1 << std::endl;
    exit(EXIT_FAILURE);
}

class Exception : std::exception {
    public:
        template<typename T>
        Exception(const char* fil, int lin, T const& msg);

        template<typename T, typename... Args>
        Exception(const char* fil, int lin, const char* msg, const T& value,  Args... args);
        const char* what() const throw() { return _msg.c_str(); }

        virtual ~Exception() throw() {}


    private:
        Exception(){}
        std::string _msg;
};


template<typename T>
Exception::Exception(const char* fil, int lin, T const& msg) {
    _msg = msg;
    std::cerr << Console::_red << Console::_bold << TimeStamp::localStamp(time(NULL)) << ": Exception in "<< fil << " l. " << lin << " ->\n";
    std::cerr << Console::_normal << Console::_red << _msg << Console::_normal << std::endl;
}

template<typename T, typename... Args>
Exception::Exception(const char* fil, int lin, const char* msg, const T& value, Args... args) {

    std::cerr << Console::_red << Console::_bold << TimeStamp::localStamp(time(NULL)) << ": Exception in "<< fil << " l. " << lin << " ->\n";
    std::stringstream ss;
    while (*msg) {
        if (*msg == '%') {
            if (*(msg + 1) == '%') {
                ++msg;
            }
            else {
                ss << value;
                convert(ss, msg + 1, args...); // call even when *s == 0 to detect extra arguments
                _msg = ss.str();

                // Test if errno is set and reset it before logging the error.
                if( errno != 0 ) {
                    _msg += std::string(" (errno: ") + std::string(strerror(errno)) + std::string(")");
                    errno = 0;
                }

                std::cerr << Console::_normal << Console::_red << _msg << Console::_normal << std::endl;
                return;
            }
        }
        ss << *msg++;
    }
    static const int size = sizeof...(Args);
    std::cerr << Console::_red << "And by the way extra arguments provided to printf." << Console::_normal;
    std::cerr << "In File: " << fil << " l." << lin << ": \"" << msg << "\", #" << size + 1 << std::endl;
}

void title(const char *mask, ...);
void emphasize(const char *mask, ...);

template<typename T>
void _warning(const char* fil, int lin, T const& msg) {

    // Show the warning.
    std::cerr << Console::_bold << Console::_pink << "Warning: ";
    std::cerr << TimeStamp::localStamp(time(NULL)) << " in " << fil << " l. " << lin << " ->" << std::endl;
    std::cerr << Console::_normal << Console::_pink << msg << Console::_normal << std::endl;
}

template<typename T, typename... Args>
void _warning(const char* fil, int lin, const char* message, const T& value, Args... args) {

    std::cerr << Console::_bold << Console::_pink << "Warning: ";
    std::cerr << TimeStamp::localStamp(time(NULL)) << " in " << fil << " l. " << lin << " ->" << std::endl;

    std::stringstream ss;
    while (*message) {
        if (*message == '%') {
            if (*(message + 1) == '%') {
                ++message;
            }
            else {
                ss << value;
                convert(ss, message + 1, args...); // call even when *s == 0 to detect extra arguments

                // Show the warning.
                std::cerr << Console::_normal << Console::_pink <<  ss.str() << Console::_normal << std::endl;

                // Finally returns.
                return;
            }
        }
        ss << *message++;
    }

    static const int size = sizeof...(Args);
    std::cerr << Console::_red << "And by the way extra arguments provided to printf." << Console::_normal;
    std::cerr << "In File: " << fil << " l." << lin << ": \"" << message << "\", #" << size + 1 << std::endl;
    exit(EXIT_FAILURE);
}

template<typename T>
void _debug(bool log, const char* fil, int lin, T const& msg) {

    // Show the warning.
    std::cerr << Console::_bold << Console::_yellow << "Debug -> ";
    std::cerr << fil << " l." << lin << ":" << std::endl;
    std::cerr << Console::_normal << Console::_yellow << msg << Console::_normal << std::endl;
}

template<typename T, typename... Args>
void _debug(const char* fil, int lin, const char* message, const T& value, Args... args) {

    std::cerr << Console::_bold << Console::_yellow << "Debug -> ";
    std::cerr << fil << " l." << lin << ":" << std::endl;

    std::stringstream ss;
    while (*message) {
        if (*message == '%') {
            if (*(message + 1) == '%') {
                ++message;
            }
            else {
                ss << value;
                convert(ss, message + 1, args...); // call even when *s == 0 to detect extra arguments

                // Show the debug message.
                std::cerr << Console::_normal << Console::_yellow << ss.str() << Console::_normal << std::endl;

                // Finally returns.
                return;
            }
        }
        ss << *message++;
    }

    static const int size = sizeof...(Args);
    std::cerr << Console::_red << "And by the way extra arguments provided to printf." << Console::_normal;
    std::cerr << "In File: " << fil << " l." << lin << ": \"" << message << "\", #" << size + 1 << std::endl;
    exit(EXIT_FAILURE);
}

#endif // EXCEPTION_H
