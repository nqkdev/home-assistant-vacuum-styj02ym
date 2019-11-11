# Hacky Home assistant support for Xiaomi vaccum STYJ02YM 

### Install:
- Create the following folder structure: /config/custom_components/miio2 and place all files there [4 files](https://github.com/nqkdev/home-assistant-vacuum-styj02ym) there.
- Add the configuration to configuration.yaml, example:

```yaml
vacuum:
  - platform: miio2
    host: 192.168.68.105
    token: !secret vacuum
    name: Mi hihi
```
