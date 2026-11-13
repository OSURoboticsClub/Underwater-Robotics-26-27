#include "ros_publisher.h"

#include <godot_cpp/variant/utility_functions.hpp>

using namespace godot;

namespace ros2gd {

void RosPublisher::_bind_methods() {
    ClassDB::bind_method(D_METHOD("publish", "msg"), &RosPublisher::publish);
    ClassDB::bind_method(D_METHOD("get_topic_name"), &RosPublisher::get_topic_name);
    ClassDB::bind_method(D_METHOD("get_type_name"), &RosPublisher::get_type_name);
}

void RosPublisher::setup(std::shared_ptr<void> handle, PublishFn fn,
                         const String &topic, const String &type) {
    publisher_handle_ = handle;
    publish_fn_ = fn;
    topic_name_ = topic;
    type_name_ = type;
}

void RosPublisher::publish(const Ref<RosMessage> &msg) {
    if (publish_fn_) {
        publish_fn_(msg);
    } else {
        UtilityFunctions::printerr("[ros2gd] Publisher not initialized");
    }
}

String RosPublisher::get_topic_name() const {
    return topic_name_;
}

String RosPublisher::get_type_name() const {
    return type_name_;
}

} // namespace ros2gd
