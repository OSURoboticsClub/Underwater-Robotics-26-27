#ifndef REGISTER_TYPES_H
#define REGISTER_TYPES_H

#include <godot_cpp/core/class_db.hpp>

void initialize_ros2_for_godot(godot::ModuleInitializationLevel p_level);
void uninitialize_ros2_for_godot(godot::ModuleInitializationLevel p_level);

#endif // REGISTER_TYPES_H
