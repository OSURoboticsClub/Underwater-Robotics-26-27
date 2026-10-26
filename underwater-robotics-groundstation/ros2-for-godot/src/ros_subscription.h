#ifndef ROS_SUBSCRIPTION_H
#define ROS_SUBSCRIPTION_H

#include <memory>

#include <godot_cpp/classes/ref_counted.hpp>
#include <godot_cpp/core/class_db.hpp>

namespace ros2gd {

class RosSubscription : public godot::RefCounted {
    GDCLASS(RosSubscription, godot::RefCounted)

private:
    std::shared_ptr<void> subscription_handle_;
    godot::String topic_name_;
    godot::String type_name_;

protected:
    static void _bind_methods();

public:
    RosSubscription() = default;
    ~RosSubscription() = default;

    void setup(std::shared_ptr<void> handle,
               const godot::String &topic, const godot::String &type);

    godot::String get_topic_name() const;
    godot::String get_type_name() const;
};

} // namespace ros2gd

#endif // ROS_SUBSCRIPTION_H
