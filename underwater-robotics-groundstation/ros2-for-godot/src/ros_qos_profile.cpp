#include "ros_qos_profile.h"

using namespace godot;

namespace ros2gd {

void RosQoSProfile::_bind_methods() {
    // Enum constants
    BIND_ENUM_CONSTANT(RELIABLE);
    BIND_ENUM_CONSTANT(BEST_EFFORT);
    BIND_ENUM_CONSTANT(RELIABILITY_SYSTEM_DEFAULT);

    BIND_ENUM_CONSTANT(VOLATILE);
    BIND_ENUM_CONSTANT(TRANSIENT_LOCAL);
    BIND_ENUM_CONSTANT(DURABILITY_SYSTEM_DEFAULT);

    BIND_ENUM_CONSTANT(KEEP_LAST);
    BIND_ENUM_CONSTANT(KEEP_ALL);
    BIND_ENUM_CONSTANT(HISTORY_SYSTEM_DEFAULT);

    BIND_ENUM_CONSTANT(AUTOMATIC);
    BIND_ENUM_CONSTANT(MANUAL_BY_TOPIC);
    BIND_ENUM_CONSTANT(LIVELINESS_SYSTEM_DEFAULT);

    // Properties
    ClassDB::bind_method(D_METHOD("set_reliability", "value"), &RosQoSProfile::set_reliability);
    ClassDB::bind_method(D_METHOD("get_reliability"), &RosQoSProfile::get_reliability);
    ADD_PROPERTY(PropertyInfo(Variant::INT, "reliability", PROPERTY_HINT_ENUM, "Reliable,BestEffort,SystemDefault"),
                 "set_reliability", "get_reliability");

    ClassDB::bind_method(D_METHOD("set_durability", "value"), &RosQoSProfile::set_durability);
    ClassDB::bind_method(D_METHOD("get_durability"), &RosQoSProfile::get_durability);
    ADD_PROPERTY(PropertyInfo(Variant::INT, "durability", PROPERTY_HINT_ENUM, "Volatile,TransientLocal,SystemDefault"),
                 "set_durability", "get_durability");

    ClassDB::bind_method(D_METHOD("set_history", "value"), &RosQoSProfile::set_history);
    ClassDB::bind_method(D_METHOD("get_history"), &RosQoSProfile::get_history);
    ADD_PROPERTY(PropertyInfo(Variant::INT, "history", PROPERTY_HINT_ENUM, "KeepLast,KeepAll,SystemDefault"),
                 "set_history", "get_history");

    ClassDB::bind_method(D_METHOD("set_depth", "value"), &RosQoSProfile::set_depth);
    ClassDB::bind_method(D_METHOD("get_depth"), &RosQoSProfile::get_depth);
    ADD_PROPERTY(PropertyInfo(Variant::INT, "depth"), "set_depth", "get_depth");

    ClassDB::bind_method(D_METHOD("set_deadline_ns", "value"), &RosQoSProfile::set_deadline_ns);
    ClassDB::bind_method(D_METHOD("get_deadline_ns"), &RosQoSProfile::get_deadline_ns);
    ADD_PROPERTY(PropertyInfo(Variant::INT, "deadline_ns"), "set_deadline_ns", "get_deadline_ns");

    ClassDB::bind_method(D_METHOD("set_lifespan_ns", "value"), &RosQoSProfile::set_lifespan_ns);
    ClassDB::bind_method(D_METHOD("get_lifespan_ns"), &RosQoSProfile::get_lifespan_ns);
    ADD_PROPERTY(PropertyInfo(Variant::INT, "lifespan_ns"), "set_lifespan_ns", "get_lifespan_ns");

    ClassDB::bind_method(D_METHOD("set_liveliness", "value"), &RosQoSProfile::set_liveliness);
    ClassDB::bind_method(D_METHOD("get_liveliness"), &RosQoSProfile::get_liveliness);
    ADD_PROPERTY(PropertyInfo(Variant::INT, "liveliness", PROPERTY_HINT_ENUM, "Automatic,ManualByTopic,SystemDefault"),
                 "set_liveliness", "get_liveliness");

    ClassDB::bind_method(D_METHOD("set_liveliness_lease_duration_ns", "value"), &RosQoSProfile::set_liveliness_lease_duration_ns);
    ClassDB::bind_method(D_METHOD("get_liveliness_lease_duration_ns"), &RosQoSProfile::get_liveliness_lease_duration_ns);
    ADD_PROPERTY(PropertyInfo(Variant::INT, "liveliness_lease_duration_ns"),
                 "set_liveliness_lease_duration_ns", "get_liveliness_lease_duration_ns");

    // Preset static methods
    ClassDB::bind_static_method("RosQoSProfile", D_METHOD("preset_default"), &RosQoSProfile::preset_default);
    ClassDB::bind_static_method("RosQoSProfile", D_METHOD("sensor_data"), &RosQoSProfile::sensor_data);
    ClassDB::bind_static_method("RosQoSProfile", D_METHOD("services"), &RosQoSProfile::services);
    ClassDB::bind_static_method("RosQoSProfile", D_METHOD("parameters"), &RosQoSProfile::parameters);
    ClassDB::bind_static_method("RosQoSProfile", D_METHOD("parameter_events"), &RosQoSProfile::parameter_events);
    ClassDB::bind_static_method("RosQoSProfile", D_METHOD("best_effort", "depth"), &RosQoSProfile::best_effort, DEFVAL(10));
}

BridgeQoS RosQoSProfile::to_bridge() const {
    BridgeQoS qos;
    qos.reliability = reliability_;
    qos.durability = durability_;
    qos.history = history_;
    qos.depth = depth_;
    qos.deadline_ns = deadline_ns_;
    qos.lifespan_ns = lifespan_ns_;
    qos.liveliness = liveliness_;
    qos.liveliness_lease_duration_ns = liveliness_lease_duration_ns_;
    return qos;
}

BridgeQoS RosQoSProfile::from_depth(int depth) {
    BridgeQoS qos;
    qos.depth = depth;
    return qos;
}

Ref<RosQoSProfile> RosQoSProfile::preset_default() {
    Ref<RosQoSProfile> p;
    p.instantiate();
    // RELIABLE, VOLATILE, KEEP_LAST(10) — matches rclcpp default
    return p;
}

Ref<RosQoSProfile> RosQoSProfile::sensor_data() {
    Ref<RosQoSProfile> p;
    p.instantiate();
    p->reliability_ = BEST_EFFORT;
    p->durability_ = VOLATILE;
    p->history_ = KEEP_LAST;
    p->depth_ = 5;
    return p;
}

Ref<RosQoSProfile> RosQoSProfile::services() {
    Ref<RosQoSProfile> p;
    p.instantiate();
    p->reliability_ = RELIABLE;
    p->durability_ = VOLATILE;
    p->history_ = KEEP_LAST;
    p->depth_ = 10;
    return p;
}

Ref<RosQoSProfile> RosQoSProfile::parameters() {
    Ref<RosQoSProfile> p;
    p.instantiate();
    p->reliability_ = RELIABLE;
    p->durability_ = VOLATILE;
    p->history_ = KEEP_LAST;
    p->depth_ = 1000;
    return p;
}

Ref<RosQoSProfile> RosQoSProfile::parameter_events() {
    Ref<RosQoSProfile> p;
    p.instantiate();
    p->reliability_ = RELIABLE;
    p->durability_ = VOLATILE;
    p->history_ = KEEP_LAST;
    p->depth_ = 1000;
    return p;
}

Ref<RosQoSProfile> RosQoSProfile::best_effort(int depth) {
    Ref<RosQoSProfile> p;
    p.instantiate();
    p->reliability_ = BEST_EFFORT;
    p->depth_ = depth;
    return p;
}

} // namespace ros2gd
