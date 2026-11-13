#ifndef ROS_QOS_PROFILE_H
#define ROS_QOS_PROFILE_H

#include <godot_cpp/classes/ref_counted.hpp>
#include <godot_cpp/core/class_db.hpp>

#include "ros_bridge.h"  // for BridgeQoS

namespace ros2gd {

class RosQoSProfile : public godot::RefCounted {
    GDCLASS(RosQoSProfile, godot::RefCounted)

public:
    enum Reliability { RELIABLE = 0, BEST_EFFORT = 1, RELIABILITY_SYSTEM_DEFAULT = 2 };
    enum Durability { VOLATILE = 0, TRANSIENT_LOCAL = 1, DURABILITY_SYSTEM_DEFAULT = 2 };
    enum History { KEEP_LAST = 0, KEEP_ALL = 1, HISTORY_SYSTEM_DEFAULT = 2 };
    enum Liveliness { AUTOMATIC = 0, MANUAL_BY_TOPIC = 1, LIVELINESS_SYSTEM_DEFAULT = 2 };

private:
    int reliability_ = RELIABLE;
    int durability_ = VOLATILE;
    int history_ = KEEP_LAST;
    int depth_ = 10;
    int64_t deadline_ns_ = 0;
    int64_t lifespan_ns_ = 0;
    int liveliness_ = AUTOMATIC;
    int64_t liveliness_lease_duration_ns_ = 0;

protected:
    static void _bind_methods();

public:
    RosQoSProfile() = default;
    ~RosQoSProfile() = default;

    // Setters / Getters
    void set_reliability(int v) { reliability_ = v; }
    int get_reliability() const { return reliability_; }

    void set_durability(int v) { durability_ = v; }
    int get_durability() const { return durability_; }

    void set_history(int v) { history_ = v; }
    int get_history() const { return history_; }

    void set_depth(int v) { depth_ = v; }
    int get_depth() const { return depth_; }

    void set_deadline_ns(int64_t v) { deadline_ns_ = v; }
    int64_t get_deadline_ns() const { return deadline_ns_; }

    void set_lifespan_ns(int64_t v) { lifespan_ns_ = v; }
    int64_t get_lifespan_ns() const { return lifespan_ns_; }

    void set_liveliness(int v) { liveliness_ = v; }
    int get_liveliness() const { return liveliness_; }

    void set_liveliness_lease_duration_ns(int64_t v) { liveliness_lease_duration_ns_ = v; }
    int64_t get_liveliness_lease_duration_ns() const { return liveliness_lease_duration_ns_; }

    // Convert to bridge struct
    BridgeQoS to_bridge() const;

    // --- Presets (rclpy-compatible names) ---
    static godot::Ref<RosQoSProfile> preset_default();
    static godot::Ref<RosQoSProfile> sensor_data();
    static godot::Ref<RosQoSProfile> services();
    static godot::Ref<RosQoSProfile> parameters();
    static godot::Ref<RosQoSProfile> parameter_events();
    static godot::Ref<RosQoSProfile> best_effort(int depth = 10);

    // Convenience: create from depth only (backward compat)
    static BridgeQoS from_depth(int depth);
};

} // namespace ros2gd

VARIANT_ENUM_CAST(ros2gd::RosQoSProfile::Reliability)
VARIANT_ENUM_CAST(ros2gd::RosQoSProfile::Durability)
VARIANT_ENUM_CAST(ros2gd::RosQoSProfile::History)
VARIANT_ENUM_CAST(ros2gd::RosQoSProfile::Liveliness)

#endif // ROS_QOS_PROFILE_H
