from myclasses import IVSweep

def extract_channel_vs_name_pairs(*lstivSweep:IVSweep):
    channel_vs_name_pair = {}
    for _sweep in lstivSweep:
        channel_vs_name_pair[_sweep.sweep.remarks] = _sweep.sweep.resource
        for bias in _sweep.biases:
            channel_vs_name_pair[bias.remarks] = bias.resource
        return channel_vs_name_pair