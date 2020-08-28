# compile gresource file
gnome.compile_resources(
  'glack',
  'glack.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: join_paths(get_option('prefix'), get_option('datadir'), 'glack'),
)

install_data(
  'com.gitlab.lnovsak.Glack.gschema.xml',
  install_dir: join_paths(get_option('datadir'), 'glib-2.0/schemas')
)

# compile and validate desktop file
desktop_file = i18n.merge_file(
  input: 'com.gitlab.lnovsak.Glack.desktop.in',
  output: 'com.gitlab.lnovsak.Glack.desktop',
  type: 'desktop',
  po_dir: join_paths(meson.source_root(), 'po'),
  install: true,
  install_dir: join_paths(get_option('datadir'), 'applications')
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils, args: [desktop_file])
endif

# compile and validate appdata file
appstream_file = i18n.merge_file(
  input: 'com.gitlab.lnovsak.Glack.appdata.xml.in',
  output: 'com.gitlab.lnovsak.Glack.appdata.xml',
  po_dir: join_paths(meson.source_root(), 'po'),
  install: true,
  install_dir: join_paths(get_option('datadir'), 'appdata')
)

appstream_util = find_program('appstream-util', required: false)
if appstream_util.found()
  test('Validate appstream file', appstream_util, args: ['validate', appstream_file])
endif

# validate gschema file
compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file', compile_schemas,
    args: ['--strict', '--dry-run', meson.current_source_dir()]
  )
endif
