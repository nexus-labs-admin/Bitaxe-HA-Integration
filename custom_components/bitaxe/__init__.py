from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

DOMAIN = "bitaxe"
_LOGGER = logging.getLogger(__name__)
_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)


async def async_setup_entry(
    hass: HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    ip_address = entry.data["ip_address"]
    device_id = entry.unique_id or ip_address
    session = async_get_clientsession(hass)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"BitAxe Sensor Data ({device_id})",
        update_method=lambda: fetch_bitaxe_data(session, ip_address),
        update_interval=timedelta(seconds=30),
    )

    await coordinator.async_refresh()

    hass.data.setdefault(DOMAIN, {})[device_id] = {"coordinator": coordinator}
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True


async def fetch_bitaxe_data(
    session: aiohttp.ClientSession, ip_address: str
) -> dict[str, Any]:
    url = f"http://{ip_address}/api/system/info"
    try:
        async with session.get(url, timeout=_REQUEST_TIMEOUT) as response:
            response.raise_for_status()
            data = await response.json()
    except (TimeoutError, aiohttp.ClientError, ValueError) as error:
        detail = str(error) or type(error).__name__
        raise UpdateFailed(f"Error fetching data from BitAxe API: {detail}") from error

    if not isinstance(data, dict):
        raise UpdateFailed("BitAxe API response was not a JSON object")

    _LOGGER.debug("Fetched data: %s", data)
    return data
