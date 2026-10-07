#!/usr/bin/env python3
"""Install the verified ARM GCC 14/newlib toolchain into the repository cache."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
PACKAGES = [
    ('pool/main/g/gcc-arm-none-eabi/gcc-arm-none-eabi_14.2.rel1-1_amd64.deb','99252fdda02ad134e8c3c344d3c843f7aa5c0d006e92a5b3d53daf4bd935b5d3'),
    ('pool/main/n/newlib/libnewlib-arm-none-eabi_4.5.0.20241231-1_all.deb','b444760d62896f03db89d6db94936929f300b72445763557fa94da32b7732f51'),
    ('pool/main/n/newlib/libnewlib-dev_4.5.0.20241231-1_all.deb','feb2ed49a464b0346e42c3506088a41025273bff5f8e6bc5777afeac3704b3c1'),
]

def main():
    cache = ROOT/'.local/arm-gcc-downloads';cache.mkdir(parents=True,exist_ok=True)
    install = ROOT/'.local/arm-gcc'
    verified = []
    for relative,digest in PACKAGES:
        name = relative.rsplit('/',1)[1]; path = cache/name
        if not path.exists():
            # Reuse the epoch-encoded filename produced by apt-get download.
            existing = next((p for p in cache.glob('*.deb') if hashlib.sha256(p.read_bytes()).hexdigest()==digest),None)
            if existing: path = existing
            else:
                temp = cache/(name+'.partial')
                with urllib.request.urlopen('https://deb.debian.org/debian/'+relative,timeout=60) as response,temp.open('wb') as out:
                    shutil.copyfileobj(response,out)
                if hashlib.sha256(temp.read_bytes()).hexdigest()!=digest:
                    temp.unlink();raise ValueError('Downloaded compiler checksum mismatch')
                temp.rename(path)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest: raise ValueError(f'Checksum mismatch: {path.name}')
        verified.append(path)
    compiler = install/'usr/bin/arm-none-eabi-gcc'
    if not compiler.exists():
        install.mkdir(parents=True,exist_ok=True)
        for path in verified: subprocess.run(['dpkg-deb','-x',str(path),str(install)],check=True)
    for name,target in [('lib','newlib'),('include','../../include/newlib')]:
        link = install/'usr/lib/arm-none-eabi'/name
        if not link.exists(): link.symlink_to(target)
    version = subprocess.check_output([str(compiler),'-dumpfullversion'],text=True).strip()
    if version!='14.2.1': raise ValueError(f'Unexpected ARM compiler: {version}')
    print('Verified ARM GCC '+version+' and newlib; cache: '+str(install))

if __name__ == '__main__': main()
