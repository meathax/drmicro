# Audit every available operating condition in the configured temperature range.
package require ::quartus::sta
project_open Arcade-DrMicro -revision Arcade-DrMicro
create_timing_netlist
read_sdc
update_timing_netlist
report_clocks -file reports/quartus_clocks.rpt
report_ucp -file reports/quartus_unconstrained.rpt
set out [open reports/quartus_corners.csv w]
puts $out "corner,type,slack_ns,from,to"
set index 0
foreach_in_collection op [get_available_operating_conditions] {
 set label [get_operating_conditions_info $op -display_name]
 set_operating_conditions $op
 update_timing_netlist
 foreach kind {setup hold recovery removal} {
  set paths [get_timing_paths -$kind -npaths 1]
  foreach_in_collection path $paths {
   set slack [get_path_info $path -slack]
   set source [get_node_info [get_path_info $path -from] -name]
   set target [get_node_info [get_path_info $path -to] -name]
   puts $out "\"$label\",$kind,$slack,\"$source\",\"$target\""
  }
  report_timing -$kind -npaths 5 -detail full_path -file reports/quartus_corner_${index}_${kind}.rpt
 }
 report_min_pulse_width -nworst 5 -detail summary -file reports/quartus_corner_${index}_pulse.rpt
 incr index
}
close $out
puts "Completed $index operating-condition audits"
delete_timing_netlist
project_close
