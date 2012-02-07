# -*- coding: utf-8 -*-

## SystemD itself

# DBus service name
service_name = 'org.freedesktop.systemd1'

# DBus paths
_root_path = "/org/freedesktop/systemd1"
manager_path = _root_path
unit_root = _root_path + "/unit"

# DBus interfaces
_interface_root = "org.freedesktop.systemd1"
manager_interface = _interface_root + ".Manager"
unit_interface = _interface_root + ".Unit"
service_interface = _interface_root + ".Service"

## PolicyKit enabled mechanism for privileged operations

# DBus service name
polkit_service_name = 'org.fedoraproject.Config.Services'

# DBus paths
_polkit_root_path = "/org/fedoraproject/Config/Services/systemd1"
polkit_manager_path = _polkit_root_path
# the polkit-enabled mechanism supports (a reasonable subset of) the interfaces
# of SystemD itself, so we just abuse the original interface names for them

properties_interface = 'org.freedesktop.DBus.Properties'
