# EmulationStation-Install

Scripts to easily compile, install and run EmulationStation.

I tested several forsk of EmulationStation including **Retropie EmulationStation**, **Recalbox EmulationStation** and **Batocera EmulationStation** in Debian Unstable. Only Retropie ES semms to work well and hence here I include instructions to build and use that fork only. Additional comments about the other forks of ES can be found in the [NOTES file](./NOTES.md).

## RetroPie EmulationStation

[RetroPie ES documentation](https://retropie.org.uk/docs/EmulationStation)

Cloning and compilation:

```
$ git clone https://github.com/RetroPie/EmulationStation.git retropie-ES
$ cd retropie-ES
$ git submodule update --init --recursive
$ cmake .
$ make -j8
```

The usual compilation errors... I solved them with this patch. NOTE that on Ubuntu Focal Fossa this is not necessary.

```
diff --git a/CMake/Packages/FindSDL2.cmake b/CMake/Packages/FindSDL2.cmake
@@ -74,6 +74,7 @@ SET(SDL2_SEARCH_PATHS
        /opt/local # DarwinPorts
        /opt/csw # Blastwave
        /opt
+       /usr/include/x86_64-linux-gnu/SDL2
 )
```

To run EmulationStation with the script `emulationstation.sh` and be able to reboot and power off the system, edit the file `retropie-ES/es-core/src/platform.cpp` and comment a couple of lines of code:

```
diff --git a/es-core/src/platform.cpp b/es-core/src/platform.cpp
@@ -78,12 +78,12 @@ void processQuitMode()
        case QuitMode::REBOOT:
                LOG(LogInfo) << "Rebooting system";
                touch("/tmp/es-sysrestart");
-               runRestartCommand();
+               // runRestartCommand();
                break;
        case QuitMode::SHUTDOWN:
                LOG(LogInfo) << "Shutting system down";
                touch("/tmp/es-shutdown");
-               runShutdownCommand();
+               // runShutdownCommand();
                break;
        }
 }
```

### Running RetroPie ES for the first time

RetroPie ES creates a default `/home/kodi/.emulationstation/es_systems.cfg`. After one platform is configured then the keyboard or a gamepad must be configured in ES. By defaul EmulationStation looks really ugly unless a theme is installed.

Even if you use the keyboard to control ES it must be configured to control ES. In other words, you can not use your keyboard or any other medium right away without configuring it in ES first. If the file `es_input.cfg` does not exist, ES asks to configure a control device. Additional control devices can be configured later.

To exit ES press `F4` on the keyboard at any time.

### Installing ES themes or skins

Place themes in `/home/kodi/.emulationstation/themes/`. ES scans this directory for themes automatically at startup. The directory name of the theme is irrelevant.

#### Retropie themes

[Retropie ES Carbon theme (default theme)](https://github.com/RetroPie/es-theme-carbon)

Carbon is the default theme for Retropie.

[This script](https://github.com/RetroPie/RetroPie-Setup/blob/master/scriptmodules/supplementary/esthemes.sh) has a collection of all supported Retropie themes. See the function `gui_esthemes()`

```
local themes=(
        'RetroPie carbon'
        'RetroPie carbon-centered'
        ...
```

The first part of the theme is the Github user name and the second part is the repository name. To download the theme, build the Github URL like this:

```
https://github.com/$USERNAME/es-theme-$THEMENAME
```

For example, to download the theme `RetroPie carbon` use the URL `https://github.com/RetroPie/es-theme-carbon`.

Retropie also has a [theme preview repository](https://github.com/wetriner/es-theme-gallery) in
Github and another in the [Retropie documentation](https://retropie.org.uk/docs/Themes/).

#### Batocera themes

[Github Batocera ES theme (default theme)](https://github.com/batocera-linux/batocera-themes)

#### EmuELEC themes

[EmuELEC Carbon ES theme (default theme)](https://github.com/EmuELEC/es-theme-EmuELEC-carbon)

EmuELEC themes do not work on Retropie ES.

#### Recalbox themes

[Recalbox ES themes](https://gitlab.com/recalbox/recalbox-themes)

**IMPORTANT** Recalbox themes do not work well with the Retropie fork of ES. When you select a Recalbox theme ES freezes some seconds. Also, some Recalbox platform names do not match the Retropie ones.

Recalbox has a `resources` directory at the same level as `themes`. I'm not sure if the resources are used by ES or not, in other words, if the `resources` directory must be installed in `/home/kodi/.emulationstation/`.

### Artwork for the ROMs

ES supports only once piece of artwork that must be set in `gamelist.xml` togheter with the ROM metadata.

Retropie ES seems to also support the tag `<marquee>` but I'm not sure if it is used by many themes.

## Some useful Links

[Official ES web](https://emulationstation.org/)

[Official ES Getting Started](https://emulationstation.org/gettingstarted.html)

[Recalbox ES fork](https://gitlab.com/recalbox/recalbox-emulationstation)

[Batocera.linux web](https://batocera.org/)

[GitHub ES Batocera fork](https://github.com/batocera-linux/batocera-emulationstation)
