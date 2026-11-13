#include "ros_msg.h"
#include "msg_factory.h"

using namespace godot;

namespace ros2gd {

void RosMsg::_bind_methods() {
    ClassDB::bind_static_method("RosMsg", D_METHOD("create", "type_name"), &RosMsg::create);
}

Ref<RosMessage> RosMsg::create(const String &type_name) {
    return factory_create_message(type_name);
}

} // namespace ros2gd
