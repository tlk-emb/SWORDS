file delete -force {{ projname }}_vivado/{{ projname }}.sdk
file mkdir {{ projname }}_vivado/{{ projname }}.sdk
sdk set_workspace {{ projname }}_vivado/{{ projname }}.sdk
file copy -force  {{ projname }}_vivado/{{ projname }}.runs/impl_1/{{ funcname }}_system_wrapper.sysdef {{ projname }}_vivado/{{ projname }}.sdk/{{ funcname }}_system_wrapper.hdf
sdk create_hw_project -name {{ funcname }}_system_wrapper_hw_platform_0 -hwspec {{ projname }}_vivado/{{ projname }}.sdk/{{ funcname }}_system_wrapper.hdf
sdk create_app_project -name {{ projname }} -proc ps7_cortexa9_0 -os standalone -hwproject {{ funcname }}_system_wrapper_hw_platform_0 -lang c
sdk import_sources -name {{ projname }} -path software -linker-script
sdk build_project -name {{ projname }}
exit
