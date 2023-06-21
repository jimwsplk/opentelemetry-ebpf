#include <linux/cgroup-defs.h>
#include <linux/kernfs.h>

// calls kill_css() OR css_clear_dir()
kprobe:cgroup_apply_control_disable
{
  printf("%lld: %s(): cgrp=0x%llx  ssid=%2d  cgrp->kn->name=%s\n",
         nsecs,
         func,
         arg0,
         ((struct cgroup *)arg0)->self.ss->id,
         str(((struct cgroup *)arg0)->kn->name));
}

kretprobe:cgroup_apply_control_disable
{
  printf("%lld: cgroup_apply_control_disable(): returning\n\n", nsecs);
}

// always calls css_clear_dir()
// attaches on Ubuntu Focal, not on Ubuntu Jammy "WARNING: kill_css is not traceable (either non-existing, inlined, or marked as
// "notrace"); attaching to it will likely fail"
/*
*/
kprobe:kill_css {
  printf("%lld:   %s(): css=0x%llx  css->id=%3d\n",
         nsecs,
         func,
         arg0,
         ((struct cgroup_subsys_state *)arg0)->id);
  printf("%lld:     css->cgroup=0x%llx  css->cgroup->kn->name=%s\n",
         nsecs,
         ((struct cgroup_subsys_state *)arg0)->cgroup,
         str(((struct cgroup_subsys_state *)arg0)->cgroup->kn->name));
  printf("%lld:     css->ss=0x%llx  css->ss->id=%2d  css->ss->name=%s\n",
         nsecs,
         ((struct cgroup_subsys_state *)arg0)->ss,
         ((struct cgroup_subsys_state *)arg0)->ss->id,
         str(((struct cgroup_subsys_state *)arg0)->ss->name));
  printf("%lld:     css->parent=0x%llx  css->parent->ss->name=%s\n",
         nsecs,
         ((struct cgroup_subsys_state *)arg0)->parent,
         str(((struct cgroup_subsys_state *)arg0)->parent->ss->name));
}

// calls kill_css() for each css and css_clear_dir() for cgrp->self
kprobe:cgroup_destroy_locked
{
  //printf("\n%lld: %s() entry\n", nsecs, func);
  printf("%lld: %s(): cgrp=0x%llx  cgrp->kn->name=%s\n",
         nsecs,
         func,
         arg0,
         str(((struct cgroup *)arg0)->kn->name));
  printf("%lld:   cgrp->self->ss=0x%llx  cgrp->self->ss->id=%2d\n",
         nsecs,
         ((struct cgroup *)arg0)->self.ss,
         ((struct cgroup *)arg0)->self.ss->id);
}

kretprobe:cgroup_destroy_locked
{
  printf("%lld: cgroup_destroy_locked(): returning\n\n", nsecs);
}

kprobe:css_clear_dir
{
  printf("%lld:     %s(): css=0x%llx  css->id=%3d\n",
         nsecs,
         func,
         arg0,
         ((struct cgroup_subsys_state *)arg0)->id);
  printf("%lld:       css->cgroup=0x%llx  css->cgroup->kn->name=%s\n",
         nsecs,
         ((struct cgroup_subsys_state *)arg0)->cgroup,
         str(((struct cgroup_subsys_state *)arg0)->cgroup->kn->name));
  printf("%lld:       css->ss=0x%llx  css->ss->id=%2d  css->ss->name=%s\n",
         nsecs,
         ((struct cgroup_subsys_state *)arg0)->ss,
         ((struct cgroup_subsys_state *)arg0)->ss->id,
         str(((struct cgroup_subsys_state *)arg0)->ss->name));
  printf("%lld:       css->parent=0x%llx  css->parent->ss->name=%s\n",
         nsecs,
         ((struct cgroup_subsys_state *)arg0)->parent,
         str(((struct cgroup_subsys_state *)arg0)->parent->ss->name));
}

/*
kprobe:cgroup_control
{
  printf("%lld: %s(): cgrp=0x%llx  cgrp->kn->name=%s\n",
         nsecs,
         func,
         arg0,
         str(((struct cgroup *)arg0)->kn->name));
  printf("%lld:   cgrp->self.parent->cgroup=0x%llx\n",
         nsecs,
         ((struct cgroup *)arg0)->self.parent->cgroup);
  printf("%lld:   cgrp->self.parent->kn->name=%s\n",
         nsecs,
         str(((struct cgroup *)arg0)->self.parent->cgroup->kn->name));
}

kretprobe:cgroup_control
{
  printf("%lld: cgroup_control(): returning 0x%x\n",
         nsecs,
         retval);
  printf("%lld:   retval & 1 << memory_cgrp_id=0x%x\n",
         nsecs,
         retval & 1 << memory_cgrp_id);
}
*/

