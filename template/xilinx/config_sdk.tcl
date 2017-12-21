sdk set_workspace {{ projname }}_vivado/{{ projname }}.sdk
connect
fpga {{ projname }}_vivado/{{ projname }}.sdk/{{ funcname }}_system_wrapper_hw_platform_0/{{ funcname }}_system_wrapper.bit
exit
