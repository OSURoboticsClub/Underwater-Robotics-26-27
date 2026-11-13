#include "ros_message.h"

using namespace godot;

namespace ros2gd {

void RosMessage::_bind_methods() {
    ClassDB::bind_method(D_METHOD("get_type_name"), &RosMessage::get_type_name);
}

String RosMessage::get_type_name() const {
    return String();
}

} // namespace ros2gd
