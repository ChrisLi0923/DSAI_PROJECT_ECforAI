import pytest
from robust_prompt.gpu_select import GPU, choose_gpu

def gpu(index, free=21000, utilization=0, processes=0):
    return GPU(index, f'GPU-test-{index}', 'NVIDIA GeForce RTX 4090', 24564, free, utilization, processes)

def test_idle_considers_all_devices():
    selected = choose_gpu([gpu(2, processes=1), gpu(1), gpu(0, free=18000)])
    assert selected.index == 1

def test_idle_rejects_busy_compute_or_graphics():
    assert choose_gpu([gpu(0, processes=1), gpu(1, utilization=90)]) is None

def test_shared_can_choose_busy_gpu_with_headroom():
    selected = choose_gpu([gpu(0, free=15000, utilization=5, processes=1),
                           gpu(1, utilization=70, processes=1), gpu(2, utilization=30, processes=1)], 'shared')
    assert selected.index == 2

def test_shared_prefers_unused_device():
    assert choose_gpu([gpu(0, utilization=0, processes=1), gpu(1, utilization=5)], 'shared').index == 1

def test_shared_requires_two_gib_extra_headroom():
    assert choose_gpu([gpu(0, free=16*1024-1)], 'shared') is None
    assert choose_gpu([gpu(0, free=16*1024)], 'shared') is not None
    assert choose_gpu([gpu(0, free=14*1024)], 'idle') is not None

def test_requested_index_or_uuid_is_respected():
    devices = [gpu(0), gpu(1)]
    assert choose_gpu(devices, requested='1').index == 1
    assert choose_gpu(devices, requested='GPU-test-0').index == 0
    assert choose_gpu([gpu(0), gpu(1, processes=1)], requested='1') is None
    with pytest.raises(ValueError): choose_gpu(devices, requested='99')

def test_no_devices_or_no_capacity():
    assert choose_gpu([]) is None
    assert choose_gpu([gpu(0, free=1000)], 'shared') is None
