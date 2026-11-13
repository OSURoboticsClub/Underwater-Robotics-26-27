#!/usr/bin/env python3
"""
Collect all ROS2 shared library dependencies needed for standalone deployment.

Recursively resolves ldd dependencies, copies .so files from the ROS2 install
directory (and its subdirectories) into the output directory.

Usage:
    python3 collect_libs.py <main_library> <ros2_install_dir> <output_dir>
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def get_ldd_deps(lib_path: str) -> list[str]:
    """Get resolved library paths from ldd output."""
    try:
        out = subprocess.check_output(
            ["ldd", lib_path], text=True, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        return []

    deps = []
    for line in out.splitlines():
        m = re.search(r"=>\s+(/\S+)", line)
        if m:
            deps.append(m.group(1))
    return deps


def find_all_ros2_deps(
    start_lib: str, ros2_dir: str, visited: set[str] | None = None
) -> set[str]:
    """Recursively find all .so dependencies that live under ros2_dir."""
    if visited is None:
        visited = set()

    real = os.path.realpath(start_lib)
    if real in visited:
        return set()
    visited.add(real)

    result = set()
    for dep in get_ldd_deps(start_lib):
        dep_real = os.path.realpath(dep)
        if dep_real.startswith(os.path.realpath(ros2_dir)):
            result.add(dep_real)
            # Also add the symlink name if different
            if dep != dep_real:
                result.add(dep)
            result |= find_all_ros2_deps(dep_real, ros2_dir, visited)

    return result


def find_rmw_plugins(ros2_dir: str) -> list[str]:
    """Find RMW implementation plugins that are dlopen'd at runtime."""
    plugins = []
    lib_dirs = [
        os.path.join(ros2_dir, "lib"),
        os.path.join(ros2_dir, "lib", "x86_64-linux-gnu"),
    ]
    patterns = [
        "librmw_cyclonedds_cpp.so",
        "librmw_fastrtps_cpp.so",
        "librosidl_typesupport_fastrtps_cpp.so",
        "librosidl_typesupport_fastrtps_c.so",
        "librosidl_typesupport_introspection_cpp.so",
        "librosidl_typesupport_introspection_c.so",
    ]
    for lib_dir in lib_dirs:
        if not os.path.isdir(lib_dir):
            continue
        for pat in patterns:
            full = os.path.join(lib_dir, pat)
            if os.path.exists(full):
                plugins.append(full)
    return plugins


def find_typesupport_libs(ros2_dir: str, msg_packages: list[str]) -> list[str]:
    """Find all rosidl typesupport .so for the given message packages.

    These are dlopen'd at runtime by rosidl_typesupport_c/cpp.
    """
    libs = []
    lib_dir = os.path.join(ros2_dir, "lib")
    if not os.path.isdir(lib_dir):
        return libs
    for pkg in msg_packages:
        for f in os.listdir(lib_dir):
            if f.startswith(f"lib{pkg}__rosidl_") and f.endswith(".so"):
                libs.append(os.path.join(lib_dir, f))
    return libs


def copy_lib(src: str, dst_dir: str, copied: set[str]) -> None:
    """Copy a library and its symlink chain to dst_dir."""
    basename = os.path.basename(src)
    if basename in copied:
        return

    real = os.path.realpath(src)
    real_basename = os.path.basename(real)

    # Copy the real file
    if real_basename not in copied:
        dst = os.path.join(dst_dir, real_basename)
        if not os.path.exists(dst):
            shutil.copy2(real, dst)
        copied.add(real_basename)

    # Create symlink if name differs
    if basename != real_basename:
        link_path = os.path.join(dst_dir, basename)
        if not os.path.exists(link_path):
            os.symlink(real_basename, link_path)
        copied.add(basename)


def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <main_lib> <ros2_install_dir> <output_dir>")
        sys.exit(1)

    main_lib = sys.argv[1]
    ros2_dir = sys.argv[2]
    out_dir = sys.argv[3]

    os.makedirs(out_dir, exist_ok=True)

    msg_packages = [
        "std_msgs",
        "builtin_interfaces",
        "geometry_msgs",
        "sensor_msgs",
        "nav_msgs",
        "tf2_msgs",
        "action_msgs",
        "unique_identifier_msgs",
        "rcl_interfaces",
        "rosgraph_msgs",
        "statistics_msgs",
        "rmw_dds_common",
    ]

    # 1. Direct + transitive ldd deps
    print(f"  Resolving dependencies of {os.path.basename(main_lib)}...")
    all_deps = find_all_ros2_deps(main_lib, ros2_dir)

    # 2. RMW plugins (dlopen'd, not in ldd)
    print("  Finding RMW plugins...")
    for plugin in find_rmw_plugins(ros2_dir):
        all_deps.add(plugin)
        all_deps |= find_all_ros2_deps(plugin, ros2_dir)

    # 3. Message typesupport libs (dlopen'd by rosidl)
    print("  Finding message typesupport libraries...")
    for lib in find_typesupport_libs(ros2_dir, msg_packages):
        all_deps.add(lib)
        all_deps |= find_all_ros2_deps(lib, ros2_dir)

    # 4. Copy everything
    copied: set[str] = set()
    for dep in sorted(all_deps):
        copy_lib(dep, out_dir, copied)

    print(f"  Collected {len(copied)} files into {out_dir}")


if __name__ == "__main__":
    main()
