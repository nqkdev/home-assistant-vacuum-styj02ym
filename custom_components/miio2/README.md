# Hacky Home assistant support for Xiaomi vacuum STYJ02YM

_Original code by [@nqkdev](https://github.com/nqkdev/home-assistant-vacuum-styj02ym), then I forked it and added HACS support._  
_Next steps were checking forks of original repository and backporting changes in order to provide most feature-complete Home Assistant integration for STYJ02YM._

## This is for STYJ02YM (apparently EU version) with 3.5.3_0017 firmware

### Install

- Install it with HACS
- Add the configuration to configuration.yaml, example:

### Usage

Add to `configuration.yaml`:

```yaml
vacuum:
  - platform: miio2
    host: 192.168.68.105
    token: !secret vacuum
    name: Mi hihi
```
