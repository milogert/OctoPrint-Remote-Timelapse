#!/usr/bin/env python

import octoprint
import subprocess


class RemoteTimelapsePlugin(
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.EventHandlerPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.RestartNeedingPlugin,
):
    def get_settings_defaults(self):
        return dict(api_token=None, delete_after_upload=False)

    def get_settings_restricted_paths(self):
        return dict(admin=[["api_token"]])

    def get_template_configs(self):
        return [
            dict(
                type="settings",
                custom_bindings=False,
                template="remote_timelapse_settings.jinja2",
            )
        ]

    def get_update_information(self):
        return dict(
            remote_timelapse=dict(
                displayName="Remote Timelapse Plugin",
                displayVersion=self._plugin_version,
                # version check: github repository
                type="github_release",
                user="milogert",
                repo="OctoPrint-Remote-Timelapse",
                current=self._plugin_version,
                # update method: pip
                pip="https://github.com/milogert/OctoPrint-Remote-Timelapse/archive/{target_version}.zip",
            )
        )

    @property
    def user(self):
        return self._settings.get(["user"])

    @property
    def password(self):
        return self._settings.get(["password"])

    @property
    def host(self):
        return self._settings.get(["host"])

    @property
    def path(self):
        return self._settings.get(["path"])

    @property
    def delete_after_upload(self):
        return self._settings.get_boolean(["delete_after_upload"])

    def on_event(self, event, payload):
        from octoprint.events import Events

        if event == Events.MOVIE_DONE:
            self.upload_timelapse(payload)

    def upload_timelapse(self, payload):
        path = payload["movie"]
        file_name = payload["movie_basename"]
        if self.user and self.password and self.host and self.path:
            try:
                result = subprocess.run(
                    args=[
                        "scp",
                        f"{self.user}:{self.password}@{self.host}:{self.path}",
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError:
                self._logger.info(
                    "Failed to run command: `{self.user}:REDACTED@{self.host}:{self.path}`"
                )
                return
        else:
            self._logger.info(
                "Make sure that your user, password, host, and path are defined."
            )
            return

        if self.delete_after_upload:
            import os

            self._logger.info("Deleting %s from local disk..." % file_name)
            os.remove(path)
            self._logger.info("Deleted %s from local disk." % file_name)


__plugin_name__ = "Remote Timelapse Plugin"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = RemoteTimelapsePlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
