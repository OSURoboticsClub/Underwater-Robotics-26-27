#include "ros_node.h"
#include "ros_bridge.h"
#include "msg_factory.h"

#include <godot_cpp/variant/utility_functions.hpp>
#include <godot_cpp/classes/engine.hpp>

using namespace godot;

namespace ros2gd {

int RosNode::node_count_ = 0;

BridgeQoS RosNode::variant_to_qos(const Variant &qos_var) {
    if (qos_var.get_type() == Variant::INT) {
        return RosQoSProfile::from_depth(qos_var);
    }
    if (qos_var.get_type() == Variant::OBJECT) {
        Ref<RosQoSProfile> profile = qos_var;
        if (profile.is_valid()) {
            return profile->to_bridge();
        }
    }
    return RosQoSProfile::from_depth(10);
}

RosNode::RosNode() {
    node_name_ = "godot_ros_node";
    node_namespace_ = "";
}

RosNode::~RosNode() {
}

void RosNode::_enter_tree() {
    if (Engine::get_singleton()->is_editor_hint()) {
        return;
    }

    bridge_init();

    std::string name = node_name_.utf8().get_data();
    std::string ns = node_namespace_.utf8().get_data();

    rcl_node_ = bridge_create_node(name, ns);
    if (rcl_node_) {
        node_count_++;
        UtilityFunctions::print("[ros2gd] Node '", node_name_, "' created");
    } else {
        UtilityFunctions::printerr("[ros2gd] Failed to create node '", node_name_, "'");
    }
}

void RosNode::_exit_tree() {
    if (Engine::get_singleton()->is_editor_hint()) {
        return;
    }

    publishers_.clear();
    subscriptions_.clear();
    rcl_subscriptions_.clear();

    bridge_destroy_node(rcl_node_);
    node_count_--;

    if (node_count_ <= 0) {
        bridge_shutdown();
    }

    UtilityFunctions::print("[ros2gd] Node '", node_name_, "' destroyed");
}

void RosNode::_bind_methods() {
    ClassDB::bind_method(D_METHOD("set_ros_node_name", "name"), &RosNode::set_node_name);
    ClassDB::bind_method(D_METHOD("get_ros_node_name"), &RosNode::get_node_name);
    ADD_PROPERTY(PropertyInfo(Variant::STRING, "ros_node_name"),
                 "set_ros_node_name", "get_ros_node_name");

    ClassDB::bind_method(D_METHOD("set_ros_namespace", "namespace"), &RosNode::set_node_namespace);
    ClassDB::bind_method(D_METHOD("get_ros_namespace"), &RosNode::get_node_namespace);
    ADD_PROPERTY(PropertyInfo(Variant::STRING, "ros_namespace"),
                 "set_ros_namespace", "get_ros_namespace");

    ClassDB::bind_method(D_METHOD("create_publisher", "type_name", "topic", "qos"),
                         &RosNode::create_publisher);
    ClassDB::bind_method(D_METHOD("create_subscription", "type_name", "topic", "callback", "qos"),
                         &RosNode::create_subscription);
    ClassDB::bind_method(D_METHOD("spin_some"), &RosNode::spin_some);
    ClassDB::bind_method(D_METHOD("now"), &RosNode::now);
}

void RosNode::set_node_name(const String &name) {
    node_name_ = name;
}

String RosNode::get_node_name() const {
    return node_name_;
}

void RosNode::set_node_namespace(const String &ns) {
    node_namespace_ = ns;
}

String RosNode::get_node_namespace() const {
    return node_namespace_;
}

Ref<RosPublisher> RosNode::create_publisher(
        const String &type_name,
        const String &topic,
        const Variant &qos) {
    if (!rcl_node_) {
        UtilityFunctions::printerr("[ros2gd] Node not initialized");
        return Ref<RosPublisher>();
    }

    BridgeQoS bridge_qos = variant_to_qos(qos);
    Ref<RosPublisher> pub = factory_create_publisher(rcl_node_, type_name, topic, bridge_qos);
    if (pub.is_valid()) {
        publishers_.push_back(pub);
        UtilityFunctions::print("[ros2gd] Publisher created: ", topic, " [", type_name, "]");
    }
    return pub;
}

Ref<RosSubscription> RosNode::create_subscription(
        const String &type_name,
        const String &topic,
        const Callable &callback,
        const Variant &qos) {
    if (!rcl_node_) {
        UtilityFunctions::printerr("[ros2gd] Node not initialized");
        return Ref<RosSubscription>();
    }

    BridgeQoS bridge_qos = variant_to_qos(qos);
    std::shared_ptr<RclSubscriptionHandle> sub_handle;
    Ref<RosSubscription> sub = factory_create_subscription(
        rcl_node_, type_name, topic, callback, bridge_qos, sub_handle);
    if (sub.is_valid()) {
        rcl_subscriptions_.push_back(sub_handle);
        subscriptions_.push_back(sub);
        UtilityFunctions::print("[ros2gd] Subscription created: ", topic, " [", type_name, "]");
    }
    return sub;
}

void RosNode::spin_some() {
    if (rcl_node_) {
        bridge_spin_some(rcl_node_);
    }
}

double RosNode::now() const {
    if (rcl_node_) {
        return bridge_now(rcl_node_);
    }
    return 0.0;
}

} // namespace ros2gd
