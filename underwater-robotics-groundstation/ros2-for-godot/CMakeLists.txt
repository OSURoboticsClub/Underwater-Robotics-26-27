cmake_minimum_required(VERSION 3.16)
project(ros2_for_godot LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# godot-cpp
add_subdirectory(godot-cpp)

# ROS2 packages
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2_msgs REQUIRED)

# --- Code generation ---
set(GEN_DIR "${CMAKE_CURRENT_BINARY_DIR}/gen")
set(GEN_PACKAGES "std_msgs;geometry_msgs;sensor_msgs;nav_msgs;tf2_msgs"
    CACHE STRING "ROS2 message packages to generate")
set(ROS_DIR "$ENV{AMENT_PREFIX_PATH}" CACHE PATH "ROS2 install directory (auto-detected from env)")

# Use first path from AMENT_PREFIX_PATH (colon-separated)
string(REPLACE ":" ";" _ament_paths "${ROS_DIR}")
list(GET _ament_paths 0 _ros_dir)

# Run generator at configure time
execute_process(
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/scripts/generate_msgs.py
        --ros-dir "${_ros_dir}"
        --packages ${GEN_PACKAGES}
        --out-dir "${GEN_DIR}"
    RESULT_VARIABLE _gen_result
)
if(NOT _gen_result EQUAL 0)
    # Fallback: try system python3
    execute_process(
        COMMAND python3 ${CMAKE_CURRENT_SOURCE_DIR}/scripts/generate_msgs.py
            --ros-dir "${_ros_dir}"
            --packages ${GEN_PACKAGES}
            --out-dir "${GEN_DIR}"
        RESULT_VARIABLE _gen_result
    )
    if(NOT _gen_result EQUAL 0)
        message(FATAL_ERROR "Message generation failed. Run manually:\n"
            "  python3 scripts/generate_msgs.py --ros-dir ${_ros_dir} --packages ${GEN_PACKAGES} --out-dir ${GEN_DIR}")
    endif()
endif()

# Include generated source lists
include(${GEN_DIR}/gen_sources.cmake)

# --- Bridge library (rclcpp side, no godot-cpp headers) ---
add_library(ros2_bridge STATIC
    src/ros_bridge.cpp
    ${GEN_BRIDGE_SOURCES}
)
target_include_directories(ros2_bridge PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${GEN_DIR}
)
target_link_libraries(ros2_bridge PUBLIC
    rclcpp::rclcpp
    ${std_msgs_TARGETS}
    ${builtin_interfaces_TARGETS}
    ${geometry_msgs_TARGETS}
    ${sensor_msgs_TARGETS}
    ${nav_msgs_TARGETS}
    ${tf2_msgs_TARGETS}
)
target_compile_options(ros2_bridge PRIVATE -fexceptions)

# --- GDExtension library (godot-cpp side) ---
add_library(ros2_for_godot SHARED
    src/register_types.cpp
    src/ros_message.cpp
    src/ros_publisher.cpp
    src/ros_subscription.cpp
    src/ros_qos_profile.cpp
    src/ros_msg.cpp
    src/ros_node.cpp
    ${GEN_GODOT_SOURCES}
)

target_include_directories(ros2_for_godot PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${GEN_DIR}
)

target_link_libraries(ros2_for_godot PUBLIC
    godot-cpp
    ros2_bridge
)
add_dependencies(ros2_for_godot godot-cpp)

# Output to build/bin/
set_target_properties(ros2_for_godot PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/bin"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/bin"
    PREFIX "lib"
)
