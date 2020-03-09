Some technical notes to compile and run several version of EmulationStation.

## Recalbox EmulationStation

Some build documentation and first running getting started is on the 
[README](https://gitlab.com/recalbox/recalbox-emulationstation) in Gitlab.

Cloning and compilation:

```
$ git clone https://gitlab.com/recalbox/recalbox-emulationstation.git
$ cd recalbox-emulationstation
$ git submodule update --init --recursive
$ cmake .
$ make -j8
```

cmake fails with the message `Could NOT find SDL2 (missing: SDL2_INCLUDE_DIR)` and
package `libsdl2-dev` is installed. SOLUTION: Edit file `CMake/Packages/FindSDL2.cmake` and
add `/usr/include/x86_64-linux-gnu/SDL2` to `SDL2_SEARCH_PATHS` variable.

Compilation fails because of this line `#include "SDL_mixer.h"`, `SDL_mixer.h` cannot
be found. On Debian Unstable this file is located in `/usr/include/SDL2/SDL_mixer.h`. These are
the changes I did to compile Recalbox ES:

```
diff --git a/CMake/Packages/FindSDL2.cmake b/CMake/Packages/FindSDL2.cmake
@@ -74,6 +74,7 @@ SET(SDL2_SEARCH_PATHS
        /opt/local # DarwinPorts
        /opt/csw # Blastwave
        /opt
+       /usr/include/x86_64-linux-gnu/SDL2
 )
 
 FIND_PATH(SDL2_INCLUDE_DIR SDL.h

diff --git a/CMake/Packages/FindSDL2MIXER.cmake b/CMake/Packages/FindSDL2MIXER.cmake
@@ -19,6 +19,7 @@ ELSE(SDL2_Mixer_INCLUDE_DIRS)
     /usr/lib
     /usr/local/lib
     /sw/lib
+    /usr/lib/x86_64-linux-gnu # Debian Unstable
   ) 
   SET(TRIAL_INCLUDE_PATHS
     $ENV{SDL2_MIXER_HOME}/include/SDL2

diff --git a/CMakeLists.txt b/CMakeLists.txt
@@ -116,6 +116,7 @@ set(COMMON_INCLUDE_DIRS
     ${FREETYPE_INCLUDE_DIRS}
     ${FreeImage_INCLUDE_DIRS}
     ${SDL2_INCLUDE_DIR}
+    ${SDLMIXER_INCLUDE_DIR}
     #${Boost_INCLUDE_DIRS}
     ${CURL_INCLUDE_DIR}
 )
```

The executable is placed in `recalbox-emulationstation/emulationstation`

### Running Recalbox ES for the first time

When running Recalbox ES in Debian Unstable it segfaults on Debian Unstable.

## Batocera EmulationStation

### Cloning and compilation

Dependencies in Debian Unstable.

```
# apt install libsdl2-dev libvlc-dev
```

To configure and compile ES use:

```
$ git clone https://github.com/batocera-linux/batocera-emulationstation.git
$ cd batocera-emulationstation
$ git submodule update --init --recursive
$ cmake .
$ make -j8
```

cmake fails with the message `Could NOT find SDL2 (missing: SDL2_INCLUDE_DIR)` and
package `libsdl2-dev` is installed. SOLUTION: Edit file `CMake/Packages/FindSDL2.cmake` and
add `/usr/include/x86_64-linux-gnu/SDL2` to `SDL2_SEARCH_PATHS` variable.

The executable is placed in the root directory.

If I execute EmulationStation I get the following error:

```
Creating config directory "/userdata/system/configs/emulationstation"
Config directory could not be created!
```

Probably this version of ES has some hard-coded configuration for Batocera Linux. To solve
this problem do this:

```
# mkdir /userdata
# chmod kodi:kodi /userdata
```

### Running ES for the first time

Even if you use the keyboard it must be configured to control ES.

ES creates some default files in `/userdata/system/configs/emulationstation/`.

Batocera ES does not allow to exit the front-end. It is better not to use this
version of ES, it has a lot of hard-coded customizations.
