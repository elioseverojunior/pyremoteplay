# pyremoteplay #
[![PyPi](https://img.shields.io/pypi/v/pyremoteplay.svg)](https://pypi.org/project/pyremoteplay/)
[![Build Status](https://github.com/elioseverojunior/pyremoteplay/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/elioseverojunior/pyremoteplay/actions/?query=workflow%3Abuild)
[![Documentation Status](https://readthedocs.org/projects/pyremoteplay/badge/?version=latest)](https://pyremoteplay.readthedocs.io/en/latest/?badge=latest)

Python PlayStation Remote Play API

> **Fork notice.** This is an actively-maintained fork of
> [ktnrg45/pyremoteplay](https://github.com/ktnrg45/pyremoteplay), which has
> not seen commits since August 2022. The fork carries modernization work
> (PEP 621 packaging, uv lock files, Python 3.11+ minimum, refreshed CI,
> macOS validation, additional tests) while preserving the original API.

[Documentation](https://pyremoteplay.readthedocs.io/en/latest)

## About ##
This project provides an API to programmatically connect to and control Remote Play hosts (PS4 and PS5). The low-level networking internals is written using the Asyncio framework. In addition it includes an optional GUI, allowing to view the live stream and control the host through keyboard/mouse input. This library is based on the C/C++ project [Chiaki](https://github.com/thestr4ng3r/chiaki).

## Features ##
- API to programatically control host and expose live audio/video stream
- Registering client for Remote Play on the host
- Interface for controlling the host, which emulates a DualShock controller
- Ability to power off/on the host if standby is enabled
- GUI which displays the live stream and supports keyboard/mouse input
- Support for controllers

## Requirements ##
- Python **3.11+** (was 3.8+ in upstream)
- OS: Linux, Windows 10, **macOS** (validated in CI)

## Network Requirements ##
This project will only work with local devices; devices on the same local network.
You may be able to connect with devices on different subnets, but this is not guaranteed.

## GUI Dependencies ##
The GUI requires dependencies that may be complex to install.
Below is a list of such dependencies.
- pyav (May require FFMPEG to be installed)
- PySide6

`uvloop` is supported for the GUI and will be used if installed.

## Installation ##

### Using uv (recommended) ###

This fork is set up as a [uv](https://docs.astral.sh/uv/) project. To use it
as a dependency from another `pyproject.toml`:

```toml
[project]
dependencies = [
    "pyremoteplay @ git+https://github.com/elioseverojunior/pyremoteplay.git",
]
```

Or installed directly:

```bash
uv pip install "git+https://github.com/elioseverojunior/pyremoteplay.git"
```

Available extras (PEP 621): `av`, `fec`, `gui`, `test`, `dev`. Example:

```bash
uv pip install "pyremoteplay[av,gui] @ git+https://github.com/elioseverojunior/pyremoteplay.git"
```

### From pip ###

The legacy `pip install pyremoteplay` still resolves to the **upstream** PyPI
package (0.7.6) which does not include the modernization changes in this
fork. Use the git URL above if you need them.

```bash
pip install "git+https://github.com/elioseverojunior/pyremoteplay.git"
```

### From Source ###

Clone this repo and use uv:

```bash
git clone https://github.com/elioseverojunior/pyremoteplay.git
cd pyremoteplay
uv sync --extra dev
```

GUI extras require additional system libraries (PyAV needs FFmpeg, FEC needs
libJerasure). See the **Extras** comments in `pyproject.toml` for per-OS
install hints.

## Setup ##
There are some steps that must be completed to use this library from a user standpoint.
- Registering a PSN Account
- Linking PSN Account and client to the Remote Play Host

Configuration files are saved in the `.pyremoteplay` folder in the users home directory. Both the CLI and GUI utilize the same files.

### CLI Setup ###
Registering and linking can be completed through the cli by following the prompts after using the below command:

`pyremoteplay {host IP Address} --register`

Replace `{host IP Address}` with the IP Address of the Remote Play host.

### GUI Setup ###
Registering and linking can be performed in the options screen.

## Usage ##
To run the terminal only CLI use the following command:
`pyremoteplay {host IP Address}`

To run the GUI use the following command:
`pyremoteplay-gui`

## Notes ##
- Video decoding is performed by the CPU by default. Hardware Decoding can be enabled in the options screen in the GUI.
- You may have to install `ffmpeg` with hardware decoding enabled and then install `pyav` with the following command to allow for hardware decoding:
`pip install av --no-binary av`


## Baseline measurements ##
The CLI instance runs at 5-10% CPU usage with around 50Mb memory usage according to `top` on this author's machine: ODroid N2.

## Known Issues/To Do ##
- Text sending functions
- Add support for HDR
- Audio stutters
