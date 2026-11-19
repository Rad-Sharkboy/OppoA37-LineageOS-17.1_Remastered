/* Preserve Android's ARM32 memory helper exports from the original binaries.
 * These EABI helpers have void return values; memset's argument order differs. */
#include <stddef.h>
/* Declarations only: Android's fortified inline headers explicitly emit memory
 * builtins, which would lower these wrappers recursively to EABI helpers. */
extern void *memcpy(void *,const void *,size_t);
extern void *memset(void *,int,size_t);
#define EXPORT __attribute__((visibility("default")))
EXPORT void __aeabi_memcpy(void *d,const void *s,size_t n) { memcpy(d,s,n); }
EXPORT void __aeabi_memcpy4(void *d,const void *s,size_t n) { memcpy(d,s,n); }
EXPORT void __aeabi_memcpy8(void *d,const void *s,size_t n) { memcpy(d,s,n); }
EXPORT void __aeabi_memset(void *d,size_t n,int c) { memset(d,c,n); }
EXPORT void __aeabi_memset4(void *d,size_t n,int c) { memset(d,c,n); }
EXPORT void __aeabi_memset8(void *d,size_t n,int c) { memset(d,c,n); }
EXPORT void __aeabi_memclr(void *d,size_t n) { memset(d,0,n); }
EXPORT void __aeabi_memclr4(void *d,size_t n) { memset(d,0,n); }
EXPORT void __aeabi_memclr8(void *d,size_t n) { memset(d,0,n); }
