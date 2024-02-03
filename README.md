# 3DS battery patches

## Home Menu
**Battery percent in status bar (statusbatpercent)**  
This patch replaces date in statusbar with battery percent. It is not possible to display "%" character, so it shows battery percent as ":35:" instead.

![Screenshot](https://github.com/nowrep/3ds-patches/blob/master/doc/screenshot.jpg?raw=true)

**Battery icon in status bar with 25% bars (statusbaticon)**  
This patch makes the battery icon display each bar as 25% of battery charge.
## Building
- Dumping extheader.bin from the 3DS and put it in the repo's root

- installing [Python](https://www.python.org/)

- ``pip install suppress``

- Downloading [armips.exe](https://buildbot.orphis.net/armips/) to environment

- ``make``
