# Hacky Home assistant support for Xiaomi vacuum STYJ02YM 

## This is for STYJ02YM (apparently EU version) with 3.5.3_0017 firmware

### Install:
- install it with HACS
- Add the configuration to configuration.yaml, example:

```yaml
vacuum:
  - platform: miio2
    host: 192.168.68.105
    token: !secret vacuum
    name: Mi hihi
```
