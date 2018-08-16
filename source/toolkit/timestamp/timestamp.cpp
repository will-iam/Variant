#include <cassert>
#include <ctime>
#include <iostream>
#include <sstream>

#include "timestamp.h"

#include <errno.h>
#include <cstring>

/*
 * Except for the strftime function, these functions each return a pointer to one of two types of static objects:
 * a broken-down time structure or an array of char. Execution of any of the functions that return a pointer to one of these object
 * types may overwrite the information in any object of the same type pointed to by the value returned from any previous call to any of them.
 * The implementation shall behave as if no other library functions call these functions.
 *
 * The four functions asctime(), ctime(), gmtime() and localtime() return a pointer to static data and hence are not thread-safe.
 * Thread-safe versions asctime_r(), ctime_r(), gmtime_r() and localtime_r() are specified by SUSv2, and available since libc 5.2.5
*/

int to_int(const std::string& str){
    int numb;
    std::istringstream ( str ) >> numb;
    return numb;
}

double to_double(const std::string& str){
    double numb;
    std::istringstream ( str ) >> numb;
    return numb;
}

template<typename T>
void showbits(T n) {
    int bitSize = 8*sizeof(T);
    std::cerr << "Number of bits = " << bitSize << std::endl;
    for (int bit = bitSize; bit >= 0 ;--bit)
        {std::cerr << ( (n >> bit) & 1 );}
    std::cerr << std::endl;
}

void TimeStamp::printLocalTime(time_t t) {
    tm thread_safe;
    tm *now=localtime_r(&t, &thread_safe);
    printf("[%i/%i/%i, %i:%i:%i %s]", now->tm_mday, now->tm_mon+1, now->tm_year+1900,  now->tm_hour, now->tm_min, now->tm_sec, now->tm_zone);

    assert(thread_safe.tm_year == now->tm_year);
    assert(thread_safe.tm_mon == now->tm_mon);
    assert(thread_safe.tm_mday == now->tm_mday);
    assert(thread_safe.tm_hour == now->tm_hour);
    assert(thread_safe.tm_min == now->tm_min);
    assert(thread_safe.tm_sec == now->tm_sec);
    assert(thread_safe.tm_zone == now->tm_zone);
    assert(thread_safe.tm_wday == now->tm_wday);
    assert(thread_safe.tm_gmtoff == now->tm_gmtoff);
    assert(thread_safe.tm_isdst == now->tm_isdst);
    assert(thread_safe.tm_yday == now->tm_yday);
}

void TimeStamp::printGmtTime(time_t t) {
    tm thread_safe;
    tm *now=gmtime_r(&t, &thread_safe);
    printf("[%i/%i/%i, %i:%i:%i %s]", now->tm_mday, now->tm_mon+1, now->tm_year+1900,  now->tm_hour, now->tm_min, now->tm_sec, now->tm_zone);

    assert(thread_safe.tm_year == now->tm_year);
    assert(thread_safe.tm_mon == now->tm_mon);
    assert(thread_safe.tm_mday == now->tm_mday);
    assert(thread_safe.tm_hour == now->tm_hour);
    assert(thread_safe.tm_min == now->tm_min);
    assert(thread_safe.tm_sec == now->tm_sec);
    assert(thread_safe.tm_zone == now->tm_zone);
    assert(thread_safe.tm_wday == now->tm_wday);
    assert(thread_safe.tm_gmtoff == now->tm_gmtoff);
    assert(thread_safe.tm_isdst == now->tm_isdst);
    assert(thread_safe.tm_yday == now->tm_yday);
}


void TimeStamp::stampGMTStream(std::ostream &out, time_t t) {
    tm thread_safe;
    tm *now=gmtime_r(&t, &thread_safe);
    out << "[" << now->tm_mday << "/" <<  now->tm_mon+1 << "/" << now->tm_year+1900 << ", " <<  now->tm_hour << ":" << now->tm_min << ":" << now->tm_sec << " " << now->tm_zone << "]";
}

void TimeStamp::stampLocalStream(std::ostream &out, time_t t) {
    tm thread_safe;
    tm *now=localtime_r(&t, &thread_safe);
    out << "[" << now->tm_mday << "/" <<  now->tm_mon+1 << "/" << now->tm_year+1900 << ", " <<  now->tm_hour << ":" << now->tm_min << ":" << now->tm_sec << " " << now->tm_zone << "]";
}

std::string TimeStamp::gmtStamp(time_t date){
    std::stringstream out;
    stampGMTStream(out, date);
    return out.str();
}

std::string TimeStamp::localStamp(time_t date){
    std::stringstream out;
    stampLocalStream(out, date);
    return out.str();
}

std::string TimeStamp::gmtDateStamp(time_t date){
    std::stringstream out;
    gmtDateStream(out, date);
    return out.str();
}

void TimeStamp::gmtDateStream(std::ostream &out, time_t date) {

    tm thread_safe;
    tm *now=gmtime_r(&date,&thread_safe);
    out << now->tm_year+1900;

    if( now->tm_mon+1 < 10 )
        out << "0";

    out << now->tm_mon+1;

    if( now->tm_mday < 10 )
        out << "0";

    out << now->tm_mday;

}

int TimeStamp::getLocalHour(time_t t) {

    tm thread_safe;
    tm *now=localtime_r(&t, &thread_safe);


    return now->tm_hour;
}

// Elastic Search TimeStamp format for precise logs with milliseconds.
std::string TimeStamp::log(){

    std::chrono::system_clock::time_point now = std::chrono::system_clock::now();
    time_t tnow = std::chrono::system_clock::to_time_t(now);
    std::chrono::system_clock::time_point withoutms = std::chrono::system_clock::from_time_t(tnow);
    int ms = std::chrono::duration_cast<std::chrono::milliseconds>(now - withoutms).count();

    return elasticsearch(tnow, ms);
}

// Elastic Search TimeStamp format.
std::string TimeStamp::elasticsearch(std::chrono::system_clock::time_point t){

    time_t tnow = std::chrono::system_clock::to_time_t(t);
    std::chrono::system_clock::time_point withoutms = std::chrono::system_clock::from_time_t(tnow);
    int ms = std::chrono::duration_cast<std::chrono::milliseconds>(t - withoutms).count();

    return elasticsearch(tnow, ms);
}

// Elastic Search TimeStamp format.
std::string TimeStamp::elasticsearch(time_t t, int ms){
    std::stringstream os;
    os << elasticsearch(t) << ".";
    if(ms < 100)
        os << "0";

    if(ms < 10)
        os << "0";

    os << ms;

    return os.str();
}

// Elastic Search TimeStamp format.
std::string TimeStamp::elasticsearch(time_t t){

    // Convert time_t to string
    std::stringstream os;
    tm thread_safe;
    tm *timeinfo=gmtime_r(&t, &thread_safe);
    os <<  timeinfo->tm_year+1900;

    if(timeinfo->tm_mon + 1 < 10)
        os << '0';
    os << timeinfo->tm_mon + 1;

    if(timeinfo->tm_mday < 10)
        os << '0';
    os << timeinfo->tm_mday << 'T';

    if(timeinfo->tm_hour < 10)
        os << '0';
    os << timeinfo->tm_hour;

    if(timeinfo->tm_min < 10)
        os << '0';
    os << timeinfo->tm_min;

    if(timeinfo->tm_sec < 10)
        os << '0';
    os << timeinfo->tm_sec;

    return os.str();
}

time_t TimeStamp::elasticsearch(const std::string& timeString){

    // The date string has this format: yyyyMMddTHHmmss.SSS
    // Convert the string into time_t.
    assert(timeString.size() == 15 || timeString.size() == 19);

    // Convert the string into time_t.
    time_t rawtime;
    time(&rawtime);
    tm thread_safe;
    tm* timeinfo = gmtime_r(&rawtime, &thread_safe);
    timeinfo->tm_year = to_int(timeString.substr(0,4)) - 1900;
    timeinfo->tm_mon = to_int(timeString.substr(4,2)) - 1;
    timeinfo->tm_mday = to_int(timeString.substr(6,2));
    timeinfo->tm_hour = to_int(timeString.substr(9,2));
    timeinfo->tm_min = to_int(timeString.substr(11,2));
    timeinfo->tm_sec = to_int(timeString.substr(13,2));

    return timegm(timeinfo);
}

time_t TimeStamp::yyyymmdd(const std::string& dateString){

    // The date string has this format: yyyyMMdd
    // Convert the string into time_t.
    assert(dateString.size() == 8);

    // Convert the string into time_t.
    time_t rawtime;
    time(&rawtime);
    tm thread_safe;
    tm* timeinfo = gmtime_r(&rawtime, &thread_safe);
    timeinfo->tm_year = to_int(dateString.substr(0,4)) - 1900;
    timeinfo->tm_mon = to_int(dateString.substr(4,2)) - 1;
    timeinfo->tm_mday = to_int(dateString.substr(6,2));

    // Set to midnight
    timeinfo->tm_hour = 0;
    timeinfo->tm_min = 0;
    timeinfo->tm_sec = 0;

    return timegm(timeinfo);
}

time_t TimeStamp::yyyymmdd(const unsigned int& dateNumber){

    // The date string has this format: yyyyMMdd
    // Convert the string into time_t.
    assert(dateNumber < 99991231);

    // Find the date
    unsigned int year = dateNumber / 10000;
    unsigned int month = (dateNumber - year*10000)/100;
    unsigned int day = dateNumber - year*10000 - month*100;

    assert(month <= 12 && month > 0);
    assert(day <= 31 && day > 0);

    time_t now = time(NULL);
    tm thread_safe;
    tm* timeinfo = gmtime_r(&now, &thread_safe);
    timeinfo->tm_year = year - 1900;
    timeinfo->tm_mon = month - 1;
    timeinfo->tm_mday = day;

    // Set to midnight
    timeinfo->tm_hour = 0;
    timeinfo->tm_min = 0;
    timeinfo->tm_sec = 0;

    return timegm(timeinfo);
}
