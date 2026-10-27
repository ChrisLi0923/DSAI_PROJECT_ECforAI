"""Read-only validation of the prepared and frozen main protocol."""
from pathlib import Path
from .core import *
from .data import verify_data
from .workflow import source_hash,environment

def check(root):
    root=Path(root); frozen=read_json(root/'configs/protocol_freeze.json')
    config=read_json(root/'configs/main.json')
    assert digest(config)==frozen['config_sha256'],'Frozen configuration changed'
    assert source_hash()==frozen['source_sha256'],'Frozen implementation changed'
    assert verify_data(root/'data')==frozen['data_manifest'],'Frozen data changed'
    assert environment()['packages']==frozen['packages'],'Frozen environment changed'
    assert environment()['python']==frozen['python'],'Frozen Python version changed'
    assert config['mode']=='main'
    assert config['data']['pilot_n']==100
    assert len(config['search']['seeds'])==3
    assert set(SEEN).isdisjoint(WITHHELD)
    print('Frozen protocol, data and package verification passed.',flush=True)
    return config

if __name__=='__main__': check(Path(__file__).resolve().parents[1])
