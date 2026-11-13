#ifndef ROS_MSG_H
#define ROS_MSG_H

#include <godot_cpp/classes/ref_counted.hpp>
#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/variant/string.hpp>

#include "ros_message.h"

namespace ros2gd {

// Factory class for creating message instances by ROS type name.
// Usage in GDScript: var msg = RosMsg.create("geometry_msgs/msg/Twist")
class RosMsg : public godot::RefCounted {
    GDCLASS(RosMsg, godot::RefCounted)

protected:
    static void _bind_methods();

public:
    static godot::Ref<RosMessage> create(const godot::String &type_name);
};

} // namespace ros2gd

#endif // ROS_MSG_H
