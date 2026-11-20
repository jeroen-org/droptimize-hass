"""Config flow for the Droptimize integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DroptimizeApi, DroptimizeAuthError, DroptimizeError
from .const import (
    BASE_URL,
    CONF_REGISTRATION_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LOGGER,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_REGISTRATION_ID): str,
    }
)


async def _validate_input(hass: HomeAssistant, user_input: dict[str, Any]) -> dict[str, Any]:
    """Validate the registration id by exchanging it for a token.

    Returns a dict with ``title`` and ``unique_id`` on success.
    Raises DroptimizeAuthError / DroptimizeError on failure.
    """
    api = DroptimizeApi(
        async_get_clientsession(hass),
        BASE_URL,
        user_input[CONF_REGISTRATION_ID],
    )
    await api.exchange_token()

    claims = api.claims
    sensor_id = claims.get("id")
    registration_id = str(user_input[CONF_REGISTRATION_ID])

    if sensor_id is None:
        raise DroptimizeAuthError("Geen sensor id in token claims")

    return {
        "title": f"Droptimize {registration_id}",
        "unique_id": str(sensor_id),
    }


class DroptimizeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Droptimize."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await _validate_input(self.hass, user_input)
            except DroptimizeAuthError:
                errors["base"] = "invalid_auth"
            except DroptimizeError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected error validating registration id")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info["unique_id"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=info["title"],
                    data={CONF_REGISTRATION_ID: user_input[CONF_REGISTRATION_ID]},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Handle a re-authentication request."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm re-authentication with a new registration id."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()

        if user_input is not None:
            try:
                info = await _validate_input(self.hass, user_input)
            except DroptimizeAuthError:
                errors["base"] = "invalid_auth"
            except DroptimizeError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected error validating registration id")
                errors["base"] = "unknown"
            else:
                if info["unique_id"] != entry.unique_id:
                    errors["base"] = "wrong_account"
                else:
                    return self.async_update_reload_and_abort(
                        entry,
                        data={CONF_REGISTRATION_ID: user_input[CONF_REGISTRATION_ID]},
                    )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={"sensor_id": entry.unique_id},
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> DroptimizeOptionsFlow:
        """Return the options flow."""
        return DroptimizeOptionsFlow(entry)


class DroptimizeOptionsFlow(OptionsFlow):
    """Handle options."""

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        if hasattr(current, "total_seconds"):
            current = int(current.total_seconds())

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=current,
                    ): vol.All(vol.Coerce(int), vol.Range(min=300, max=86400))
                }
            ),
        )