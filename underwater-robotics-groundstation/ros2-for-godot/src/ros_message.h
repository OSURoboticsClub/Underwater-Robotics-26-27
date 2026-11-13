#ifndef ROS_MESSAGE_H
#define ROS_MESSAGE_H

#include <godot_cpp/classes/ref_counted.hpp>
#include <godot_cpp/core/class_db.hpp>

namespace ros2gd {

class RosMessage : public godot::RefCounted {
    GDCLASS(RosMessage, godot::RefCounted)

protected:
    static void _bind_methods();

public:
    RosMessage() = default;
    virtual ~RosMessage() = default;

    virtual godot::String get_type_name() const;
};

} // namespace ros2gd

#endif // ROS_MESSAGE_H
