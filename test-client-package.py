"""Verify client-mode feature flags and projection-mode exclusion in the engine."""
from pathlib import Path
import json,os,subprocess,tempfile
ROOT=Path(__file__).resolve().parent
OUTPUT=ROOT/'dist'
with tempfile.TemporaryDirectory(dir=ROOT/'host-test') as directory:
 root=Path(directory)
 for name in ['system/wifi','system/onebin/lx2pe_kr','data/hmgapi/settings','data/hmgapi/mods']:
  (root/name).mkdir(parents=True)
 (root/'system/wifi/bcmdhd.ko').write_bytes(Path(os.environ['HMGAPI_TEST_STOCK']).read_bytes())
 features=''.join('-/system/etc/permissions/'+name+'.xml\n' for name in ['android.hardware.wifi','com.hkmc.software.wifihotspot'])
 (root/'system/onebin/lx2pe_kr/featurexml.cfg').write_text(features)
 (root/'props.txt').write_text('ro.board.platform=tcc803x\nro.mobis.onebindir=lx2pe_kr\n')
 (root/'settings.txt').write_text('global/wifi_on=0\n')
 env=dict(os.environ,HMGAPI_ROOT=str(root),HMGAPI_HOST='1',HMGAPI_PRODUCT=os.environ.get('HMGAPI_TEST_PRODUCT','LX2PE.KOR.0000.V039.001.260902'),HMGAPI_ONEBIN='lx2pe_kr')
 def engine(*args):
  return subprocess.run(['java','-cp',os.environ['HMGAPI_ENGINE_CLASSES'],'hmgapi.engine.Engine',*args],env=env,capture_output=True,text=True)
 for package in ['usb-wifi-rtl8822bu-0.1.7.zip','wifi-client-test-0.1.5.zip']:
  r=engine('install',str(OUTPUT/package));assert r.returncode==0,r.stdout+r.stderr
 print('PASS signed client-test and driver packages imported')
 old=root/'data/hmgapi/mods/wireless-phone-projection';old.mkdir()
 (old/'mod.json').write_text(json.dumps({'id':'wireless-phone-projection','version':'0.1.2','feature_flags':['android.hardware.wifi','com.hkmc.software.wifihotspot']}))
 r=engine('apply');assert r.returncode!=0 and 'conflict' in r.stdout.lower(),r.stdout+r.stderr
 print('PASS simultaneous projection and client-test modes refused')
 (old/'.disabled').touch()
 r=engine('apply');assert r.returncode==0,r.stdout+r.stderr
 for name in ['android.hardware.wifi','com.hkmc.software.wifihotspot']:
  assert (root/'system/etc/permissions'/f'{name}.xml').exists()
 assert (root/'settings.txt').read_text()=='global/wifi_on=0\n'
 print('PASS Wi-Fi settings flags retained without automatically enabling the client')
 (root/'data/hmgapi/mods/wifi-client-test/.disabled').touch();(old/'.disabled').unlink()
 r=engine('apply');assert r.returncode==0,r.stdout+r.stderr
 print('PASS projection-mode feature plan restored after disabling the client test')
