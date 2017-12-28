# Setting project attributes by board specification
{% if boardname == "zedboard": %}
create_project -force {{ projname }} {{ projpath }}/{{ projname }}_vivado -part xc7z020clg484-1
set_property board_part em.avnet.com:zed:part0:1.3 [current_project]
{% elif boardname == "zc702": %}
create_project -force {{ projname }} {{ projpath }}/{{ projname }}_vivado -part xc7z020clg484-1
set_property board_part xilinx.com:zc702:part0:1.2 [current_project]
{% elif boardname == "zc706": %}
create_project -force {{ projname }} {{ projpath }}/{{ projname }}_vivado -part xc7z045ffg900-2
set_property board_part xilinx.com:zc706:part0:1.2 [current_project]
{% elif boardname == "zybo": %}
create_project -force {{ projname }} {{ projpath }}/{{ projname }}_vivado -part xc7z010clg400-1
set_property board_part digilentinc.com:zybo:part0:1.0 [current_project]
{% else %}
Could_not_specify_boardname...
{% endif %}

set_property  ip_repo_paths  { {{ hlsippath }} {{ libpath }} } [current_project]

create_bd_design {{ funcname }}_system

open_bd_design {{ '{' }}{{ projpath }}/{{ projname }}_vivado/{{ projname }}.srcs/sources_1/bd/{{ funcname }}_system/{{ funcname }}_system.bd}

update_ip_catalog

startgroup
create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 processing_system7_0
endgroup

startgroup
create_bd_cell -type ip -vlnv xilinx.com:hls:{{ funcname }}:1.0 {{ funcname }}_0
endgroup

startgroup
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 -config {make_external "FIXED_IO, DDR" apply_board_preset "1" Master "Disable" Slave "Disable" }  [get_bd_cells processing_system7_0]
endgroup

# connect HW return port to Zynq
{% if use_hw_interrupt_port: %}
startgroup
apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config {Master "/processing_system7_0/M_AXI_GP0" Clk "Auto" }  [get_bd_intf_pins {{ funcname }}_0/s_axi_AXILiteS]
endgroup
{% endif %}

# about bundle using s_axilite
{% if s_axilite_bundles|length > 0 : %}
	{% for s_axilite_bundle in s_axilite_bundles %}
		startgroup
		{% if s_axilite_bundle[1] == "GP1": %}
			set_property -dict [list CONFIG.PCW_USE_M_AXI_{{ s_axilite_bundle[1] }} {1}] [get_bd_cells processing_system7_0]
			apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config {Master "/processing_system7_0/M_AXI_{{ s_axilite_bundle[1] }}" Clk "Auto" }  [get_bd_intf_pins {{ funcname }}_0/s_axi_{{ s_axilite_bundle[0] }}]
		{% endif %}
		apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config {Master "/processing_system7_0/M_AXI_{{ s_axilite_bundle[1] }}" Clk "Auto" }  [get_bd_intf_pins {{ funcname }}_0/s_axi_{{ s_axilite_bundle[0] }}]
		endgroup
	{% endfor %}
{% endif %}

# about bundle using m_axi
{% if m_axi_bundles|length > 0 : %}
	{%for m_axi_bundle in m_axi_bundles %}
		startgroup
		{#使用するポートを有効にしてbundleと接続する#}
		set_property -dict [list CONFIG.PCW_USE_S_AXI_{{ m_axi_bundle[1] }} {1}] [get_bd_cells processing_system7_0]
		apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config {Master "/{{ funcname }}_0/m_axi_{{ m_axi_bundle[0]}}" Clk "Auto" }  [get_bd_intf_pins processing_system7_0/S_AXI_{{ m_axi_bundle[1] }}]
		{#address editor からinclude segment する#}
		include_bd_addr_seg [get_bd_addr_segs -excluded {{ funcname }}_0/Data_m_axi_{{ m_axi_bundle[0] }}/SEG_processing_system7_0_{{ m_axi_bundle[1] }}_IOP]
		include_bd_addr_seg [get_bd_addr_segs -excluded {{ funcname }}_0/Data_m_axi_{{ m_axi_bundle[0] }}/SEG_processing_system7_0_{{ m_axi_bundle[1] }}_M_AXI_GP0]
		{#M_axi_gp1を使用しているときはそのbd_addr_segもinclude#}
		{% if use_m_axi_GP1: %}
			include_bd_addr_seg [get_bd_addr_segs -excluded {{ funcname }}_0/Data_m_axi_{{ m_axi_bundle[0] }}/SEG_processing_system7_0_{{ m_axi_bundle[1] }}_M_AXI_GP1]
		{% endif%}
		endgroup
	{% endfor %}
{% endif %}

# about bundle using axis
{% if axis_bundles|length > 0 : %}
	{% for axis_bundle in axis_bundles %}
		startgroup
		{#使用するポートを有効にしてbundleと接続する#}
		set_property -dict [list CONFIG.PCW_USE_S_AXI_{{ axis_bundle[1] }} {1}] [get_bd_cells processing_system7_0]
		endgroup
	{% endfor %}
	{% if axis_bundles[0][2] == "in" %}
		apply_bd_automation -rule xilinx.com:bd_rule:axi4_s2mm -config {Dest_Intf "/processing_system7_0/S_AXI_{{ axis_bundles[0][1] }}" Bridge_IP "New AXI DMA (High/Medium frequency transfer)" {{ Conn_strs }} Clk_Stream "Auto" Clk_MM "Auto" }  [get_bd_intf_pins {{ funcname }}_0/{{ axis_bundles[0][0] }}]
	{% endif %}
	{% if axis_bundles[0][2] == "out" %}
		apply_bd_automation -rule xilinx.com:bd_rule:axi4_mm2s -config {Dest_Intf "/processing_system7_0/S_AXI_{{ axis_bundles[0][1] }}" Bridge_IP "New AXI DMA (High/Medium frequency transfer)" {{ Conn_strs }} Clk_Stream "Auto" Clk_MM "Auto" }  [get_bd_intf_pins {{ funcname }}_0/{{ axis_bundles[0][0] }}]
	{% endif %}
	apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config {Master "/processing_system7_0/M_AXI_GP0" Clk "Auto" }  [get_bd_intf_pins axi_dma/S_AXI_LITE]
	{#HWコアの出力ピンとDMAの間にtlast_genをおく#}
	{% for axis_bundle in axis_bundles if axis_bundle[2] == "out" %}
		{#tlast_genを配置#}
		{% set tlast_gen_name = "tlast_gen_" + loop.index0|string %} 
		create_bd_cell -type ip -vlnv xilinx.com:user:tlast_gen:1.0 {{ tlast_gen_name }}
		{#新しいDMAとHWコアが接続されているネットリストに含まれるピンのリストを取得#}
		set pins [get_bd_intf_pins -of_objects [ get_bd_intf_nets -of_objects  [get_bd_intf_pins {{ funcname }}_0/{{ axis_bundle[0] }}]]]
		{#DMAとHWコアの出力ピンの接続を削除#}
		delete_bd_objs [ get_bd_intf_nets -of_objects  [get_bd_intf_pins {{ funcname }}_0/{{ axis_bundle[0] }}]]
		{#DMAとtlast_gen/maxisを接続#}
		foreach elem $pins {if {[string equal [get_property MODE $elem] "Slave"] == 1 } {connect_bd_intf_net $elem [get_bd_intf_pins {{ tlast_gen_name }}/m_axis]}}
		{#HWコアとtlast_gen/saxisを接続#}
		foreach elem $pins {if {[string equal [get_property MODE $elem] "Master"] == 1 } {connect_bd_intf_net $elem [get_bd_intf_pins {{ tlast_gen_name }}/s_axis]}}
		{#tlast_genのクロックとリセット信号を接続#}
		{% set data_width = 32 %}
		connect_bd_net [get_bd_pins {{ tlast_gen_name }}/aclk] [get_bd_pins {{ funcname }}_0/ap_clk]
		connect_bd_net [get_bd_pins {{ tlast_gen_name }}/resetn] [get_bd_pins {{ funcname }}_0/ap_rst_n]
		{#tlastのデータ幅を設定#}
		set_property -dict [list CONFIG.TDATA_WIDTH {{ '{' }}{{ data_width }}{{ '}' }}] [get_bd_cells {{ tlast_gen_name }}]
		{#tlast_genのtlasをたてるまでのパケット数(出力の配列数)を定数値で設定#}
		{#packet_lenは現在は50で固定#}
		{% set packet_length = 50 %}
		create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 xlconstant_{{ loop.index0 }}
		set_property -dict [list CONFIG.CONST_WIDTH {9} CONFIG.CONST_VAL {{ '{' }}{{ packet_length }}{{ '}' }}] [get_bd_cells xlconstant_{{ loop.index0 }}]
		connect_bd_net [get_bd_pins {{ tlast_gen_name }}/pkt_length] [get_bd_pins xlconstant_{{ loop.index0 }}/dout]
	{% endfor %}
	{#HWコアのap_startに定数1設定#}
	startgroup
	create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 xlconstant_{{ tlast_gen_num }}
	endgroup
	connect_bd_net [get_bd_pins {{ funcname }}_0/ap_start] [get_bd_pins xlconstant_{{ tlast_gen_num }}/dout]
{% endif %}

# connect interrupt pin to zynq
{% if interrupt_pins|length > 0 : %}
	set_property -dict [list CONFIG.PCW_USE_FABRIC_INTERRUPT {1} CONFIG.PCW_IRQ_F2P_INTR {1}] [get_bd_cells processing_system7_0]
	{% if interrupt_pins|length == 1 : %}
		{#connect directly when there is only one interrupt pin#}
		connect_bd_net [get_bd_pins {{ interrupt_pins[0] }}] [get_bd_pins processing_system7_0/IRQ_F2P]
	{% else : %}
		{#connect using concat ip when there is more than one interrupt pin#}
		startgroup
        create_bd_cell -type ip -vlnv xilinx.com:ip:xlconcat:2.1 xlconcat_0
        set_property -dict [list CONFIG.NUM_PORTS {{ interrupt_pins|length }}] [get_bd_cells xlconcat_0]
       	endgroup
       	{% for interrupt_pin in interrupt_pins: %}
       		connect_bd_net [get_bd_pins {{ interrupt_pin }}] [get_bd_pins xlconcat_0/In{{ loop.index0 }}]
       	{% endfor %}
       	connect_bd_net [get_bd_pins xlconcat_0/dout] [get_bd_pins processing_system7_0/IRQ_F2P]
	{% endif %}
{% endif %}

# run implementation and generate bitstream
make_wrapper -files [get_files {{ projpath }}/{{ projname }}_vivado/{{ projname }}.srcs/sources_1/bd/{{ funcname }}_system/{{ funcname }}_system.bd] -top
add_files -norecurse {{ projpath }}/{{ projname }}_vivado/{{ projname }}.srcs/sources_1/bd/{{ funcname }}_system/hdl/{{ funcname }}_system_wrapper.v
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
launch_runs impl_1 -to_step write_bitstream
wait_on_run impl_1
open_bd_design {{ '{' }}{{ projpath }}/{{ projname }}_vivado/{{ projname }}.srcs/sources_1/bd/{{ funcname }}_system/{{ funcname }}_system.bd}
file mkdir {{ projpath }}/{{ projname}}_vivado/{{ projname }}.sdk
file copy -force {{ projpath }}/{{ projname }}_vivado/{{ projname }}.runs/impl_1/{{ funcname }}_system_wrapper.sysdef {{ projpath }}/{{ projname }}_vivado/{{ projname }}.sdk/{{ funcname }}_system_wrapper.hdf
open_run impl_1
report_utilization -hierarchical -file {{ projpath }}/utilreport.txt
exit
