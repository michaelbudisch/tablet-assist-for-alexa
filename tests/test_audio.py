"""Exercise actual FFmpeg encode_mp3 implementation without external services."""
import sys,os,types,unittest,io,wave,math,struct,subprocess,tempfile,json
from pathlib import Path
from unittest.mock import patch
root=Path(__file__).resolve().parents[1]
try: import flask
except ImportError:
    class Flask:
        def __init__(self,*a,**k): self.config={}
        def get(self,*a,**k): return lambda fn:fn
        post=get
    sys.modules['flask']=types.SimpleNamespace(Flask=Flask,request=None,jsonify=None)
os.environ['PIPER_API_TOKEN']='test-only-'+'0'*32
sys.path.insert(0,str(root/'speechserver'))
import api
class Audio(unittest.TestCase):
    def test_encoder(self):
        buf=io.BytesIO()
        with wave.open(buf,'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000)
            w.writeframes(b''.join(struct.pack('<h',int(4000*math.sin(2*math.pi*220*i/24000))) for i in range(24000)))
        for profile in api.SOUND_PROFILES:
            for chime in [False,True]:
                with self.subTest(profile=profile,chime=chime):
                    data=api.encode_mp3(buf.getvalue(),chime,profile)
                    with tempfile.NamedTemporaryFile(suffix='.mp3') as fp:
                        fp.write(data);fp.flush()
                        r=subprocess.run(['ffprobe','-v','error','-select_streams','a:0','-show_entries','stream=codec_name,sample_rate,channels,bit_rate','-of','json',fp.name],capture_output=True,check=True)
                        s=json.loads(r.stdout)['streams'][0]
                        self.assertEqual((s['codec_name'],s['sample_rate'],s['channels'],s['bit_rate']),('mp3','24000',1,'48000'))
    def test_invalid_wav(self):
        with self.assertRaises(ValueError):api.encode_mp3(b'bad')
    def test_profiles(self):
        with self.assertRaises(ValueError):api.speech_filters(0,'invalid')
if __name__=='__main__': unittest.main()
