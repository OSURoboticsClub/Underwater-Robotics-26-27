// Bridge between Godot and rclcpp.
// This header uses ONLY standard C++ types — no godot-cpp, no rclcpp headers.
// The implementation (ros_bridge.cpp) includes rclcpp directly.

#ifndef ROS_BRIDGE_H
#define ROS_BRIDGE_H

#include <cstdint>
#include <functional>
#include <memory>
#include <string>
#include <vector>

namespace ros2gd {

// Forward declaration of internal handle (implemented in ros_bridge.cpp)
struct RclNodeHandle;
struct RclPublisherHandle;
struct RclSubscriptionHandle;

// Struct for passing vector3 data across the bridge
struct Vec3 {
    double x = 0, y = 0, z = 0;
};

// QoS profile (plain C++ — maps to rclcpp::QoS on the bridge side)
struct BridgeQoS {
    int reliability = 0;  // 0=RELIABLE, 1=BEST_EFFORT, 2=SYSTEM_DEFAULT
    int durability = 0;   // 0=VOLATILE, 1=TRANSIENT_LOCAL, 2=SYSTEM_DEFAULT
    int history = 0;      // 0=KEEP_LAST, 1=KEEP_ALL, 2=SYSTEM_DEFAULT
    int depth = 10;
    int64_t deadline_ns = 0;
    int64_t lifespan_ns = 0;
    int liveliness = 0;   // 0=AUTOMATIC, 1=MANUAL_BY_TOPIC, 2=SYSTEM_DEFAULT
    int64_t liveliness_lease_duration_ns = 0;
};

// --- ROS lifecycle ---
void bridge_init();
void bridge_shutdown();
bool bridge_ok();

// --- Node ---
std::shared_ptr<RclNodeHandle> bridge_create_node(
    const std::string &name, const std::string &ns);
void bridge_destroy_node(std::shared_ptr<RclNodeHandle> &node);
void bridge_spin_some(const std::shared_ptr<RclNodeHandle> &node);
double bridge_now(const std::shared_ptr<RclNodeHandle> &node);

// Convert BridgeQoS to rclcpp QoS (implemented in ros_bridge.cpp, rclcpp-only)
// Returns an opaque pointer to a heap-allocated rclcpp::QoS. Caller must free with delete_rcl_qos.
void *make_rcl_qos(const BridgeQoS &qos);
void delete_rcl_qos(void *qos);

// --- Internal accessors (used by generated bridge code) ---
// These return opaque pointers usable only in .cpp files that include rclcpp.
void *get_rcl_node_raw(const std::shared_ptr<RclNodeHandle> &node);
std::shared_ptr<void> get_pub_ptr(const std::shared_ptr<RclPublisherHandle> &pub);
std::shared_ptr<RclPublisherHandle> make_pub_handle(std::shared_ptr<void> pub);
std::shared_ptr<RclSubscriptionHandle> make_sub_handle(std::shared_ptr<void> sub);

} // namespace ros2gd

#endif // ROS_BRIDGE_H
