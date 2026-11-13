#ifndef ROS_NODE_H
#define ROS_NODE_H

#include <memory>
#include <vector>

#include <godot_cpp/classes/node.hpp>
#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/variant/callable.hpp>
#include <godot_cpp/variant/variant.hpp>

#include "ros_message.h"
#include "ros_publisher.h"
#include "ros_subscription.h"
#include "ros_qos_profile.h"

namespace ros2gd {

struct RclNodeHandle;
struct RclPublisherHandle;
struct RclSubscriptionHandle;

class RosNode : public godot::Node {
    GDCLASS(RosNode, godot::Node)

private:
    std::shared_ptr<RclNodeHandle> rcl_node_;
    godot::String node_name_;
    godot::String node_namespace_;

    std::vector<godot::Ref<RosPublisher>> publishers_;
    std::vector<godot::Ref<RosSubscription>> subscriptions_;
    std::vector<std::shared_ptr<RclSubscriptionHandle>> rcl_subscriptions_;

    static int node_count_;

    static BridgeQoS variant_to_qos(const godot::Variant &qos_var);

protected:
    static void _bind_methods();

public:
    RosNode();
    ~RosNode();

    void _enter_tree() override;
    void _exit_tree() override;

    void set_node_name(const godot::String &name);
    godot::String get_node_name() const;

    void set_node_namespace(const godot::String &ns);
    godot::String get_node_namespace() const;

    // type_name: "geometry_msgs/msg/Twist" etc.
    // qos: int (depth) or RosQoSProfile
    godot::Ref<RosPublisher> create_publisher(
        const godot::String &type_name,
        const godot::String &topic,
        const godot::Variant &qos);

    godot::Ref<RosSubscription> create_subscription(
        const godot::String &type_name,
        const godot::String &topic,
        const godot::Callable &callback,
        const godot::Variant &qos);

    void spin_some();
    double now() const;
};

} // namespace ros2gd

#endif // ROS_NODE_H
