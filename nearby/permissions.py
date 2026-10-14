DEFAULT_PERMISSIONS = {
    "device_info": True,
    "battery": True,
    "network_status": True,
    "send_notification": False,
    "send_files": False,
    "receive_files": False,
    "location": False,
    "contacts": False,
    "messages": False,
    "photos": False,
}


class PermissionManager:

    def __init__(self):

        self.permissions = {}

    def create_permissions(self, device_id):

        self.permissions[device_id] = (
            DEFAULT_PERMISSIONS.copy()
        )

        return self.permissions[device_id]

    def set_permission(
        self,
        device_id,
        permission,
        allowed,
    ):

        if device_id not in self.permissions:
            self.create_permissions(device_id)

        if permission not in DEFAULT_PERMISSIONS:
            return False

        self.permissions[device_id][permission] = bool(
            allowed
        )

        return True

    def allowed(
        self,
        device_id,
        permission,
    ):

        return self.permissions.get(
            device_id,
            {},
        ).get(permission, False)

    def get_permissions(self, device_id):

        return self.permissions.get(
            device_id,
            DEFAULT_PERMISSIONS.copy(),
        )