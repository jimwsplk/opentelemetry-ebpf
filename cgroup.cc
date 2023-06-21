kprobe:cgroup_apply_control_disable
{
  printf("%lld: %s()\n", nsecs, func);
  printf("=======================================\n");
}
kprobe:cgroup_destroy_locked
{ printf("%lld: %s()\n", nsecs, func); }
/*
kprobe:kill_css
{ printf("%lld: %s()\n", nsecs, func); }
*/
kprobe:css_clear_dir
{ printf("%lld: %s()\n", nsecs, func); }

kprobe:cgroup_control
{ printf("%lld: %s()\n", nsecs, func); }
kprobe:cgroup_controllers_show
{ printf("%lld: %s()\n", nsecs, func); }
kprobe:cgroup_do_get_tree
{ printf("%lld: %s()\n", nsecs, func); }
kprobe:cgroup_events_show
{ printf("%lld: %s()\n", nsecs, func); }
kprobe:cgroup_get_from_path
{ printf("%lld: %s()\n", nsecs, func); }
// too much noise
//kprobe:cgroup_procs_show
//{ printf("%lld: %s()\n", nsecs, func); }
kprobe:cgroup_subtree_control_show
{ printf("%lld: %s()\n", nsecs, func); }
