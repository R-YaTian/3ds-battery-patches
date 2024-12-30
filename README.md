# 3DS battery patches

## Home Menu
**Battery percent in status bar (statusbatpercent)**  
This patch replaces date in statusbar with battery percent. It is not possible to display "%" character, so it shows battery percent as ":35:" instead.

![Screenshot](https://github.com/nowrep/3ds-patches/blob/master/doc/screenshot.jpg?raw=true)

**Battery icon in status bar with 25% bars (statusbaticon)**  
This patch makes the battery icon display each bar as 25% of battery charge.
## Building
- Dump DecryptedExHeader.bin from your HomeMenu.cia from your 3DS ([guide](https://3ds.codeberg.page/homemenu/)) and place it next to createips.py

- Rename DecryptedExHeader.bin to extheader_U.bin, extheader_E.bin, extheader_J.bin depending on the region its from

- Install [Python](https://www.python.org/)

- Run ``pip install suppress``

- Download [armips](https://buildbot.orphis.net/armips/) ([mirror](https://www.romhacking.net/utilities/635/)) and place it next to createips.py

- Either run ``createips.py`` or ``make``
