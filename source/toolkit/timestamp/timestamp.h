#ifndef TIMESTAMP_H
#define TIMESTAMP_H

#include <sstream>
#include <chrono>

#define today(a) (((a) / 86400) * 86400)

int to_int(const std::string& str);
double to_double(const std::string& str);

class TimeStamp {
public:
    static void printLocalTime(time_t t = time(NULL));
    static void printGmtTime(time_t t);

    static void stampLocalStream(std::ostream &out, time_t t = time(NULL));
    static void stampGMTStream(std::ostream &out, time_t t);

    static std::string gmtStamp(time_t date);
    static std::string localStamp(time_t date);
    static std::string gmtDateStamp(time_t date);

    static void gmtDateStream(std::ostream &out, time_t date);

    /// Returns local hour.
    static int getLocalHour(time_t t);

    /// Elastic Search TimeStamp format.
    static std::string elasticsearch(std::chrono::system_clock::time_point t);
    static std::string elasticsearch(time_t t);
    static std::string elasticsearch(time_t t, int ms);
    static time_t elasticsearch(const std::string& timeString);
    static time_t yyyymmdd(const std::string& timeString);
    static time_t yyyymmdd(const unsigned int& dateNumber);

    /// Elastic Search TimeStamp format for precise logs with milliseconds.
    static std::string log();

private:
    TimeStamp(){}
    static int writer(char *data, size_t size, size_t nmemb,std::string *writerData);
};

#endif // TIMESTAMP_H
