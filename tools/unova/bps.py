from pathlib import Path
import struct,zlib,hashlib,json,sys
def apply(patch, source):
 if patch[:4]!=b'BPS1':raise ValueError('Not BPS')
 crcs=struct.unpack('<III',patch[-12:])
 if zlib.crc32(patch[:-4])!=crcs[2]:raise ValueError('Patch CRC mismatch')
 if zlib.crc32(source)!=crcs[0]:raise ValueError(f'Source CRC mismatch: {zlib.crc32(source):08x}')
 cursor=4
 end=len(patch)-12
 def number():
  nonlocal cursor
  value=0;shift=1
  for _ in range(10):
   if cursor>=end:raise ValueError('Truncated BPS')
   b=patch[cursor];cursor+=1;value+=(b&127)*shift
   if b&128:return value
   shift<<=7;value+=shift
  raise ValueError('Oversized integer')
 def signed():
  value=number();return -(value>>1) if value&1 else value>>1
 source_size,target_size,meta_size=number(),number(),number()
 if source_size!=len(source) or target_size>32*1024*1024:raise ValueError('Wrong sizes')
 metadata=patch[cursor:cursor+meta_size];cursor+=meta_size
 target=bytearray();src_rel=dst_rel=0;actions=[0]*4
 while len(target)<target_size:
  command=number();action=command&3;length=(command>>2)+1
  if length>target_size-len(target):raise ValueError('Output overflow')
  actions[action]+=length
  if action==0:
   start=len(target)
   if start+length>len(source):raise ValueError('SourceRead overflow')
   target.extend(source[start:start+length])
  elif action==1:
   if cursor+length>end:raise ValueError('TargetRead overflow')
   target.extend(patch[cursor:cursor+length]);cursor+=length
  elif action==2:
   src_rel+=signed()
   if src_rel<0 or src_rel+length>len(source):raise ValueError('SourceCopy overflow')
   target.extend(source[src_rel:src_rel+length]);src_rel+=length
  else:
   dst_rel+=signed()
   if dst_rel<0 or dst_rel>=len(target):raise ValueError('TargetCopy overflow')
   for _ in range(length):target.append(target[dst_rel]);dst_rel+=1
 if cursor!=end or zlib.crc32(target)!=crcs[1]:raise ValueError('Output CRC mismatch')
 return bytes(target)
