#!/usr/bin/env python3
"""
rosidl_generator_godot: Generate GDExtension C++ classes and bridge code from .msg files.

Usage:
    python3 generate_msgs.py --ros-dir /opt/ros/humble \
        --packages std_msgs geometry_msgs sensor_msgs nav_msgs tf2_msgs \
        --out-dir ../gen
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Type mappings
# ---------------------------------------------------------------------------

# ROS primitive → (bridge C++ type, Godot Variant type enum, Godot C++ type)
PRIMITIVE_MAP = {
    "bool":    ("bool",     "BOOL",  "bool"),
    "int8":    ("int8_t",   "INT",   "int64_t"),
    "uint8":   ("uint8_t",  "INT",   "int64_t"),
    "int16":   ("int16_t",  "INT",   "int64_t"),
    "uint16":  ("uint16_t", "INT",   "int64_t"),
    "int32":   ("int32_t",  "INT",   "int64_t"),
    "uint32":  ("uint32_t", "INT",   "int64_t"),
    "int64":   ("int64_t",  "INT",   "int64_t"),
    "uint64":  ("uint64_t", "INT",   "int64_t"),
    "float32": ("float",    "FLOAT", "double"),
    "float64": ("double",   "FLOAT", "double"),
    "string":  ("std::string", "STRING", "godot::String"),
    "byte":    ("uint8_t",  "INT",   "int64_t"),
    "char":    ("uint8_t",  "INT",   "int64_t"),
}

# ROS array → (bridge C++ type, Godot Variant type enum, Godot C++ type)
ARRAY_MAP = {
    "uint8":   ("std::vector<uint8_t>",  "PACKED_BYTE_ARRAY",    "godot::PackedByteArray"),
    "int8":    ("std::vector<int8_t>",   "PACKED_BYTE_ARRAY",    "godot::PackedByteArray"),
    "byte":    ("std::vector<uint8_t>",  "PACKED_BYTE_ARRAY",    "godot::PackedByteArray"),
    "int32":   ("std::vector<int32_t>",  "PACKED_INT32_ARRAY",   "godot::PackedInt32Array"),
    "uint32":  ("std::vector<uint32_t>", "PACKED_INT32_ARRAY",   "godot::PackedInt32Array"),
    "int64":   ("std::vector<int64_t>",  "PACKED_INT64_ARRAY",   "godot::PackedInt64Array"),
    "uint64":  ("std::vector<uint64_t>", "PACKED_INT64_ARRAY",   "godot::PackedInt64Array"),
    "float32": ("std::vector<float>",    "PACKED_FLOAT32_ARRAY", "godot::PackedFloat32Array"),
    "float64": ("std::vector<double>",   "PACKED_FLOAT64_ARRAY", "godot::PackedFloat64Array"),
    "string":  ("std::vector<std::string>", "PACKED_STRING_ARRAY", "godot::PackedStringArray"),
    "bool":    ("std::vector<uint8_t>",  "PACKED_BYTE_ARRAY",    "godot::PackedByteArray"),
}

# Special ROS types mapped to Godot native types
# (ros_type → godot_class, needs_coord_transform)
NATIVE_TYPE_MAP = {
    "geometry_msgs/msg/Vector3":    ("godot::Vector3",    True),
    "geometry_msgs/msg/Point":      ("godot::Vector3",    True),
    "geometry_msgs/msg/Point32":    ("godot::Vector3",    True),
    "geometry_msgs/msg/Quaternion": ("godot::Quaternion", True),
}

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class MsgField:
    ros_type: str           # e.g. "float64", "geometry_msgs/Vector3", "uint8[]"
    name: str
    default_value: Optional[str] = None
    is_array: bool = False
    is_fixed_array: bool = False
    array_size: int = 0
    base_type: str = ""     # type without [] suffix
    is_primitive: bool = False
    is_native_mapped: bool = False  # mapped to Godot native type
    is_constant: bool = False


@dataclass
class MsgDef:
    package: str            # e.g. "geometry_msgs"
    name: str               # e.g. "Twist"
    full_type: str = ""     # e.g. "geometry_msgs/msg/Twist"
    fields: List[MsgField] = field(default_factory=list)
    constants: List[MsgField] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse_msg_file(filepath: str, package: str, msg_name: str) -> MsgDef:
    """Parse a .msg file into a MsgDef."""
    msg = MsgDef(package=package, name=msg_name, full_type=f"{package}/msg/{msg_name}")

    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Check for constant definition: TYPE NAME = VALUE
            const_match = re.match(r"^(\S+)\s+(\w+)\s*=\s*(.+)$", line)
            if const_match:
                fld = MsgField(
                    ros_type=const_match.group(1),
                    name=const_match.group(2),
                    default_value=const_match.group(3).strip(),
                    is_constant=True,
                )
                msg.constants.append(fld)
                continue

            # Strip inline comments
            if "#" in line:
                line = line[:line.index("#")].strip()
            if not line:
                continue

            # Regular field: TYPE NAME [DEFAULT]
            parts = line.split()
            if len(parts) < 2:
                continue

            ros_type_raw = parts[0]
            fname = parts[1]
            default_val = parts[2] if len(parts) > 2 else None

            fld = MsgField(ros_type=ros_type_raw, name=fname, default_value=default_val)

            # Detect arrays
            fixed_match = re.match(r"^(.+)\[(\d+)\]$", ros_type_raw)
            dyn_match = re.match(r"^(.+)\[\]$", ros_type_raw)
            if fixed_match:
                fld.base_type = fixed_match.group(1)
                fld.is_array = True
                fld.is_fixed_array = True
                fld.array_size = int(fixed_match.group(2))
            elif dyn_match:
                fld.base_type = dyn_match.group(1)
                fld.is_array = True
            else:
                fld.base_type = ros_type_raw

            # Resolve package-relative types (e.g. "Vector3" → "geometry_msgs/msg/Vector3")
            if "/" not in fld.base_type and fld.base_type not in PRIMITIVE_MAP:
                fld.base_type = f"{package}/msg/{fld.base_type}"
                fld.ros_type = fld.base_type + ("[]" if fld.is_array and not fld.is_fixed_array
                                                 else f"[{fld.array_size}]" if fld.is_fixed_array
                                                 else "")

            # Normalize "pkg/Type" to "pkg/msg/Type"
            if "/" in fld.base_type and "/msg/" not in fld.base_type:
                parts2 = fld.base_type.split("/")
                if len(parts2) == 2:
                    fld.base_type = f"{parts2[0]}/msg/{parts2[1]}"

            fld.is_primitive = fld.base_type in PRIMITIVE_MAP
            fld.is_native_mapped = fld.base_type in NATIVE_TYPE_MAP

            msg.fields.append(fld)

    return msg


def discover_msgs(ros_dir: str, packages: List[str]) -> Dict[str, MsgDef]:
    """Discover and parse all .msg files for the given packages."""
    all_msgs: Dict[str, MsgDef] = {}

    for pkg in packages:
        msg_dir = os.path.join(ros_dir, "share", pkg, "msg")
        if not os.path.isdir(msg_dir):
            print(f"Warning: {msg_dir} not found, skipping {pkg}", file=sys.stderr)
            continue
        for fname in sorted(os.listdir(msg_dir)):
            if not fname.endswith(".msg"):
                continue
            msg_name = fname[:-4]
            filepath = os.path.join(msg_dir, fname)
            msg = parse_msg_file(filepath, pkg, msg_name)
            all_msgs[msg.full_type] = msg

    # Also parse builtin_interfaces for Time/Duration
    for pkg in ["builtin_interfaces"]:
        msg_dir = os.path.join(ros_dir, "share", pkg, "msg")
        if os.path.isdir(msg_dir):
            for fname in sorted(os.listdir(msg_dir)):
                if not fname.endswith(".msg"):
                    continue
                msg_name = fname[:-4]
                filepath = os.path.join(msg_dir, fname)
                msg = parse_msg_file(filepath, pkg, msg_name)
                all_msgs[msg.full_type] = msg

    return all_msgs


# ---------------------------------------------------------------------------
# Code generation helpers
# ---------------------------------------------------------------------------

def godot_class_name(msg: MsgDef) -> str:
    """e.g. geometry_msgs/msg/Twist → RosTwist"""
    return f"Ros{msg.name}"


def bridge_struct_name(msg: MsgDef) -> str:
    """e.g. geometry_msgs/msg/Twist → BridgeTwist"""
    return f"Bridge{msg.name}"


def ros_cpp_type(msg: MsgDef) -> str:
    """e.g. geometry_msgs/msg/Twist → geometry_msgs::msg::Twist"""
    return f"{msg.package}::msg::{msg.name}"


def ros_cpp_header(msg: MsgDef) -> str:
    """e.g. geometry_msgs/msg/Twist → geometry_msgs/msg/twist.hpp"""
    # Convert CamelCase to snake_case
    # Convert CamelCase to snake_case, keeping digit sequences attached
    # ColorRGBA → color_rgba, TF2Error → tf2_error, PointCloud2 → point_cloud2
    s = msg.name
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    s = s.lower()
    return f"{msg.package}/msg/{s}.hpp"


def snake_case(name: str) -> str:
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    return s.lower()


def file_base(msg: MsgDef) -> str:
    """File base name with ros_ prefix to avoid system header conflicts (e.g. time.h)."""
    return f"ros_{snake_case(msg.name)}"


def field_bridge_type(fld: MsgField, all_msgs: Dict[str, MsgDef]) -> str:
    """Get the bridge C++ type for a field."""
    if fld.is_primitive:
        if fld.is_array:
            return ARRAY_MAP.get(fld.base_type, ("std::vector<int>",))[0]
        if fld.is_fixed_array:
            bt = PRIMITIVE_MAP[fld.base_type][0]
            return f"std::array<{bt}, {fld.array_size}>"
        return PRIMITIVE_MAP[fld.base_type][0]

    if fld.is_native_mapped and not fld.is_array:
        # Native mapped types use specific bridge types
        if "Vector3" in fld.base_type or "Point" in fld.base_type:
            return "Vec3"
        if "Quaternion" in fld.base_type:
            return "Quat4"

    if fld.base_type in all_msgs:
        bname = bridge_struct_name(all_msgs[fld.base_type])
        if fld.is_array:
            return f"std::vector<{bname}>"
        return bname

    return "/* unknown */"


def field_godot_type(fld: MsgField, all_msgs: Dict[str, MsgDef]) -> Tuple[str, str]:
    """Get (Godot C++ type, Variant type enum) for a field."""
    if fld.is_primitive:
        if fld.is_array:
            entry = ARRAY_MAP.get(fld.base_type, ("PackedByteArray", "PACKED_BYTE_ARRAY", "godot::PackedByteArray"))
            return entry[2], entry[1]
        if fld.is_fixed_array:
            entry = ARRAY_MAP.get(fld.base_type, ("PackedFloat64Array", "PACKED_FLOAT64_ARRAY", "godot::PackedFloat64Array"))
            return entry[2], entry[1]
        return PRIMITIVE_MAP[fld.base_type][2], PRIMITIVE_MAP[fld.base_type][1]

    if fld.is_native_mapped and not fld.is_array:
        godot_type = NATIVE_TYPE_MAP[fld.base_type][0]
        if "Vector3" in godot_type:
            return godot_type, "VECTOR3"
        if "Quaternion" in godot_type:
            return godot_type, "QUATERNION"

    if fld.base_type in all_msgs:
        gname = godot_class_name(all_msgs[fld.base_type])
        if fld.is_array:
            return "godot::TypedArray<" + gname + ">", "ARRAY"
        return f"godot::Ref<{gname}>", "OBJECT"

    return "godot::Variant", "NIL"


def field_default_expr(fld: MsgField, godot_type: str) -> str:
    """Default initializer for a field."""
    if fld.default_value is not None:
        if "String" in godot_type:
            return f'"{fld.default_value}"'
        return fld.default_value
    if "Vector3" in godot_type:
        return ""
    if "Quaternion" in godot_type:
        return "0, 0, 0, 1"
    if "Ref<" in godot_type:
        return ""
    if "Array" in godot_type:
        return ""
    if "int" in godot_type:
        return "0"
    if "double" in godot_type or "float" in godot_type:
        return "0.0"
    if "bool" in godot_type:
        return "false"
    if "String" in godot_type:
        return ""
    return ""


# ---------------------------------------------------------------------------
# Sort messages topologically (dependencies first)
# ---------------------------------------------------------------------------

def topo_sort(msgs: Dict[str, MsgDef]) -> List[MsgDef]:
    """Sort messages so that dependencies appear before dependents."""
    visited = set()
    result = []

    def visit(full_type: str):
        if full_type in visited:
            return
        visited.add(full_type)
        if full_type not in msgs:
            return
        msg = msgs[full_type]
        for fld in msg.fields:
            if not fld.is_primitive and fld.base_type in msgs:
                visit(fld.base_type)
        result.append(msg)

    for ft in msgs:
        visit(ft)
    return result


# ---------------------------------------------------------------------------
# Generate bridge header (bridge_msgs.h)
# ---------------------------------------------------------------------------

def gen_bridge_header(msgs: List[MsgDef], all_msgs: Dict[str, MsgDef]) -> str:
    lines = [
        "// AUTO-GENERATED by generate_msgs.py — do not edit",
        "#ifndef BRIDGE_MSGS_H",
        "#define BRIDGE_MSGS_H",
        "",
        '#include "ros_bridge.h"',
        "",
        "#include <array>",
        "#include <cstdint>",
        "#include <string>",
        "#include <vector>",
        "",
        "namespace ros2gd {",
        "",
        "struct Quat4 { double x = 0, y = 0, z = 0, w = 1; };",
        "",
    ]

    for msg in msgs:
        sname = bridge_struct_name(msg)
        lines.append(f"struct {sname} {{")
        for fld in msg.fields:
            bt = field_bridge_type(fld, all_msgs)
            if fld.is_fixed_array and fld.is_primitive:
                prim_t = PRIMITIVE_MAP[fld.base_type][0]
                lines.append(f"    std::array<{prim_t}, {fld.array_size}> {fld.name}{{}};")
            else:
                lines.append(f"    {bt} {fld.name}{{}};")
        lines.append("};")
        lines.append("")

    # Declare per-type bridge functions
    for msg in msgs:
        sname = bridge_struct_name(msg)
        ft = msg.full_type.replace("/", "_")
        lines.append(f"std::shared_ptr<RclPublisherHandle> bridge_create_{ft}_publisher(")
        lines.append(f"    const std::shared_ptr<RclNodeHandle>& node, const std::string& topic, const BridgeQoS& qos);")
        lines.append(f"void bridge_publish_{ft}(")
        lines.append(f"    const std::shared_ptr<RclPublisherHandle>& pub, const {sname}& data);")
        lines.append(f"std::shared_ptr<RclSubscriptionHandle> bridge_create_{ft}_subscription(")
        lines.append(f"    const std::shared_ptr<RclNodeHandle>& node, const std::string& topic, const BridgeQoS& qos,")
        lines.append(f"    std::function<void(const {sname}&)> callback);")
        lines.append("")

    lines += ["} // namespace ros2gd", "", "#endif // BRIDGE_MSGS_H", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generate bridge implementation for one package (bridge_<pkg>.cpp)
# ---------------------------------------------------------------------------

def gen_ros_to_bridge(fld: MsgField, ros_expr: str, bridge_expr: str, all_msgs: Dict[str, MsgDef], indent: str = "    ") -> List[str]:
    """Generate code to copy from rclcpp message field to bridge struct field."""
    lines = []
    if fld.is_primitive and not fld.is_array and not fld.is_fixed_array:
        if fld.base_type == "string":
            lines.append(f"{indent}{bridge_expr} = {ros_expr};")
        else:
            lines.append(f"{indent}{bridge_expr} = {ros_expr};")
    elif fld.is_primitive and fld.is_fixed_array:  # check fixed BEFORE dynamic
        lines.append(f"{indent}std::copy({ros_expr}.begin(), {ros_expr}.end(), {bridge_expr}.begin());")
    elif fld.is_primitive and fld.is_array:
        lines.append(f"{indent}{bridge_expr}.assign({ros_expr}.begin(), {ros_expr}.end());")
    elif fld.is_native_mapped and not fld.is_array:
        if "Vector3" in fld.base_type or "Point" in fld.base_type:
            lines.append(f"{indent}{bridge_expr}.x = {ros_expr}.x;")
            lines.append(f"{indent}{bridge_expr}.y = {ros_expr}.y;")
            lines.append(f"{indent}{bridge_expr}.z = {ros_expr}.z;")
        elif "Quaternion" in fld.base_type:
            lines.append(f"{indent}{bridge_expr}.x = {ros_expr}.x;")
            lines.append(f"{indent}{bridge_expr}.y = {ros_expr}.y;")
            lines.append(f"{indent}{bridge_expr}.z = {ros_expr}.z;")
            lines.append(f"{indent}{bridge_expr}.w = {ros_expr}.w;")
    elif fld.base_type in all_msgs:
        sub_msg = all_msgs[fld.base_type]
        if fld.is_array:
            lines.append(f"{indent}{bridge_expr}.resize({ros_expr}.size());")
            lines.append(f"{indent}for (size_t i = 0; i < {ros_expr}.size(); ++i) {{")
            for sf in sub_msg.fields:
                lines += gen_ros_to_bridge(sf, f"{ros_expr}[i].{sf.name}", f"{bridge_expr}[i].{sf.name}", all_msgs, indent + "    ")
            lines.append(f"{indent}}}")
        else:
            for sf in sub_msg.fields:
                lines += gen_ros_to_bridge(sf, f"{ros_expr}.{sf.name}", f"{bridge_expr}.{sf.name}", all_msgs, indent)
    return lines


def gen_bridge_to_ros(fld: MsgField, bridge_expr: str, ros_expr: str, all_msgs: Dict[str, MsgDef], indent: str = "    ") -> List[str]:
    """Generate code to copy from bridge struct field to rclcpp message field."""
    lines = []
    if fld.is_primitive and not fld.is_array and not fld.is_fixed_array:
        lines.append(f"{indent}{ros_expr} = {bridge_expr};")
    elif fld.is_primitive and fld.is_fixed_array:  # check fixed BEFORE dynamic
        lines.append(f"{indent}std::copy({bridge_expr}.begin(), {bridge_expr}.end(), {ros_expr}.begin());")
    elif fld.is_primitive and fld.is_array:
        lines.append(f"{indent}{ros_expr}.assign({bridge_expr}.begin(), {bridge_expr}.end());")
    elif fld.is_native_mapped and not fld.is_array:
        if "Vector3" in fld.base_type or "Point" in fld.base_type:
            lines.append(f"{indent}{ros_expr}.x = {bridge_expr}.x;")
            lines.append(f"{indent}{ros_expr}.y = {bridge_expr}.y;")
            lines.append(f"{indent}{ros_expr}.z = {bridge_expr}.z;")
        elif "Quaternion" in fld.base_type:
            lines.append(f"{indent}{ros_expr}.x = {bridge_expr}.x;")
            lines.append(f"{indent}{ros_expr}.y = {bridge_expr}.y;")
            lines.append(f"{indent}{ros_expr}.z = {bridge_expr}.z;")
            lines.append(f"{indent}{ros_expr}.w = {bridge_expr}.w;")
    elif fld.base_type in all_msgs:
        sub_msg = all_msgs[fld.base_type]
        if fld.is_array:
            lines.append(f"{indent}{ros_expr}.resize({bridge_expr}.size());")
            lines.append(f"{indent}for (size_t i = 0; i < {bridge_expr}.size(); ++i) {{")
            for sf in sub_msg.fields:
                lines += gen_bridge_to_ros(sf, f"{bridge_expr}[i].{sf.name}", f"{ros_expr}[i].{sf.name}", all_msgs, indent + "    ")
            lines.append(f"{indent}}}")
        else:
            for sf in sub_msg.fields:
                lines += gen_bridge_to_ros(sf, f"{bridge_expr}.{sf.name}", f"{ros_expr}.{sf.name}", all_msgs, indent)
    return lines


def gen_bridge_impl(pkg: str, msgs: List[MsgDef], all_msgs: Dict[str, MsgDef]) -> str:
    lines = [
        "// AUTO-GENERATED by generate_msgs.py — do not edit",
        '#include "bridge_msgs.h"',
        "",
        "#include <rclcpp/rclcpp.hpp>",
    ]

    # Collect rclcpp includes
    includes = set()
    for msg in msgs:
        includes.add(f"#include <{ros_cpp_header(msg)}>")
        for fld in msg.fields:
            if fld.base_type in all_msgs:
                dep = all_msgs[fld.base_type]
                includes.add(f"#include <{ros_cpp_header(dep)}>")
    for inc in sorted(includes):
        lines.append(inc)
    lines += [
        "",
        "namespace ros2gd {",
        "",
        "// Inline helper: cast void* from get_rcl_node_raw() to rclcpp::Node*",
        "static inline rclcpp::Node* get_rcl_node(const std::shared_ptr<RclNodeHandle>& h) {",
        "    return static_cast<rclcpp::Node*>(get_rcl_node_raw(h));",
        "}",
        "",
    ]

    for msg in msgs:
        ft = msg.full_type.replace("/", "_")
        sname = bridge_struct_name(msg)
        rtype = ros_cpp_type(msg)

        # create_publisher
        lines.append(f"std::shared_ptr<RclPublisherHandle> bridge_create_{ft}_publisher(")
        lines.append(f"        const std::shared_ptr<RclNodeHandle>& node, const std::string& topic, const BridgeQoS& qos) {{")
        lines.append(f"    auto *rqos = static_cast<rclcpp::QoS*>(make_rcl_qos(qos));")
        lines.append(f"    auto pub = get_rcl_node(node)->create_publisher<{rtype}>(topic, *rqos);")
        lines.append(f"    delete_rcl_qos(rqos);")
        lines.append(f"    return make_pub_handle(pub);")
        lines.append(f"}}")
        lines.append("")

        # publish
        lines.append(f"void bridge_publish_{ft}(")
        lines.append(f"        const std::shared_ptr<RclPublisherHandle>& pub, const {sname}& data) {{")
        lines.append(f"    auto typed_pub = std::static_pointer_cast<rclcpp::Publisher<{rtype}>>(get_pub_ptr(pub));")
        lines.append(f"    {rtype} msg;")
        for fld in msg.fields:
            lines += gen_bridge_to_ros(fld, f"data.{fld.name}", f"msg.{fld.name}", all_msgs)
        lines.append(f"    typed_pub->publish(msg);")
        lines.append(f"}}")
        lines.append("")

        # create_subscription
        lines.append(f"std::shared_ptr<RclSubscriptionHandle> bridge_create_{ft}_subscription(")
        lines.append(f"        const std::shared_ptr<RclNodeHandle>& node, const std::string& topic, const BridgeQoS& qos,")
        lines.append(f"        std::function<void(const {sname}&)> callback) {{")
        lines.append(f"    auto *rqos = static_cast<rclcpp::QoS*>(make_rcl_qos(qos));")
        lines.append(f"    auto sub = get_rcl_node(node)->create_subscription<{rtype}>(")
        lines.append(f"        topic, *rqos,")
        lines.append(f"        [callback](const {rtype}::SharedPtr ros_msg) {{")
        lines.append(f"            {sname} data;")
        for fld in msg.fields:
            lines += gen_ros_to_bridge(fld, f"ros_msg->{fld.name}", f"data.{fld.name}", all_msgs, "            ")
        lines.append(f"            callback(data);")
        lines.append(f"        }});")
        lines.append(f"    delete_rcl_qos(rqos);")
        lines.append(f"    return make_sub_handle(sub);")
        lines.append(f"}}")
        lines.append("")

    lines += ["} // namespace ros2gd", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generate Godot message class
# ---------------------------------------------------------------------------

def gen_godot_to_bridge(fld: MsgField, godot_expr: str, bridge_expr: str,
                        all_msgs: Dict[str, MsgDef], indent: str = "    ") -> List[str]:
    """Generate code to convert from Godot field to bridge field."""
    lines = []
    if fld.is_primitive and not fld.is_array and not fld.is_fixed_array:
        if fld.base_type == "string":
            lines.append(f"{indent}{bridge_expr} = {godot_expr}.utf8().get_data();")
        else:
            lines.append(f"{indent}{bridge_expr} = {godot_expr};")
    elif fld.is_primitive and (fld.is_array or fld.is_fixed_array):
        if fld.base_type == "string":
            lines.append(f"{indent}for (int i = 0; i < {godot_expr}.size(); ++i)")
            lines.append(f"{indent}    {bridge_expr}.push_back({godot_expr}[i].utf8().get_data());")
        elif fld.is_fixed_array:
            lines.append(f"{indent}for (int i = 0; i < {godot_expr}.size() && i < {fld.array_size}; ++i)")
            lines.append(f"{indent}    {bridge_expr}[i] = {godot_expr}[i];")
        else:
            pt = PRIMITIVE_MAP.get(fld.base_type, ("int",))[0]
            lines.append(f"{indent}{bridge_expr}.assign({godot_expr}.ptr(), {godot_expr}.ptr() + {godot_expr}.size());")
    elif fld.is_native_mapped and not fld.is_array:
        needs_coord = NATIVE_TYPE_MAP[fld.base_type][1]
        if "Vector3" in fld.base_type or "Point" in fld.base_type:
            if needs_coord:
                lines.append(f"{indent}godot_to_ros({godot_expr}, {bridge_expr}.x, {bridge_expr}.y, {bridge_expr}.z);")
            else:
                lines.append(f"{indent}{bridge_expr}.x = {godot_expr}.x; {bridge_expr}.y = {godot_expr}.y; {bridge_expr}.z = {godot_expr}.z;")
        elif "Quaternion" in fld.base_type:
            if needs_coord:
                lines.append(f"{indent}godot_quat_to_ros({godot_expr}, {bridge_expr}.x, {bridge_expr}.y, {bridge_expr}.z, {bridge_expr}.w);")
            else:
                lines.append(f"{indent}{bridge_expr}.x = {godot_expr}.x; {bridge_expr}.y = {godot_expr}.y; {bridge_expr}.z = {godot_expr}.z; {bridge_expr}.w = {godot_expr}.w;")
    elif fld.base_type in all_msgs:
        sub_msg = all_msgs[fld.base_type]
        gname = godot_class_name(sub_msg)
        if fld.is_array:
            lines.append(f"{indent}{bridge_expr}.resize({godot_expr}.size());")
            lines.append(f"{indent}for (int i = 0; i < {godot_expr}.size(); ++i) {{")
            lines.append(f"{indent}    godot::Ref<{gname}> item = {godot_expr}[i];")
            lines.append(f"{indent}    if (item.is_valid()) {{")
            lines.append(f"{indent}        {bridge_expr}[i] = item->to_bridge();")
            lines.append(f"{indent}    }}")
            lines.append(f"{indent}}}")
        else:
            lines.append(f"{indent}if ({godot_expr}.is_valid())")
            lines.append(f"{indent}    {bridge_expr} = {godot_expr}->to_bridge();")
    return lines


def gen_bridge_to_godot(fld: MsgField, bridge_expr: str, godot_expr: str,
                        all_msgs: Dict[str, MsgDef], indent: str = "    ") -> List[str]:
    """Generate code to convert from bridge field to Godot field."""
    lines = []
    if fld.is_primitive and not fld.is_array and not fld.is_fixed_array:
        if fld.base_type == "string":
            lines.append(f"{indent}{godot_expr} = godot::String::utf8({bridge_expr}.c_str());")
        else:
            lines.append(f"{indent}{godot_expr} = {bridge_expr};")
    elif fld.is_primitive and (fld.is_array or fld.is_fixed_array):
        if fld.base_type == "string":
            gt = field_godot_type(fld, all_msgs)[0]
            lines.append(f"{indent}{godot_expr}.resize({bridge_expr}.size());")
            lines.append(f"{indent}for (size_t i = 0; i < {bridge_expr}.size(); ++i)")
            lines.append(f"{indent}    {godot_expr}.set(i, godot::String::utf8({bridge_expr}[i].c_str()));")
        elif fld.is_fixed_array:
            gt = field_godot_type(fld, all_msgs)[0]
            lines.append(f"{indent}{godot_expr}.resize({fld.array_size});")
            lines.append(f"{indent}for (int i = 0; i < {fld.array_size}; ++i)")
            lines.append(f"{indent}    {godot_expr}.set(i, {bridge_expr}[i]);")
        else:
            lines.append(f"{indent}{godot_expr}.resize({bridge_expr}.size());")
            lines.append(f"{indent}memcpy({godot_expr}.ptrw(), {bridge_expr}.data(), {bridge_expr}.size() * sizeof({bridge_expr}[0]));")
    elif fld.is_native_mapped and not fld.is_array:
        needs_coord = NATIVE_TYPE_MAP[fld.base_type][1]
        if "Vector3" in fld.base_type or "Point" in fld.base_type:
            if needs_coord:
                lines.append(f"{indent}{godot_expr} = ros_to_godot({bridge_expr}.x, {bridge_expr}.y, {bridge_expr}.z);")
            else:
                lines.append(f"{indent}{godot_expr} = godot::Vector3({bridge_expr}.x, {bridge_expr}.y, {bridge_expr}.z);")
        elif "Quaternion" in fld.base_type:
            if needs_coord:
                lines.append(f"{indent}{godot_expr} = ros_quat_to_godot({bridge_expr}.x, {bridge_expr}.y, {bridge_expr}.z, {bridge_expr}.w);")
            else:
                lines.append(f"{indent}{godot_expr} = godot::Quaternion({bridge_expr}.x, {bridge_expr}.y, {bridge_expr}.z, {bridge_expr}.w);")
    elif fld.base_type in all_msgs:
        sub_msg = all_msgs[fld.base_type]
        gname = godot_class_name(sub_msg)
        if fld.is_array:
            lines.append(f"{indent}{godot_expr}.resize({bridge_expr}.size());")
            lines.append(f"{indent}for (size_t i = 0; i < {bridge_expr}.size(); ++i) {{")
            lines.append(f"{indent}    godot::Ref<{gname}> item;")
            lines.append(f"{indent}    item.instantiate();")
            lines.append(f"{indent}    item->from_bridge({bridge_expr}[i]);")
            lines.append(f"{indent}    {godot_expr}.set(i, item);")
            lines.append(f"{indent}}}")
        else:
            lines.append(f"{indent}if ({godot_expr}.is_null()) {{ {godot_expr}.instantiate(); }}")
            lines.append(f"{indent}{godot_expr}->from_bridge({bridge_expr});")
    return lines


def gen_godot_class(msg: MsgDef, all_msgs: Dict[str, MsgDef]) -> Tuple[str, str]:
    """Generate header and source for a Godot message class."""
    gname = godot_class_name(msg)
    bname = bridge_struct_name(msg)
    guard = f"GEN_{msg.package.upper()}_{msg.name.upper()}_H"

    # Determine includes
    godot_includes = set()
    godot_includes.add('#include "ros_message.h"')
    godot_includes.add('#include <godot_cpp/core/class_db.hpp>')

    needs_coord_utils = False
    for fld in msg.fields:
        gt, _ = field_godot_type(fld, all_msgs)
        if "Vector3" in gt:
            godot_includes.add("#include <godot_cpp/variant/vector3.hpp>")
        if "Quaternion" in gt:
            godot_includes.add("#include <godot_cpp/variant/quaternion.hpp>")
        if "PackedByteArray" in gt:
            godot_includes.add("#include <godot_cpp/variant/packed_byte_array.hpp>")
        if "PackedFloat32Array" in gt:
            godot_includes.add("#include <godot_cpp/variant/packed_float32_array.hpp>")
        if "PackedFloat64Array" in gt:
            godot_includes.add("#include <godot_cpp/variant/packed_float64_array.hpp>")
        if "PackedInt32Array" in gt:
            godot_includes.add("#include <godot_cpp/variant/packed_int32_array.hpp>")
        if "PackedInt64Array" in gt:
            godot_includes.add("#include <godot_cpp/variant/packed_int64_array.hpp>")
        if "PackedStringArray" in gt:
            godot_includes.add("#include <godot_cpp/variant/packed_string_array.hpp>")
        if "TypedArray" in gt:
            godot_includes.add("#include <godot_cpp/variant/typed_array.hpp>")
        if "String" in gt and "Packed" not in gt:
            godot_includes.add("#include <godot_cpp/variant/string.hpp>")
        if fld.is_native_mapped and NATIVE_TYPE_MAP[fld.base_type][1]:
            needs_coord_utils = True

    # Determine which sub-message headers to include
    sub_includes = set()
    for fld in msg.fields:
        if not fld.is_primitive and fld.base_type in all_msgs:
            # Include if: non-native, OR native-mapped but used as array (needs the class)
            if not fld.is_native_mapped or fld.is_array:
                dep = all_msgs[fld.base_type]
                sub_includes.add(f'#include "{file_base(dep)}.h"')

    # ---- HEADER ----
    h_lines = [
        f"// AUTO-GENERATED by generate_msgs.py — do not edit",
        f"#ifndef {guard}",
        f"#define {guard}",
        "",
    ]
    h_lines += sorted(godot_includes)
    h_lines.append("")
    if sub_includes:
        h_lines += sorted(sub_includes)
        h_lines.append("")
    h_lines += [
        f"namespace ros2gd {{",
        f"struct {bname};",
        "",
        f"class {gname} : public RosMessage {{",
        f"    GDCLASS({gname}, RosMessage)",
        "",
        "private:",
    ]

    # Member variables
    for fld in msg.fields:
        gt, _ = field_godot_type(fld, all_msgs)
        default = field_default_expr(fld, gt)
        if "Ref<" in gt:
            h_lines.append(f"    {gt} {fld.name}_;")
        elif default:
            h_lines.append(f"    {gt} {fld.name}_{{{default}}};")
        else:
            h_lines.append(f"    {gt} {fld.name}_;")

    h_lines += [
        "",
        "protected:",
        "    static void _bind_methods();",
        "",
        "public:",
        f"    {gname}() = default;",
        f"    ~{gname}() = default;",
        "",
        f'    godot::String get_type_name() const {{ return "{msg.full_type}"; }}',
        "",
    ]

    # Getters/setters
    for fld in msg.fields:
        gt, _ = field_godot_type(fld, all_msgs)
        is_ref = gt.startswith("godot::Ref<") or gt.startswith("godot::TypedArray<")
        param_type = f"const {gt}&" if is_ref or "String" in gt or "Packed" in gt or "Array" in gt else gt
        h_lines.append(f"    void set_{fld.name}({param_type} v) {{ {fld.name}_ = v; }}")
        ret_type = gt
        h_lines.append(f"    {ret_type} get_{fld.name}() const {{ return {fld.name}_; }}")
        h_lines.append("")

    # to_bridge / from_bridge
    h_lines.append(f"    {bname} to_bridge() const;")
    h_lines.append(f"    void from_bridge(const {bname}& data);")
    h_lines += [
        "};",
        "",
        "} // namespace ros2gd",
        "",
        f"#endif // {guard}",
        "",
    ]

    # ---- SOURCE ----
    cpp_lines = [
        f"// AUTO-GENERATED by generate_msgs.py — do not edit",
        f'#include "{file_base(msg)}.h"',
        f'#include "bridge_msgs.h"',
    ]
    if needs_coord_utils:
        cpp_lines.append('#include "coord_utils.h"')
    cpp_lines += [
        "",
        "using namespace godot;",
        "",
        "namespace ros2gd {",
        "",
        f"void {gname}::_bind_methods() {{",
    ]

    for fld in msg.fields:
        gt, vtype = field_godot_type(fld, all_msgs)
        cpp_lines.append(f'    ClassDB::bind_method(D_METHOD("set_{fld.name}", "{fld.name}"), &{gname}::set_{fld.name});')
        cpp_lines.append(f'    ClassDB::bind_method(D_METHOD("get_{fld.name}"), &{gname}::get_{fld.name});')
        cpp_lines.append(f'    ADD_PROPERTY(PropertyInfo(Variant::{vtype}, "{fld.name}"), "set_{fld.name}", "get_{fld.name}");')

    cpp_lines.append(f'    ClassDB::bind_method(D_METHOD("get_type_name"), &{gname}::get_type_name);')
    cpp_lines += ["}", ""]

    # to_bridge
    cpp_lines.append(f"{bname} {gname}::to_bridge() const {{")
    cpp_lines.append(f"    {bname} data;")
    for fld in msg.fields:
        cpp_lines += gen_godot_to_bridge(fld, f"{fld.name}_", f"data.{fld.name}", all_msgs)
    cpp_lines.append(f"    return data;")
    cpp_lines += ["}", ""]

    # from_bridge
    cpp_lines.append(f"void {gname}::from_bridge(const {bname}& data) {{")
    for fld in msg.fields:
        cpp_lines += gen_bridge_to_godot(fld, f"data.{fld.name}", f"{fld.name}_", all_msgs)
    cpp_lines += ["}", ""]

    cpp_lines += ["} // namespace ros2gd", ""]
    return "\n".join(h_lines), "\n".join(cpp_lines)


# ---------------------------------------------------------------------------
# Generate factory dispatch (msg_factory.h / msg_factory.cpp)
# ---------------------------------------------------------------------------

def gen_factory(msgs: List[MsgDef], all_msgs: Dict[str, MsgDef]) -> Tuple[str, str]:
    """Generate msg_factory.h/cpp that dispatches type_name → bridge functions."""

    # Header
    h_lines = [
        "// AUTO-GENERATED by generate_msgs.py — do not edit",
        "#ifndef MSG_FACTORY_H",
        "#define MSG_FACTORY_H",
        "",
        '#include "ros_bridge.h"',
        '#include "ros_publisher.h"',
        '#include "ros_subscription.h"',
        '#include "ros_message.h"',
        "",
        "#include <godot_cpp/variant/callable.hpp>",
        "#include <godot_cpp/variant/string.hpp>",
        "",
        "namespace ros2gd {",
        "",
        "godot::Ref<RosPublisher> factory_create_publisher(",
        "    const std::shared_ptr<RclNodeHandle>& node,",
        "    const godot::String& type_name,",
        "    const godot::String& topic, const BridgeQoS& qos);",
        "",
        "godot::Ref<RosSubscription> factory_create_subscription(",
        "    const std::shared_ptr<RclNodeHandle>& node,",
        "    const godot::String& type_name,",
        "    const godot::String& topic, const godot::Callable& callback, const BridgeQoS& qos,",
        "    std::shared_ptr<RclSubscriptionHandle>& out_handle);",
        "",
        "godot::Ref<RosMessage> factory_create_message(const godot::String& type_name);",
        "",
        "} // namespace ros2gd",
        "",
        "#endif // MSG_FACTORY_H",
        "",
    ]

    # Source
    cpp_lines = [
        "// AUTO-GENERATED by generate_msgs.py — do not edit",
        '#include "msg_factory.h"',
        '#include "bridge_msgs.h"',
        '#include "coord_utils.h"',
        "",
        "#include <godot_cpp/variant/utility_functions.hpp>",
        "#include <godot_cpp/core/object.hpp>",
        "",
    ]

    # Include all generated message headers
    for msg in msgs:
        cpp_lines.append(f'#include "{file_base(msg)}.h"')
    cpp_lines += [
        "",
        "using namespace godot;",
        "",
        "namespace ros2gd {",
        "",
    ]

    # create_publisher
    cpp_lines += [
        "Ref<RosPublisher> factory_create_publisher(",
        "        const std::shared_ptr<RclNodeHandle>& node,",
        "        const String& type_name,",
        "        const String& topic, const BridgeQoS& qos) {",
        "    std::string topic_str = topic.utf8().get_data();",
        "",
        "    Ref<RosPublisher> pub;",
        "    pub.instantiate();",
        "",
    ]

    first = True
    for msg in msgs:
        gname = godot_class_name(msg)
        bname = bridge_struct_name(msg)
        ft = msg.full_type.replace("/", "_")
        cond = "if" if first else "} else if"
        first = False

        cpp_lines.append(f'    {cond} (type_name == "{msg.full_type}") {{')
        cpp_lines.append(f'        auto pub_handle = bridge_create_{ft}_publisher(node, topic_str, qos);')
        cpp_lines.append(f'        pub->setup(pub_handle,')
        cpp_lines.append(f'            [pub_handle](const Ref<RosMessage>& msg) {{')
        cpp_lines.append(f'                auto typed = Object::cast_to<{gname}>(msg.ptr());')
        cpp_lines.append(f'                if (typed) bridge_publish_{ft}(pub_handle, typed->to_bridge());')
        cpp_lines.append(f'            }}, topic, type_name);')

    cpp_lines += [
        "    } else {",
        '        UtilityFunctions::printerr("[ros2gd] Unsupported message type: ", type_name);',
        "        return Ref<RosPublisher>();",
        "    }",
        "",
        "    return pub;",
        "}",
        "",
    ]

    # create_subscription
    cpp_lines += [
        "Ref<RosSubscription> factory_create_subscription(",
        "        const std::shared_ptr<RclNodeHandle>& node,",
        "        const String& type_name,",
        "        const String& topic, const Callable& callback, const BridgeQoS& qos,",
        "        std::shared_ptr<RclSubscriptionHandle>& out_handle) {",
        "    std::string topic_str = topic.utf8().get_data();",
        "",
        "    Ref<RosSubscription> sub;",
        "    sub.instantiate();",
        "",
    ]

    first = True
    for msg in msgs:
        gname = godot_class_name(msg)
        bname = bridge_struct_name(msg)
        ft = msg.full_type.replace("/", "_")
        cond = "if" if first else "} else if"
        first = False

        cpp_lines.append(f'    {cond} (type_name == "{msg.full_type}") {{')
        cpp_lines.append(f'        out_handle = bridge_create_{ft}_subscription(')
        cpp_lines.append(f'            node, topic_str, qos,')
        cpp_lines.append(f'            [callback](const {bname}& data) {{')
        cpp_lines.append(f'                Ref<{gname}> godot_msg;')
        cpp_lines.append(f'                godot_msg.instantiate();')
        cpp_lines.append(f'                godot_msg->from_bridge(data);')
        cpp_lines.append(f'                callback.call(godot_msg);')
        cpp_lines.append(f'            }});')

    cpp_lines += [
        "    } else {",
        '        UtilityFunctions::printerr("[ros2gd] Unsupported message type: ", type_name);',
        "        return Ref<RosSubscription>();",
        "    }",
        "",
        "    sub->setup(out_handle, topic, type_name);",
        "    return sub;",
        "}",
        "",
    ]

    # factory_create_message
    cpp_lines += [
        "Ref<RosMessage> factory_create_message(const String& type_name) {",
        "",
    ]
    first = True
    for msg in msgs:
        gname = godot_class_name(msg)
        cond = "if" if first else "} else if"
        first = False
        cpp_lines.append(f'    {cond} (type_name == "{msg.full_type}") {{')
        cpp_lines.append(f'        Ref<{gname}> m;')
        cpp_lines.append(f'        m.instantiate();')
        cpp_lines.append(f'        return m;')
    cpp_lines += [
        "    } else {",
        '        UtilityFunctions::printerr("[ros2gd] Unknown message type: ", type_name);',
        "        return Ref<RosMessage>();",
        "    }",
        "}",
        "",
        "} // namespace ros2gd",
        "",
    ]

    return "\n".join(h_lines), "\n".join(cpp_lines)


# ---------------------------------------------------------------------------
# Generate register_all_msgs.h
# ---------------------------------------------------------------------------

def gen_register(msgs: List[MsgDef]) -> str:
    lines = [
        "// AUTO-GENERATED by generate_msgs.py — do not edit",
        "#ifndef REGISTER_ALL_MSGS_H",
        "#define REGISTER_ALL_MSGS_H",
        "",
        "#include <godot_cpp/core/class_db.hpp>",
        "",
    ]
    for msg in msgs:
        lines.append(f'#include "{file_base(msg)}.h"')
    lines += [
        "",
        "inline void register_all_generated_msgs() {",
    ]
    for msg in msgs:
        gname = godot_class_name(msg)
        lines.append(f"    godot::ClassDB::register_class<ros2gd::{gname}>();")
    lines += [
        "}",
        "",
        "#endif // REGISTER_ALL_MSGS_H",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generate CMake include (gen_sources.cmake)
# ---------------------------------------------------------------------------

def gen_cmake(msgs: List[MsgDef], packages_used: set) -> str:
    lines = [
        "# AUTO-GENERATED by generate_msgs.py — do not edit",
        "# GEN_DIR must be set before including this file",
        "",
        "set(GEN_GODOT_SOURCES",
    ]
    for msg in msgs:
        lines.append(f"    ${{GEN_DIR}}/{file_base(msg)}.cpp")
    lines.append(f"    ${{GEN_DIR}}/msg_factory.cpp")
    lines += [")", ""]

    lines.append("set(GEN_BRIDGE_SOURCES")
    for pkg in sorted(packages_used):
        lines.append(f"    ${{GEN_DIR}}/bridge_{pkg}.cpp")
    lines += [")", ""]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate GDExtension message classes from .msg files")
    parser.add_argument("--ros-dir", default="/opt/ros/humble", help="ROS2 install directory")
    parser.add_argument("--packages", nargs="+",
                        default=["std_msgs", "geometry_msgs", "sensor_msgs", "nav_msgs", "tf2_msgs"],
                        help="ROS2 packages to generate")
    parser.add_argument("--out-dir", default="gen", help="Output directory")
    parser.add_argument("--msgs", nargs="*", default=None,
                        help="Specific messages to generate (e.g. Twist Image). Default: all")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Parse all .msg files
    all_msgs = discover_msgs(args.ros_dir, args.packages + ["builtin_interfaces"])

    # Filter to requested messages if specified
    if args.msgs:
        requested = set(args.msgs)
        # Find matching messages and their dependencies
        selected = set()

        def add_with_deps(ft):
            if ft in selected or ft not in all_msgs:
                return
            selected.add(ft)
            for fld in all_msgs[ft].fields:
                if not fld.is_primitive and fld.base_type in all_msgs:
                    add_with_deps(fld.base_type)

        for ft, msg in all_msgs.items():
            if msg.name in requested:
                add_with_deps(ft)

        all_msgs = {ft: msg for ft, msg in all_msgs.items() if ft in selected}

    # Topological sort
    sorted_msgs = topo_sort(all_msgs)

    print(f"Generating {len(sorted_msgs)} message types:")
    for msg in sorted_msgs:
        print(f"  {msg.full_type} ({len(msg.fields)} fields)")

    # Generate bridge header
    with open(out_dir / "bridge_msgs.h", "w") as f:
        f.write(gen_bridge_header(sorted_msgs, all_msgs))

    # Generate bridge implementation per package
    packages_used = set()
    by_package: Dict[str, List[MsgDef]] = {}
    for msg in sorted_msgs:
        by_package.setdefault(msg.package, []).append(msg)
        packages_used.add(msg.package)

    for pkg, pkg_msgs in by_package.items():
        with open(out_dir / f"bridge_{pkg}.cpp", "w") as f:
            f.write(gen_bridge_impl(pkg, pkg_msgs, all_msgs))

    # Generate Godot classes
    for msg in sorted_msgs:
        h_code, cpp_code = gen_godot_class(msg, all_msgs)
        fname = file_base(msg)
        with open(out_dir / f"{fname}.h", "w") as f:
            f.write(h_code)
        with open(out_dir / f"{fname}.cpp", "w") as f:
            f.write(cpp_code)

    # Generate factory
    fh, fc = gen_factory(sorted_msgs, all_msgs)
    with open(out_dir / "msg_factory.h", "w") as f:
        f.write(fh)
    with open(out_dir / "msg_factory.cpp", "w") as f:
        f.write(fc)

    # Generate registration header
    with open(out_dir / "register_all_msgs.h", "w") as f:
        f.write(gen_register(sorted_msgs))

    # Generate CMake include
    with open(out_dir / "gen_sources.cmake", "w") as f:
        f.write(gen_cmake(sorted_msgs, packages_used))

    print(f"\nGenerated files in {out_dir}/")


if __name__ == "__main__":
    main()
