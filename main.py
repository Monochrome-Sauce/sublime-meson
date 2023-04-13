import importlib
importlib.import_module('Meson')

from .meson.compile import MesonCompileCommand
from .meson.panel import MesonClearPanelCommand, MesonTogglePanelCommand
from .meson.run import MesonRunCommand
from .meson.setup import MesonSetupCommand

__all__ = [
	"MesonCompileCommand",
	"MesonClearPanelCommand",
	"MesonTogglePanelCommand",
	"MesonRunCommand",
	"MesonSetupCommand",
]
