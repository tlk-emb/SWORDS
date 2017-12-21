open_project {{ projname }}_hls
set_top {{ funcname }}
add_files {{ cfilepath }}
open_solution "solution1"
{%- if boardname == "zedboard": %}
set_part {xc7z020clg484-1}
{%- elif boardname == "zc702": %}
set_part {xc7z020clg484-1}
{%- elif boardname == "zc706": %}
set_part {xc7z045ffg900-2}
{%- elif boardname == "zybo": %}
set_part {xc7z010clg400-1}
{%- else %}
Could_not_specify_boardname...
{%- endif %}
create_clock -period 10 -name default
csynth_design
export_design -format ip_catalog
exit
