// This file includes rclcpp headers ONLY — no godot-cpp headers.

#include "ros_bridge.h"

#include <rclcpp/rclcpp.hpp>

namespace ros2gd {

// --- Handle types (opaque to the Godot side) ---

struct RclNodeHandle {
    rclcpp::Node::SharedPtr node;
};

struct RclPublisherHandle {
    std::shared_ptr<void> publisher;
};

struct RclSubscriptionHandle {
    std::shared_ptr<void> subscription;
};

// --- ROS lifecycle ---

void bridge_init() {
    if (!rclcpp::ok()) {
        rclcpp::init(0, nullptr);
    }
}

void bridge_shutdown() {
    if (rclcpp::ok()) {
        rclcpp::shutdown();
    }
}

bool bridge_ok() {
    return rclcpp::ok();
}

// --- Node ---

std::shared_ptr<RclNodeHandle> bridge_create_node(
        const std::string &name, const std::string &ns) {
    auto handle = std::make_shared<RclNodeHandle>();
    handle->node = std::make_shared<rclcpp::Node>(name, ns);
    return handle;
}

void bridge_destroy_node(std::shared_ptr<RclNodeHandle> &node) {
    if (node) {
        node->node.reset();
        node.reset();
    }
}

void bridge_spin_some(const std::shared_ptr<RclNodeHandle> &node) {
    if (node && node->node) {
        rclcpp::spin_some(node->node);
    }
}

double bridge_now(const std::shared_ptr<RclNodeHandle> &node) {
    if (node && node->node) {
        return node->node->get_clock()->now().seconds();
    }
    return 0.0;
}

// --- QoS conversion ---

void *make_rcl_qos(const BridgeQoS &bq) {
    auto *qos = new rclcpp::QoS(bq.depth);

    switch (bq.history) {
        case 0: qos->keep_last(bq.depth); break;
        case 1: qos->keep_all(); break;
        default: break;
    }
    switch (bq.reliability) {
        case 0: qos->reliable(); break;
        case 1: qos->best_effort(); break;
        default: break;
    }
    switch (bq.durability) {
        case 0: qos->durability_volatile(); break;
        case 1: qos->transient_local(); break;
        default: break;
    }
    if (bq.deadline_ns > 0) {
        qos->deadline(rclcpp::Duration(std::chrono::nanoseconds(bq.deadline_ns)));
    }
    if (bq.lifespan_ns > 0) {
        qos->lifespan(rclcpp::Duration(std::chrono::nanoseconds(bq.lifespan_ns)));
    }
    switch (bq.liveliness) {
        case 0: qos->liveliness(rclcpp::LivelinessPolicy::Automatic); break;
        case 1: qos->liveliness(rclcpp::LivelinessPolicy::ManualByTopic); break;
        default: break;
    }
    if (bq.liveliness_lease_duration_ns > 0) {
        qos->liveliness_lease_duration(rclcpp::Duration(std::chrono::nanoseconds(bq.liveliness_lease_duration_ns)));
    }

    return qos;
}

void delete_rcl_qos(void *qos) {
    delete static_cast<rclcpp::QoS *>(qos);
}

// --- Internal accessors for generated bridge code ---

void *get_rcl_node_raw(const std::shared_ptr<RclNodeHandle> &node) {
    return node ? node->node.get() : nullptr;
}

std::shared_ptr<void> get_pub_ptr(const std::shared_ptr<RclPublisherHandle> &pub) {
    return pub ? pub->publisher : nullptr;
}

std::shared_ptr<RclPublisherHandle> make_pub_handle(std::shared_ptr<void> pub) {
    auto handle = std::make_shared<RclPublisherHandle>();
    handle->publisher = pub;
    return handle;
}

std::shared_ptr<RclSubscriptionHandle> make_sub_handle(std::shared_ptr<void> sub) {
    auto handle = std::make_shared<RclSubscriptionHandle>();
    handle->subscription = sub;
    return handle;
}

} // namespace ros2gd
