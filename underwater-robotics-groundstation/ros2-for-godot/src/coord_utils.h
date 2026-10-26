#ifndef COORD_UTILS_H
#define COORD_UTILS_H

#include <godot_cpp/variant/vector3.hpp>
#include <godot_cpp/variant/quaternion.hpp>
#include <godot_cpp/variant/basis.hpp>

// Godot: right-handed, Y-up (x-right, y-up, z-back)
// ROS (REP-103): right-handed, Z-up (x-forward, y-left, z-up)
//
// Mapping:
//   ROS x (forward)  = Godot -z
//   ROS y (left)     = Godot -x
//   ROS z (up)       = Godot  y

namespace ros2gd {

inline godot::Vector3 ros_to_godot(double ros_x, double ros_y, double ros_z) {
    return godot::Vector3(
        static_cast<float>(-ros_y),  // Godot x = -ROS y
        static_cast<float>(ros_z),   // Godot y =  ROS z
        static_cast<float>(-ros_x)   // Godot z = -ROS x
    );
}

inline void godot_to_ros(const godot::Vector3 &v, double &ros_x, double &ros_y, double &ros_z) {
    ros_x = -v.z;  // ROS x = -Godot z
    ros_y = -v.x;  // ROS y = -Godot x
    ros_z =  v.y;  // ROS z =  Godot y
}

inline godot::Quaternion ros_quat_to_godot(double qx, double qy, double qz, double qw) {
    // Apply the same axis remapping to quaternion components
    return godot::Quaternion(
        static_cast<float>(-qy),  // Godot qx = -ROS qy
        static_cast<float>(qz),   // Godot qy =  ROS qz
        static_cast<float>(-qx),  // Godot qz = -ROS qx
        static_cast<float>(qw)    // w unchanged
    );
}

inline void godot_quat_to_ros(const godot::Quaternion &q, double &qx, double &qy, double &qz, double &qw) {
    qx = -q.z;  // ROS qx = -Godot qz
    qy = -q.x;  // ROS qy = -Godot qx
    qz =  q.y;  // ROS qz =  Godot qy
    qw =  q.w;
}

} // namespace ros2gd

#endif // COORD_UTILS_H
