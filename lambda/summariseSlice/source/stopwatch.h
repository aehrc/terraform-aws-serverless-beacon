#ifndef _STOP_WATCH_HPP_
#define _STOP_WATCH_HPP_

#include <chrono>
#include <utility>
#include <iostream>

class stop_watch {
    std::chrono::high_resolution_clock::time_point last_time_point;
    std::chrono::duration<double> time_duration;
    bool is_running;
  public:
  int64_t nanoseconds;
    stop_watch() : 
      last_time_point {std::chrono::high_resolution_clock::now()},
      time_duration {std::chrono::duration<double>::zero()},
      is_running {false}
      {}
    void start() {
      last_time_point = std::chrono::high_resolution_clock::now();
      time_duration = std::chrono::duration<double>::zero();
      is_running = true;
    }
    void stop() {
      auto n = std::chrono::high_resolution_clock::now();
      time_duration = n - last_time_point;
      nanoseconds = std::chrono::duration_cast<
          std::chrono::nanoseconds>(time_duration).count();
      last_time_point = n;
      is_running = false;
    }
    int64_t hours() {
      return std::chrono::duration_cast<std::chrono::hours>(
          time_duration).count();
    }
    friend std::ostream& operator<<(std::ostream& out, stop_watch sw) {
      std::chrono::hours h = std::chrono::duration_cast<
          std::chrono::hours>(sw.time_duration);
      if (h.count()) {out << h.count() << "h "; sw.time_duration -= h;}
      std::chrono::minutes m = std::chrono::duration_cast<
          std::chrono::minutes>(sw.time_duration);
      if (m.count()) {out << m.count() << "min "; sw.time_duration -= m;}
      std::chrono::seconds s = std::chrono::duration_cast<
          std::chrono::seconds>(sw.time_duration);
      if (s.count()) {out << s.count() << "s "; sw.time_duration -= s;}
      std::chrono::milliseconds ms = std::chrono::duration_cast<
          std::chrono::milliseconds>(sw.time_duration);
      if (ms.count()) {out << ms.count() << "ms "; sw.time_duration -= ms;}
      std::chrono::microseconds us = std::chrono::duration_cast<
          std::chrono::microseconds>(sw.time_duration);
      if (us.count()) {out << us.count() << "us "; sw.time_duration -= us;}
      std::chrono::nanoseconds ns = std::chrono::duration_cast<
          std::chrono::nanoseconds>(sw.time_duration);
      if (ns.count()) {out << ns.count() << "ns "; sw.time_duration -= ns;}
      return out;
    }
};

#endif
