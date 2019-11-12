"""Support for the Xiaomi vacuum cleaner robot."""
import asyncio
from functools import partial
import logging

from miio import DeviceException, Vacuum  # pylint: disable=import-error
import voluptuous as vol

from homeassistant.components.vacuum import (
    ATTR_CLEANED_AREA,
    DOMAIN,
    PLATFORM_SCHEMA,
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RETURNING,
    SUPPORT_BATTERY,
    SUPPORT_FAN_SPEED,
    SUPPORT_LOCATE,
    SUPPORT_PAUSE,
    SUPPORT_RETURN_HOME,
    SUPPORT_SEND_COMMAND,
    SUPPORT_START,
    SUPPORT_STATE,
    SUPPORT_STOP,
    StateVacuumDevice,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_TOKEN,
    STATE_OFF,
    STATE_ON,
)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Xiaomi Vacuum cleaner STYJ02YM"
DATA_KEY = "vacuum.miio2"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): vol.All(str, vol.Length(min=32, max=32)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    },
    extra=vol.ALLOW_EXTRA,
)

FAN_SPEEDS = {"Silent": 0, "Standard": 1, "Medium": 2, "Turbo": 3}

VACUUM_SERVICE_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTITY_ID): cv.comp_entity_ids})

SUPPORT_XIAOMI = (
    SUPPORT_STATE |
    SUPPORT_PAUSE |
    SUPPORT_STOP |
    SUPPORT_RETURN_HOME |
    SUPPORT_FAN_SPEED |
    SUPPORT_LOCATE |
    SUPPORT_SEND_COMMAND |
    SUPPORT_BATTERY |
    SUPPORT_START
)


STATE_CODE_TO_STATE = {
    1: STATE_IDLE,
    2: STATE_IDLE,
    3: STATE_CLEANING,
    4: STATE_RETURNING,
    5: STATE_DOCKED,
}

ALL_PROPS = ["run_state", "mode", "err_state", "battary_life", "box_type", "mop_type", "s_time",
             "s_area", "suction_grade", "water_grade", "remember_map", "has_map", "is_mop", "has_newmap"]


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
  """Set up the Xiaomi vacuum cleaner robot platform."""
  if DATA_KEY not in hass.data:
    hass.data[DATA_KEY] = {}

  host = config[CONF_HOST]
  token = config[CONF_TOKEN]
  name = config[CONF_NAME]

  # Create handler
  _LOGGER.info("Initializing with host %s (token %s...)", host, token[:5])
  vacuum = Vacuum(host, token)

  mirobo = MiroboVacuum2(name, vacuum)
  hass.data[DATA_KEY][host] = mirobo

  async_add_entities([mirobo], update_before_add=True)


class MiroboVacuum2(StateVacuumDevice):
  """Representation of a Xiaomi Vacuum cleaner robot."""

  def __init__(self, name, vacuum):
    """Initialize the Xiaomi vacuum cleaner robot handler."""
    self._name = name
    self._vacuum = vacuum

    self.vacuum_state = None
    self._available = False

  @property
  def name(self):
    """Return the name of the device."""
    return self._name

  @property
  def state(self):
    """Return the status of the vacuum cleaner."""
    if self.vacuum_state is not None:
      # The vacuum reverts back to an idle state after erroring out.
      # We want to keep returning an error until it has been cleared.

      try:
        return STATE_CODE_TO_STATE[int(self.vacuum_state['run_state'])]
      except KeyError:
        _LOGGER.error(
            "STATE not supported, state_code: %s",
            self.vacuum_state['run_state'],
        )
        return None

  @property
  def battery_level(self):
    """Return the battery level of the vacuum cleaner."""
    if self.vacuum_state is not None:
      return self.vacuum_state['battary_life']

  @property
  def fan_speed(self):
    """Return the fan speed of the vacuum cleaner."""
    if self.vacuum_state is not None:
      speed = self.vacuum_state['suction_grade']
      if speed in FAN_SPEEDS.values():
        return [key for key, value in FAN_SPEEDS.items() if value == speed][0]
      return speed

  @property
  def fan_speed_list(self):
    """Get the list of available fan speed steps of the vacuum cleaner."""
    return list(sorted(FAN_SPEEDS.keys(), key=lambda s: FAN_SPEEDS[s]))

  @property
  def device_state_attributes(self):
    """Return the specific state attributes of this vacuum cleaner."""
    attrs = {}
    if self.vacuum_state is not None:
      attrs.update(self.vacuum_state)
      try:
        attrs['status'] = STATE_CODE_TO_STATE[int(self.vacuum_state['run_state'])]
      except KeyError:
        return "Definition missing for state %s" % self.vacuum_state['run_state']
    return attrs

  @property
  def available(self) -> bool:
    """Return True if entity is available."""
    return self._available

  @property
  def supported_features(self):
    """Flag vacuum cleaner robot features that are supported."""
    return SUPPORT_XIAOMI

  async def _try_command(self, mask_error, func, *args, **kwargs):
    """Call a vacuum command handling error messages."""
    try:
      await self.hass.async_add_executor_job(partial(func, *args, **kwargs))
      return True
    except DeviceException as exc:
      _LOGGER.error(mask_error, exc)
      return False

  async def async_start(self):
    """Start or resume the cleaning task."""
    await self._try_command(
        "Unable to start the vacuum: %s", self._vacuum.raw_command, 'set_mode_withroom', [
            0, 1, 0]
    )

  async def async_pause(self):
    """Pause the cleaning task."""
    await self._try_command("Unable to set start/pause: %s", self._vacuum.raw_command, 'set_mode_withroom', [0, 2, 0])

  async def async_stop(self, **kwargs):
    """Stop the vacuum cleaner."""
    await self._try_command("Unable to stop: %s", self._vacuum.raw_command, 'set_mode', [0])

  async def async_set_fan_speed(self, fan_speed, **kwargs):
    """Set fan speed."""
    if fan_speed.capitalize() in FAN_SPEEDS:
      fan_speed = FAN_SPEEDS[fan_speed.capitalize()]
    else:
      try:
        fan_speed = int(fan_speed)
      except ValueError as exc:
        _LOGGER.error(
            "Fan speed step not recognized (%s). " "Valid speeds are: %s",
            exc,
            self.fan_speed_list,
        )
        return
    await self._try_command(
        "Unable to set fan speed: %s", self._vacuum.raw_command, 'set_suction', [fan_speed]
    )

  async def async_return_to_base(self, **kwargs):
    """Set the vacuum cleaner to return to the dock."""
    await self._try_command("Unable to return home: %s", self._vacuum.raw_command, 'set_charge', [1])

  async def async_locate(self, **kwargs):
    """Locate the vacuum cleaner."""
    await self._try_command("Unable to locate the botvac: %s", self._vacuum.raw_command, 'set_resetpos', [1])

  async def async_send_command(self, command, params=None, **kwargs):
    """Send raw command."""
    await self._try_command(
        "Unable to send command to the vacuum: %s",
        self._vacuum.raw_command,
        command,
        params,
    )

  def update(self):
    """Fetch state from the device."""
    try:
      state = self._vacuum.raw_command('get_prop', ALL_PROPS)

      self.vacuum_state = dict(zip(ALL_PROPS, state))

      self._available = True
    except OSError as exc:
      _LOGGER.error("Got OSError while fetching the state: %s", exc)
    except DeviceException as exc:
      _LOGGER.warning("Got exception while fetching the state: %s", exc)
