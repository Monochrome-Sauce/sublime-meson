import importlib
importlib.import_module('Meson')

from .meson.compile import MesonCompileCommand
from .meson.panel import MesonClearPanelCommand, MesonTogglePanelCommand
from .meson.setup import MesonSetupCommand

__all__ = [
	"MesonCompileCommand",
	"MesonClearPanelCommand",
	"MesonTogglePanelCommand",
	"MesonSetupCommand",
]
