# EmulationStation-Install

Scripts to easily compile, install and run EmulationStation.

I tried Retropie EmulationStation, Recalbox EmulationStation and Batocera EmulationStation
in Debian Unstable. Only Retropie ES works.

## RetroPie EmulationStation

[RetroPie ES documentation](https://retropie.org.uk/docs/EmulationStation)

Cloning and compilation:

```
$ git clone https://github.com/RetroPie/EmulationStation.git retropie-EmulationStation
$ cd retropie-EmulationStation
$ git submodule update --init --recursive
$ cmake .
$ make -j8
```

The usual compilation errors... I solved them with this patch:

```
diff --git a/CMake/Packages/FindSDL2.cmake b/CMake/Packages/FindSDL2.cmake
@@ -74,6 +74,7 @@ SET(SDL2_SEARCH_PATHS
        /opt/local # DarwinPorts
        /opt/csw # Blastwave
        /opt
+       /usr/include/x86_64-linux-gnu/SDL2
 )
```

### Running RetroPie ES for the first time

RetroPie ES creates a default `/home/kodi/.emulationstation/es_systems.cfg`. After one
platform is configured then the keyboard or a gamepad must be configured in ES.
By defaul EmulationStation looks really ugly unless a theme is installed.

Even if you use the keyboard it must be configured to control ES. If the file `es????` does
not exists, ES asks to configure a control device. Additional control devices can
be configured later.

### Installing themes

To exit ES press `F4` on the keyboard at any time.

Place themes in `/home/kodi/.emulationstation/themes/`. ES scans that directory for
themes automatically.

[Retropie Carbon](https://github.com/RetroPie/es-theme-carbon)

[Github Batocera ES theme](https://github.com/batocera-linux/batocera-themes)

[Recalbox ES Themes](https://gitlab.com/recalbox/recalbox-themes)

Recalbox has a `resources` directory at the same level as `themes`. I'm not sure if the
resources are used by ES or not, in other words, if the `resources` directory must be
installed in `/home/kodi/.emulationstation/`.

### Artwork for the ROMs

ES supports only once piece of artwork that must be set in `gamelist.xml` togheter
with the ROM metadata.

Retropie ES seems to also support the tag `<marquee>` but I'm not sure if it is used
by many themes.

## Links

[Official ES web](https://emulationstation.org/)

[Official ES Getting Started](https://emulationstation.org/gettingstarted.html)


[Recalbox ES fork](https://gitlab.com/recalbox/recalbox-emulationstation)


[Batocera.linux web](https://batocera.org/)

[GitHub ES Batocera fork](https://github.com/batocera-linux/batocera-emulationstation)

