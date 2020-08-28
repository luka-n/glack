project(
  'glack',
  version: '0.1.0',
  meson_version: '>= 0.55.0',
)

# imports
gnome = import('gnome')
i18n = import('i18n')
python = import('python')

# validate python3
py_installation = python.find_installation('python3')

if not py_installation.found()
  error('No valid python3 binary found')
endif

# subdirs
subdir('data')
subdir('po')

# install python package
install_subdir('glack', install_dir: py_installation.get_install_dir())

# binary
conf = configuration_data({
  'data_dir': join_paths(get_option('prefix'), get_option('datadir'), 'glack'),
  'local_build': 'False',
  'locale_dir': join_paths(get_option('prefix'), get_option('localedir')),
  'python_dir': py_installation.get_path('purelib')
})

configure_file(
  input: 'glack.in',
  output: 'glack',
  configuration: conf,
  install_dir: get_option('bindir')
)

# local binary
local_conf = configuration_data({
  'data_dir': join_paths(meson.build_root(), 'data'),
  'local_build': 'True',
  'locale_dir': join_paths(get_option('prefix'), get_option('localedir')),
  'python_dir': meson.source_root()
})

configure_file(
  input: 'glack.in',
  output: 'glack-local',
  configuration: local_conf,
  install: false
)

# postinstall
meson.add_install_script('build-aux/meson/postinstall.py')
