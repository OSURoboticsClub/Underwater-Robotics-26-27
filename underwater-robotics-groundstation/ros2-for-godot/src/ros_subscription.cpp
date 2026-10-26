#include "ros_subscription.h"

using namespace godot;

namespace ros2gd {

void RosSubscription::_bind_methods() {
    ClassDB::bind_method(D_METHOD("get_topic_name"), &RosSubscription::get_topic_name);
    ClassDB::bind_method(D_METHOD("get_type_name"), &RosSubscription::get_type_name);
}

void RosSubscription::setup(std::shared_ptr<void> handle,
                            const String &topic, const String &type) {
    subscription_handle_ = handle;
    topic_name_ = topic;
    type_name_ = type;
}

String RosSubscription::get_topic_name() const {
    return topic_name_;
}

String RosSubscription::get_type_name() const {
    return type_name_;
}

} // namespace ros2gd
