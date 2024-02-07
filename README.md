# Meson Build - Sublime Text Plugin

[Meson](https://mesonbuild.com) build system integration for Sublime Text.

## Installation

### Package Control

Install it from [Package Control](https://packagecontrol.io/packages/Meson).

### Manual Installation

Copy this repo's folder into your Sublime Text `Packages` directory. You will need to rename the folder to "Meson".

## How to use

1. Open the Command Palette (`cmd+shift+p` on OS X, `ctrl+shift+p` on Linux/Windows).
2. Start typing "Meson", then you'll see the available commands.
3. Select one of the commands.

## Features

- Syntax highlighting for `meson.build` and `meson-options.txt` files.
- The following commands output to a Sublime Text panel. Every command containing "Panel" affects only the panel itself.
- `Meson: Setup` setup projects via `meson setup`.
- `Meson: Compile` compile projects via `meson compile`. This feature requires Meson version >= 0.54.
- Integrates with Sublime Text's build systems. It currently provides `meson compile`, `meson setup` and `meson test`.

## Contributing

Check out the [issues](https://github.com/Monochrome-Sauce/sublime-meson/issues) to see what is being worked on next, suggest something new or report a bug.
