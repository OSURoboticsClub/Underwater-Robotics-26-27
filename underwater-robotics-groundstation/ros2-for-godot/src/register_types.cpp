#include "register_types.h"

#include <gdextension_interface.h>
#include <godot_cpp/core/defs.hpp>
#include <godot_cpp/godot.hpp>

#include "ros_message.h"
#include "ros_publisher.h"
#include "ros_subscription.h"
#include "ros_qos_profile.h"
#include "ros_msg.h"
#include "ros_node.h"
#include "register_all_msgs.h"

using namespace godot;

void initialize_ros2_for_godot(ModuleInitializationLevel p_level) {
    if (p_level != MODULE_INITIALIZATION_LEVEL_SCENE) {
        return;
    }

    ClassDB::register_class<ros2gd::RosMessage>();
    ClassDB::register_class<ros2gd::RosPublisher>();
    ClassDB::register_class<ros2gd::RosSubscription>();
    ClassDB::register_class<ros2gd::RosQoSProfile>();
    ClassDB::register_class<ros2gd::RosMsg>();
    ClassDB::register_class<ros2gd::RosNode>();

    // Register all generated message classes
    register_all_generated_msgs();
}

void uninitialize_ros2_for_godot(ModuleInitializationLevel p_level) {
    if (p_level != MODULE_INITIALIZATION_LEVEL_SCENE) {
        return;
    }
}

extern "C" {

GDExtensionBool GDE_EXPORT ros2_for_godot_init(
        GDExtensionInterfaceGetProcAddress p_get_proc_address,
        const GDExtensionClassLibraryPtr p_library,
        GDExtensionInitialization *r_initialization) {
    godot::GDExtensionBinding::InitObject init_obj(p_get_proc_address, p_library, r_initialization);

    init_obj.register_initializer(initialize_ros2_for_godot);
    init_obj.register_terminator(uninitialize_ros2_for_godot);
    init_obj.set_minimum_library_initialization_level(MODULE_INITIALIZATION_LEVEL_SCENE);

    return init_obj.init();
}

}
