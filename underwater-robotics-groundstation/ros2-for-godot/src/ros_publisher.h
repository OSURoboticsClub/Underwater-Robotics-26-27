#ifndef ROS_PUBLISHER_H
#define ROS_PUBLISHER_H

#include <functional>
#include <memory>

#include <godot_cpp/classes/ref_counted.hpp>
#include <godot_cpp/core/class_db.hpp>

#include "ros_message.h"

namespace ros2gd {

class RosPublisher : public godot::RefCounted {
    GDCLASS(RosPublisher, godot::RefCounted)

public:
    using PublishFn = std::function<void(const godot::Ref<RosMessage> &)>;

private:
    std::shared_ptr<void> publisher_handle_;
    PublishFn publish_fn_;
    godot::String topic_name_;
    godot::String type_name_;

protected:
    static void _bind_methods();

public:
    RosPublisher() = default;
    ~RosPublisher() = default;

    void setup(std::shared_ptr<void> handle, PublishFn fn,
               const godot::String &topic, const godot::String &type);

    void publish(const godot::Ref<RosMessage> &msg);

    godot::String get_topic_name() const;
    godot::String get_type_name() const;
};

} // namespace ros2gd

#endif // ROS_PUBLISHER_H
