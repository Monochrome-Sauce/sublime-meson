from . import utils
from pathlib import Path
from typing import Any, Iterable, List, Optional
import enum, os


def _test_paths_for_executable(paths: Iterable[Path], executable: str) -> Optional[Path]:
	for directory in paths:
		file_path: Path = directory / executable
		if file_path.exists() and os.access(file_path, os.X_OK):
			return file_path

def _find_binary(binary_name: str) -> Optional[Path]:
	paths: Iterable[Path] = map(Path, os.environ.get('PATH', '').split(os.pathsep))
	if os.name == 'nt':
		binary_name += '.exe'
	
	path: Optional[Path] = _test_paths_for_executable(paths, binary_name)
	if path:
		return path
	
	# /usr/local/bin:/usr/local/meson/bin
	if os.name == 'nt':
		extra_paths = (
			os.path.join(os.environ.get('ProgramFiles', ''), 'meson', 'bin'),
			os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'meson', 'bin'),
		)
	else:
		extra_paths = ('/usr/local/bin', '/usr/local/meson/bin')
	
	return _test_paths_for_executable(map(Path, extra_paths), binary_name)

MESON_BINARY: Path = _find_binary('meson') or Path()
assert(MESON_BINARY.is_file())
del _test_paths_for_executable
del _find_binary



def _can_be_arg(s: str) -> bool:
	for c in s:
		if not c.islower() and c != '-':
			return False
	return True

def _append(cmd: List[str], *args: str):
	for arg in args:
		cmd.append(str(arg))

def _append_str(cmd: List[str], name: str, value: str):
	assert(_can_be_arg(name))
	_append(cmd, f'--{name}', value)

def _append_bool(cmd: List[str], name: str, value: bool):
	assert(_can_be_arg(name))
	if value: _append(cmd, f'--{name}')

def _append_optional(cmd: List[str], name: str, value: Optional[Any]):
	assert(_can_be_arg(name))
	if value is not None: _append(cmd, f'--{name}', str(value))



class _ParamEnum(enum.Enum):
	def lowercase(self) -> str: return self.name.lower()
	
	def __str__(self): return self.lowercase()

class AutoFeatures(_ParamEnum):
	ENABLED = enum.auto()
	DISABLED = enum.auto()
	AUTO = enum.auto()

class Backend(_ParamEnum):
	NINJA = enum.auto()
	VS = enum.auto()
	VS2010 = enum.auto()
	VS2012 = enum.auto()
	VS2013 = enum.auto()
	VS2015 = enum.auto()
	VS2017 = enum.auto()
	VS2019 = enum.auto()
	XCODE = enum.auto()

class BuildType(_ParamEnum):
	PLAIN = enum.auto()
	DEBUG = enum.auto()
	DEBUGOPTIMIZED = enum.auto()
	RELEASE = enum.auto()
	MINIMIZE = enum.auto()
	CUSTOM = enum.auto()

class Layout(_ParamEnum):
	MIRROR = enum.auto()
	FLAT = enum.auto()

class Library(_ParamEnum):
	SHARED = enum.auto()
	STATIC = enum.auto()
	BOTH = enum.auto()

class Optimization(_ParamEnum):
	O0 = enum.auto()
	OG = enum.auto()
	O1 = enum.auto()
	O2 = enum.auto()
	O3 = enum.auto()
	OS = enum.auto()
	
	def __str__(self): return self.lowercase()[1:]

class Unity(_ParamEnum):
	ON = enum.auto()
	OFF = enum.auto()
	SUBPROJECTS = enum.auto()

class WarnLevel(_ParamEnum):
	L0 = enum.auto()
	L1 = enum.auto()
	L2 = enum.auto()
	L3 = enum.auto()
	
	def __str__(self): return self.lowercase()[1:]

class WrapMode(_ParamEnum):
	DEFAULT = enum.auto()
	NOFALLBACK = enum.auto()
	NODOWNLOAD = enum.auto()
	FORCEFALLBACK = enum.auto()
	NOPROMOTE = enum.auto()


# options:
#   --debug                                    Debug
#   --errorlogs                                Whether to print the logs from failing tests.
#   --fatal-meson-warnings                     Make all Meson warnings fatal
#   --reconfigure                              Set options and reconfigure the project. Useful when
#                                              new options have been added to the project and the
#                                              default value is not working.
#   --stdsplit                                 Split stdout and stderr in test logs
#   --strip                                    Strip targets on install
#   --werror                                   Treat warnings as errors
#   --wipe                                     Wipe build directory and reconfigure using previous
#                                              command line options. Useful when build directory got
#                                              corrupted, or when rebuilding with a newer version.
#   --auto-features {enabled,disabled,auto}    Override value of all 'auto' features.
#   --backend {ninja,vs,vs2010,vs2012,vs2013,vs2015,vs2017,vs2019,vs2022,xcode}
#                                              Backend to use.
#   --buildtype {plain,debug,debugoptimized,release,minsize,custom}
#                                              Build type to use.
#   --default-library {shared,static,both}     Default library type.
#   --layout {mirror,flat}                     Build directory layout.
#   --optimization {0,g,1,2,3,s}               Optimization level.
#   --unity {on,off,subprojects}               Unity build.
#   --warnlevel {0,1,2,3}                      Compiler warning level to use.
#   --wrap-mode {default,nofallback,nodownload,forcefallback,nopromote}
#                                              Wrap mode.
#   --prefix PREFIX                            Installation prefix.
#   --bindir BINDIR                            Executable directory.
#   --datadir DATADIR                          Data file directory.
#   --includedir INCLUDEDIR                    Header file directory.
#   --infodir INFODIR                          Info page directory.
#   --libdir LIBDIR                            Library directory.
#   --libexecdir LIBEXECDIR                    Library executable directory.
#   --localedir LOCALEDIR                      Locale data directory.
#   --localstatedir LOCALSTATEDIR              Localstate data directory.
#   --mandir MANDIR                            Manual page directory.
#   --sbindir SBINDIR                          System executable directory.
#   --sharedstatedir SHAREDSTATEDIR            Architecture-independent data directory.
#   --sysconfdir SYSCONFDIR                    Sysconf data directory.
def setup(build_directory: Path, *,
	debug: bool = False,
	error_logs: bool = False,
	fatal_meson_warnings: bool = False,
	reconfigure: bool = False,
	stdsplit: bool = False,
	strip: bool = False,
	werror: bool = False,
	wipe: bool = False,
	auto_features: Optional[AutoFeatures] = None,
	backend: Optional[Backend] = None,
	buildtype: Optional[BuildType] = None,
	default_library: Optional[Library] = None,
	layout: Optional[Layout] = None,
	optimization: Optional[Optimization] = None,
	unity: Optional[Unity] = None,
	warnlevel: Optional[WarnLevel] = None,
	wrap_mode: Optional[WrapMode] = None,
	prefix: Optional[Path] = None,
	bin_dir: Optional[Path] = None, data_dir: Optional[Path] = None,
	include_dir: Optional[Path] = None, info_dir: Optional[Path] = None,
	lib_dir: Optional[Path] = None, libexec_dir: Optional[Path] = None,
	localstate_dir: Optional[Path] = None, locale_dir: Optional[Path] = None,
	man_dir: Optional[Path] = None, sbin_dir: Optional[Path] = None,
	sharedstate_dir: Optional[Path] = None, sysconf_dir: Optional[Path] = None,
) -> List[str]:
	'''Creates a terminal command corresponding to the Meson command of the same name.
	
	Run `meson setup --help` for more details.
	'''
	cmd: List[str] = [str(MESON_BINARY), 'setup']
	
	_append_bool(cmd, 'debug', debug)
	_append_bool(cmd, 'errorlogs', error_logs)
	_append_bool(cmd, 'fatal-meson-warnings', fatal_meson_warnings)
	_append_bool(cmd, 'reconfigure', reconfigure)
	_append_bool(cmd, 'stdsplit', stdsplit)
	_append_bool(cmd, 'strip', strip)
	_append_bool(cmd, 'werror', werror)
	_append_bool(cmd, 'wipe', wipe)
	
	_append_optional(cmd, 'auto-features', auto_features)
	_append_optional(cmd, 'backend', backend)
	_append_optional(cmd, 'buildtype', buildtype)
	_append_optional(cmd, 'default-library', default_library)
	_append_optional(cmd, 'layout', layout)
	_append_optional(cmd, 'optimization', optimization)
	_append_optional(cmd, 'unity', unity)
	_append_optional(cmd, 'warn-level', warnlevel)
	_append_optional(cmd, 'wrap-mode', wrap_mode)
	
	_append_optional(cmd, 'bindir', bin_dir)
	_append_optional(cmd, 'datadir', data_dir)
	_append_optional(cmd, 'includedir', include_dir)
	_append_optional(cmd, 'infodir', info_dir)
	_append_optional(cmd, 'libdir', lib_dir)
	_append_optional(cmd, 'libexecdir', libexec_dir)
	_append_optional(cmd, 'localstatedir', localstate_dir)
	_append_optional(cmd, 'localedir', locale_dir)
	_append_optional(cmd, 'mandir', man_dir)
	_append_optional(cmd, 'prefix', prefix)
	_append_optional(cmd, 'sbindir', sbin_dir)
	_append_optional(cmd, 'sharedstatedir', sharedstate_dir)
	_append_optional(cmd, 'sysconfdir', sysconf_dir)
	
	cmd.append(str(build_directory))
	utils.log(f'Meson::setup => {cmd}')
	return cmd

# options:
#   --clearcache                               Clear cached state (e.g. found dependencies).
#   --debug                                    Debug.
#   --errorlogs                                Whether to print the logs from failing tests.
#   --stdsplit                                 Split stdout and stderr in test logs.
#   --strip                                    Strip targets on install.
#   --werror                                   Treat warnings as errors.
#   --auto-features {enabled,disabled,auto}    Override value of all 'auto' features.
#   --backend {ninja,vs,vs2010,vs2012,vs2013,vs2015,vs2017,vs2019,vs2022,xcode}
#                                              Backend to use.
#   --buildtype {plain,debug,debugoptimized,release,minsize,custom}
#                                              Build type to use.
#   --default-library {shared,static,both}     Default library type.
#   --layout {mirror,flat}                     Build directory layout.
#   --optimization {0,g,1,2,3,s}               Optimization level.
#   --unity {on,off,subprojects}               Unity build.
#   --warnlevel {0,1,2,3}                      Compiler warning level to use.
#   --wrap-mode {default,nofallback,nodownload,forcefallback,nopromote}
#                                              Wrap mode (default: default).
#   --prefix PREFIX                            Installation prefix.
#   --bindir BINDIR                            Executable directory.
#   --datadir DATADIR                          Data file directory.
#   --includedir INCLUDEDIR                    Header file directory.
#   --infodir INFODIR                          Info page directory.
#   --libdir LIBDIR                            Library directory.
#   --libexecdir LIBEXECDIR                    Library executable directory.
#   --localedir LOCALEDIR                      Locale data directory.
#   --localstatedir LOCALSTATEDIR              Localstate data directory.
#   --mandir MANDIR                            Manual page directory.
#   --sbindir SBINDIR                          System executable directory.
#   --sharedstatedir SHAREDSTATEDIR            Architecture-independent data directory.
#   --sysconfdir SYSCONFDIR                    Sysconf data directory.
def configure(build_directory: Path, *,
	clearcache: bool = False,
	debug: bool = False,
	errorlogs: bool = False,
	stdsplit: bool = False,
	strip: bool = False,
	werror: bool = False,
	auto_features: Optional[AutoFeatures] = None,
	backend: Optional[Backend] = None,
	buildtype: Optional[BuildType] = None,
	default_library: Optional[Library] = None,
	layout: Optional[Layout] = None,
	optimization: Optional[Optimization] = None,
	unity: Optional[Unity] = None,
	warnlevel: Optional[WarnLevel] = None,
	wrap_mode: Optional[WrapMode] = None,
	prefix: Optional[Path] = None,
	bin_dir: Optional[Path] = None, data_dir: Optional[Path] = None,
	include_dir: Optional[Path] = None, info_dir: Optional[Path] = None,
	lib_dir: Optional[Path] = None, libexec_dir: Optional[Path] = None,
	localstate_dir: Optional[Path] = None, locale_dir: Optional[Path] = None,
	man_dir: Optional[Path] = None, sbin_dir: Optional[Path] = None,
	sharedstate_dir: Optional[Path] = None, sysconf_dir: Optional[Path] = None,
) -> List[str]:
	'''Creates a terminal command corresponding to the Meson command of the same name.
	
	Run `meson configure --help` for more details.
	'''
	cmd: List[str] = [str(MESON_BINARY), 'configure']
	
	_append_bool(cmd, 'clearcache', clearcache)
	_append_bool(cmd, 'debug', debug)
	_append_bool(cmd, 'errorlogs', errorlogs)
	_append_bool(cmd, 'stdsplit', stdsplit)
	_append_bool(cmd, 'strip', strip)
	_append_bool(cmd, 'werror', werror)
	
	_append_optional(cmd, 'auto-features', auto_features)
	_append_optional(cmd, 'backend', backend)
	_append_optional(cmd, 'buildtype', buildtype)
	_append_optional(cmd, 'default-library', default_library)
	_append_optional(cmd, 'layout', layout)
	_append_optional(cmd, 'optimization', optimization)
	_append_optional(cmd, 'unity', unity)
	_append_optional(cmd, 'warn-level', warnlevel)
	_append_optional(cmd, 'wrap-mode', wrap_mode)
	
	_append_optional(cmd, 'bindir', bin_dir)
	_append_optional(cmd, 'datadir', data_dir)
	_append_optional(cmd, 'includedir', include_dir)
	_append_optional(cmd, 'infodir', info_dir)
	_append_optional(cmd, 'libdir', lib_dir)
	_append_optional(cmd, 'libexecdir', libexec_dir)
	_append_optional(cmd, 'localstatedir', localstate_dir)
	_append_optional(cmd, 'localedir', locale_dir)
	_append_optional(cmd, 'mandir', man_dir)
	_append_optional(cmd, 'prefix', prefix)
	_append_optional(cmd, 'sbindir', sbin_dir)
	_append_optional(cmd, 'sharedstatedir', sharedstate_dir)
	_append_optional(cmd, 'sysconfdir', sysconf_dir)
	
	cmd.append(str(build_directory))
	utils.log(f'Meson::configure => {cmd}')
	return cmd

# positional arguments:
# args                   Optional list of test names to run. "testname" to run
#                        all tests with that name, "subprojname:testname" to
#                        specifically run "testname" from "subprojname",
#                        "subprojname:" to run all tests defined by "subprojname".
# test-args TEST_ARGS    Arguments to pass to the specified test(s) or all tests.
#
# options:
#   --benchmark                      Run benchmarks instead of tests.
#   --gdb                            Run test under gdb.
#   --no-rebuild                     Do not rebuild before running tests.
#   --no-stdsplit                    Do not split stderr and stdout in test logs.
#   --print-errorlogs                Whether to print failing tests' logs.
#   --quiet                          Produce less output to the terminal.
#   --verbose                        Do not redirect stdout and stderr
#   --gdb-path GDB_PATH              Path to the gdb binary (default: gdb).
#   --logbase LOGBASE                Base name for log file.
#   --no-suite SUITE                 Do not run tests belonging to the given suite.
#   --num-processes NUM_PROCESSES    How many parallel processes to use.
#   --repeat REPEAT                  Number of times to run the tests.
#   --setup SETUP                    Which test setup to use.
#   --suite SUITE                    Only run tests belonging to the given suite.
#   --timeout-multiplier TIMEOUT_MULTIPLIER
#                                    Define a multiplier for test timeout, for example when
#                                    running tests in particular conditions they might take more
#                                    time to execute (<= 0 to disable timeout).
#   --wrapper WRAPPER                Wrapper to run tests with (e.g. Valgrind).
def test(test_directory: Path, test_args: List[str] = [], *,
	benchmarks: bool = False,
	gdb: bool = False,
	no_rebuild: bool = False,
	no_stdsplit: bool = False,
	print_errorlogs: bool = False,
	quiet: bool = False,
	verbose: bool = False,
	gdb_path: Optional[Path] = None,
	logbase: Optional[Path] = None,
	no_suite: Optional[str] = None,
	num_processes: Optional[int] = None,
	repeat: Optional[int] = None,
	setup: Optional[str] = None,
	suite: Optional[str] = None,
	timeout_multiplier: Optional[int] = None,
	wrapper: Optional[str] = None,
) -> List[str]:
	'''Creates a terminal command corresponding to the Meson command of the same name.
	
	Run `meson test --help` for more details.
	'''
	cmd: List[str] = [str(MESON_BINARY), 'test']
	_append(cmd, '-C', str(test_directory))
	
	_append_bool(cmd, 'benchmarks', benchmarks)
	_append_bool(cmd, 'gdb', gdb)
	_append_bool(cmd, 'no-rebuild', no_rebuild)
	_append_bool(cmd, 'no-stdsplit', no_stdsplit)
	_append_bool(cmd, 'print-errorlogs', print_errorlogs)
	_append_bool(cmd, 'quiet', quiet)
	_append_bool(cmd, 'verbose', verbose)
	
	_append_optional(cmd, 'gdb-path', gdb_path)
	_append_optional(cmd, 'logbase', logbase)
	_append_optional(cmd, 'no-suite', no_suite)
	_append_optional(cmd, 'num-processes', num_processes)
	_append_optional(cmd, 'repeat', repeat)
	_append_optional(cmd, 'setup', setup)
	_append_optional(cmd, 'suite', suite)
	_append_optional(cmd, 'timeout-multiplier', timeout_multiplier)
	_append_optional(cmd, 'wrapper', wrapper)
	
	if len(test_args):
		_append_str(cmd, 'test-args', ' '.join(test_args))
	
	utils.log(f'Meson::test => {cmd}')
	return cmd

# options:
#   --clean        Clean the build directory.
#   --verbose      Show more verbose output.
#   --jobs JOBS    The number of worker jobs to run (if supported). If the value
#                  is less than 1 the build program will guess.
def compile(build_directory: Path, *,
	clean: bool = False,
	verbose: bool = False,
	jobs: Optional[int] = None,
) -> List[str]:
	'''Creates a terminal command corresponding to the Meson command of the same name.
	
	Run `meson compile --help` for more details.
	'''
	cmd: List[str] = [str(MESON_BINARY), 'compile']
	_append(cmd, '-C', str(build_directory))
	
	_append_bool(cmd, 'clean', clean)
	_append_bool(cmd, 'verbose', verbose)
	_append_optional(cmd, 'jobs', jobs)
	
	utils.log(f'Meson::compile => {cmd}')
	return cmd
