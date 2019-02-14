typedef i64 CanId

struct can_levels {
    1: i32 count
    2: map<CanId, double> can_levels
}

service CanLevels {
    can_levels get_cans_above_threshold(1: double percent_full)
    oneway void update_can_level(1: CanId can_id, 2: double percent_full)
}
