/* A37 V2 Power HAL extension. No libc dependency except existing dlsym PLT. */
typedef unsigned long usize;
typedef long ssize;
#define HIDDEN __attribute__((visibility("hidden")))
extern HIDDEN int original_hint(int hint, void *data);
extern HIDDEN int original_interactive(int interactive);
extern HIDDEN void *original_dlsym(void *handle, const char *name);

struct bridge_state {
    unsigned valid;
    int profile;
    int (*set_property)(const char *, const char *);
};
extern HIDDEN struct bridge_state a37_state;

void *memcpy(void *destination, const void *source, usize length)
{
    unsigned char *out = destination;
    const unsigned char *in = source;
    usize i;
    for (i = 0; i < length; i++) out[i] = in[i];
    return destination;
}

static long call3(long n, long a, long b, long c)
{
    register long x8 __asm__("x8") = n;
    register long x0 __asm__("x0") = a;
    register long x1 __asm__("x1") = b;
    register long x2 __asm__("x2") = c;
    __asm__ volatile("svc 0" : "+r"(x0) : "r"(x8), "r"(x1), "r"(x2) : "memory", "cc");
    return x0;
}

static long open_path(const char *path, int flags)
{
    /* openat without O_CREAT; mode is unused. */
    return call3(56, -100, (long)path, flags);
}

static int read_number(const char *path)
{
    char buffer[24];
    long fd = open_path(path, 0), length;
    int i, value = 0;
    if (fd < 0) return -1;
    length = call3(63, fd, (long)buffer, sizeof(buffer));
    call3(57, fd, 0, 0);
    if (length <= 0 || buffer[0] < '0' || buffer[0] > '9') return -1;
    for (i = 0; i < length && buffer[i] >= '0' && buffer[i] <= '9'; i++) {
        if (value > 214748364 || (value == 214748364 && buffer[i] > '7')) return -1;
        value = value * 10 + buffer[i] - '0';
    }
    return value;
}

static int write_text(const char *path, const char *text)
{
    usize length = 0;
    long fd, written;
    while (text[length]) length++;
    fd = open_path(path, 1);
    if (fd < 0) return 0;
    written = call3(64, fd, (long)text, length);
    call3(57, fd, 0, 0);
    return written == (long)length;
}

static int write_number(const char *path, int value)
{
    char digits[12];
    int i = sizeof(digits) - 1;
    digits[i] = 0;
    do { digits[--i] = '0' + value % 10; value /= 10; } while (value);
    return write_text(path, digits + i);
}

/* Exported so the host emulator can exercise the same policy code directly. */
int a37_apply(int profile)
{
    char cpu_min[] = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq";
    char cpu_max[] = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq";
    int cpu, maximum, floor, cpu_ok = 0, failed = 0;
    const int performance = profile == 2;
    if (profile < 0 || profile > 2) return -1;
    /* Shared policy may be exposed under CPU1/2 when CPU0 is offline. */
    for (cpu = 0; cpu < 4; cpu++) {
        cpu_min[sizeof("/sys/devices/system/cpu/cpu") - 1] =
            cpu_max[sizeof("/sys/devices/system/cpu/cpu") - 1] = '0' + cpu;
        maximum = read_number(cpu_max);
        if (maximum <= 0 || maximum > 1209600) continue;
        floor = performance ? maximum : 200000;
        if (floor > maximum) floor = maximum;
        if (write_number(cpu_min, floor)) { cpu_ok = 1; break; }
    }
    if (!cpu_ok) failed++;
    maximum = read_number("/sys/class/kgsl/kgsl-3d0/devfreq/max_freq");
    if (maximum > 0 && maximum <= 620000000) {
        floor = performance ? maximum : 200000000;
        if (floor > maximum) floor = maximum;
        if (!write_number("/sys/class/kgsl/kgsl-3d0/devfreq/min_freq", floor)) failed++;
    } else failed++;
    if (!write_text("/sys/devices/system/cpu/cpufreq/interactive/hispeed_freq",
                    performance ? "1209600" : "998400")) failed++;
    if (!write_text("/sys/devices/system/cpu/cpufreq/interactive/target_loads",
        performance ?
        "1 200000:25 400000:35 533333:45 800000:55 998400:60 1094400:65 1152000:70 1209600:80" :
        "1 200000:25 400000:35 533333:45 800000:55 998400:65 1094400:65 1152000:70 1209600:80")) failed++;
    if (!write_text("/sys/class/kgsl/kgsl-3d0/idle_timer", performance ? "500" : "80")) failed++;
    return failed;
}

static void publish(int profile, int failures)
{
    char value[2] = { '0' + profile, 0 };
    if (!a37_state.set_property)
        a37_state.set_property = original_dlsym((void *)0, "__system_property_set");
    if (a37_state.set_property) {
        a37_state.set_property("vendor.a37.profile", value);
        a37_state.set_property("vendor.a37.profile_apply", failures ? "incomplete" : "ok");
    }
}

int a37_hint(int hint, void *data)
{
    int profile = hint == 0x111 ? (data ? *(int *)data : 0) : -1;
    int result = original_hint(hint, data);
    if (profile >= 0 && profile <= 2) {
        a37_state.profile = profile;
        a37_state.valid = 1;
        publish(profile, a37_apply(profile));
    }
    return result;
}

int a37_interactive(int interactive)
{
    int result = original_interactive(interactive);
    if (a37_state.valid)
        publish(a37_state.profile, a37_apply(a37_state.profile));
    return result;
}
