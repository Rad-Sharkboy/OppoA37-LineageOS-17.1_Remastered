#include <dlfcn.h>
#include <png.h>
#include <zlib.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec+t.tv_nsec*1e-9; }
#define FN(ret,name,args) static ret (*p_##name) args
FN(const char *,zlibVersion,(void));
FN(uLong,zlibCompileFlags,(void));
FN(uLong,compressBound,(uLong));
FN(int,compress2,(Bytef *,uLongf *,const Bytef *,uLong,int));
FN(int,uncompress,(Bytef *,uLongf *,const Bytef *,uLong));
FN(uLong,crc32,(uLong,const Bytef *,uInt));
FN(png_uint_32,png_access_version_number,(void));
FN(int,png_image_begin_read_from_memory,(png_imagep,png_const_voidp,size_t));
FN(int,png_image_finish_read,(png_imagep,png_const_colorp,void *,png_int_32,void *));
FN(int,png_image_write_to_memory,(png_imagep,void *,png_alloc_size_t *,int,const void *,png_int_32,const void *));
FN(void,png_image_free,(png_imagep));
static void require(int ok, const char *msg) { if (!ok) { fprintf(stderr,"FAIL %s\n",msg); exit(2); } }
static void *openlib(const char *dir,const char *lib) { char path[1024]; snprintf(path,sizeof path,"%s/%s",dir,lib); void *h=dlopen(path,RTLD_NOW|RTLD_GLOBAL); if(!h) fprintf(stderr,"%s\n",dlerror()); require(h!=NULL,path); return h; }
#define LOAD(h,name) do { *(void **)(&p_##name)=dlsym(h,#name); require(p_##name!=NULL,#name); } while(0)
static unsigned char *readfile(const char *path, size_t *size) { FILE *f=fopen(path,"rb"); require(f!=NULL,"open input"); fseek(f,0,SEEK_END); *size=ftell(f); rewind(f); unsigned char *p=malloc(*size); require(p&&fread(p,1,*size,f)==*size,"read input"); fclose(f); return p; }
static unsigned char *decode(const unsigned char *data,size_t n,size_t *bytes,png_uint_32 *w,png_uint_32 *h) { png_image im; memset(&im,0,sizeof im); im.version=PNG_IMAGE_VERSION; require(p_png_image_begin_read_from_memory(&im,data,n),"png begin"); im.format=PNG_FORMAT_RGBA; *bytes=PNG_IMAGE_SIZE(im); *w=im.width; *h=im.height; unsigned char *p=malloc(*bytes); require(p!=NULL,"pixels alloc"); require(p_png_image_finish_read(&im,NULL,p,0,NULL),im.message); p_png_image_free(&im); return p; }
static unsigned char *encode(const unsigned char *data,png_uint_32 w,png_uint_32 h,size_t *bytes) { png_image im; memset(&im,0,sizeof im); im.version=PNG_IMAGE_VERSION; im.width=w; im.height=h; im.format=PNG_FORMAT_RGBA; png_alloc_size_t n=0; require(p_png_image_write_to_memory(&im,NULL,&n,0,data,0,NULL),"png write size"); unsigned char *p=malloc(n); require(p!=NULL,"png output alloc"); require(p_png_image_write_to_memory(&im,p,&n,0,data,0,NULL),im.message); *bytes=n; p_png_image_free(&im); return p; }
int main(int argc,char **argv) {
 setvbuf(stdout,NULL,_IONBF,0);
 require(argc==4,"usage: probe LIBDIR INPUT.png ITERATIONS"); int it=atoi(argv[3]); require(it>0,"iterations");
 fprintf(stderr,"load-z\n");
 void *z=openlib(argv[1],"libz.so");
 LOAD(z,zlibVersion); LOAD(z,zlibCompileFlags); LOAD(z,compressBound); LOAD(z,compress2); LOAD(z,uncompress); LOAD(z,crc32);
 fprintf(stderr,"load-png\n"); void *png=openlib(argv[1],"libpng.so");
 LOAD(png,png_access_version_number); LOAD(png,png_image_begin_read_from_memory); LOAD(png,png_image_finish_read); LOAD(png,png_image_write_to_memory); LOAD(png,png_image_free);
 fprintf(stderr,"decode-png\n"); size_t filebytes,bytes; png_uint_32 w,h; unsigned char *file=readfile(argv[2],&filebytes),*pixels=decode(file,filebytes,&bytes,&w,&h);
 printf("{\"zlib\":\"%s\",\"zflags\":%lu,\"png\":%u,\"w\":%u,\"h\":%u,\"rgba_bytes\":%zu,",p_zlibVersion(),p_zlibCompileFlags(),p_png_access_version_number(),w,h,bytes);
 size_t encodedbytes,roundbytes; png_uint_32 rw,rh; unsigned char *encoded=encode(pixels,w,h,&encodedbytes),*round=decode(encoded,encodedbytes,&roundbytes,&rw,&rh); require(w==rw&&h==rh&&bytes==roundbytes&&!memcmp(pixels,round,bytes),"png exact roundtrip"); free(round); free(encoded);
 png_image bad; memset(&bad,0,sizeof bad); bad.version=PNG_IMAGE_VERSION; unsigned char *broken=malloc(filebytes); require(broken!=NULL,"corrupt alloc"); memcpy(broken,file,filebytes); broken[29]^=1; int accepted=p_png_image_begin_read_from_memory(&bad,broken,filebytes); if(accepted) { bad.format=PNG_FORMAT_RGBA; unsigned char *tmp=malloc(PNG_IMAGE_SIZE(bad)); accepted=p_png_image_finish_read(&bad,NULL,tmp,0,NULL); free(tmp); } p_png_image_free(&bad); require(!accepted,"corrupt PNG rejected"); memset(&bad,0,sizeof bad); bad.version=PNG_IMAGE_VERSION; require(!p_png_image_begin_read_from_memory(&bad,file,20),"truncated PNG rejected"); p_png_image_free(&bad); free(broken);
 double start=now(); for(int i=0;i<it;i++){ size_t b; png_uint_32 x,y; unsigned char *p=decode(file,filebytes,&b,&x,&y); free(p); } double dec=(now()-start)*1000/it;
 start=now(); for(int i=0;i<it;i++){ size_t b; unsigned char *p=encode(pixels,w,h,&b); free(p); } double enc=(now()-start)*1000/it;
 uLongf cap=p_compressBound(bytes),compressed=cap; unsigned char *buf=malloc(cap),*raw=malloc(bytes); require(buf&&raw,"z buffers");
 printf("\"png_bytes\":%zu,\"decode_ms\":%.3f,\"encode_ms\":%.3f,",encodedbytes,dec,enc);
 for(int level=1;level<=6;level+=5) { compressed=cap; require(p_compress2(buf,&compressed,pixels,bytes,level)==Z_OK,"compress"); uLongf n=bytes; require(p_uncompress(raw,&n,buf,compressed)==Z_OK&&n==bytes&&!memcmp(raw,pixels,bytes),"z exact roundtrip"); buf[compressed-1]^=1; n=bytes; require(p_uncompress(raw,&n,buf,compressed)==Z_DATA_ERROR,"corrupt z rejected"); buf[compressed-1]^=1;
 start=now(); for(int i=0;i<it;i++){ n=cap; require(p_compress2(buf,&n,pixels,bytes,level)==Z_OK,"bench compress"); } double comp=(now()-start)*1000/it;
 start=now(); for(int i=0;i<it;i++){ n=bytes; require(p_uncompress(raw,&n,buf,compressed)==Z_OK,"bench inflate"); } double inf=(now()-start)*1000/it;
 printf("\"level%d_bytes\":%lu,\"level%d_compress_ms\":%.3f,\"level%d_inflate_ms\":%.3f,",level,compressed,level,comp,level,inf);
 }
 start=now(); volatile uLong crc=0; for(int i=0;i<it*20;i++)crc=p_crc32(0,pixels,bytes); double crc_ms=(now()-start)*1000/(it*20);
 printf("\"crc32\":%lu,\"crc_ms\":%.3f,\"checks\":\"roundtrip/corrupt/truncated OK\"}\n",crc,crc_ms);
 free(buf); free(raw); free(file); free(pixels); return 0;
}
