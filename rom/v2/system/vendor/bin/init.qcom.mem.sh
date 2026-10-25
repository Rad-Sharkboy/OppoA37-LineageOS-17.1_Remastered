#!/vendor/bin/sh
# Hardcoded Memory Parameters for 2GB 64-bit

# Calculate adj threshold for PPR and ALMK
adj_series=`cat /sys/module/lowmemorykiller/parameters/adj`
adj_1="${adj_series#*,}"
set_almk_ppr_adj="${adj_1%%,*}"
set_almk_ppr_adj=$(((set_almk_ppr_adj * 6) + 6))

echo $set_almk_ppr_adj > /sys/module/lowmemorykiller/parameters/adj_max_shift
echo $set_almk_ppr_adj > /sys/module/process_reclaim/parameters/min_score_adj

# Hardcoded Process Reclaim (PPR) values for 2GB RAM
echo 1 > /sys/module/process_reclaim/parameters/enable_process_reclaim
echo 70 > /sys/module/process_reclaim/parameters/pressure_max
echo 10 > /sys/module/process_reclaim/parameters/pressure_min
echo 30 > /sys/module/process_reclaim/parameters/swap_opt_eff
echo 1024 > /sys/module/process_reclaim/parameters/per_swap_size

# Hardcoded Low Memory Killer (LMK) values for 64-bit
echo 0 > /sys/module/lowmemorykiller/parameters/enable_adaptive_lmk
echo "18432,23040,27648,32256,55296,80640" > /sys/module/lowmemorykiller/parameters/minfree
echo 81250 > /sys/module/lowmemorykiller/parameters/vmpressure_file_min

exit 0