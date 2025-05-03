cmake_minimum_required(VERSION 3.10)
project(drogon)

set(CMAKE_CXX_STANDARD 17)

find_package(Drogon REQUIRED)

add_executable(drogon_app main.cc HomeController.cc)
target_link_libraries(drogon_app PRIVATE Drogon::Drogon)
