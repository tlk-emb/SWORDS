sdk set_workspace {{ projname }}_vivado/{{ projname }}.sdk
connect
targets 2
rst -processor
source {{ projname }}_vivado/{{ projname }}.sdk/{{ funcname }}_system_wrapper_hw_platform_0/ps7_init.tcl
ps7_init
ps7_post_config
dow {{ projname }}_vivado/{{ projname }}.sdk/{{ projname }}/Debug/{{ projname }}.elf
con
exit
