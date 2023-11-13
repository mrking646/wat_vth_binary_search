import nidcpower
import sys
sys.path.append("..")
from configs.config import current_ranges


current_range = current_ranges['PXIe-4163']

def check_compliance(sess: nidcpower.Session, ):
    """Check if the measured current is within the compliance range of the device.

    Returns:
        bool: True if the measured current is within the compliance range of the device.
    """
    # Get the measured current
    chn_resources = sess.get_channel_names("0:3")
    resources_in_compl = []
    for res in chn_resources:
        chn  = sess.channels[res]
        if chn.query_in_compliance():
            print("!!!!comp")
            resources_in_compl.append(res)
    chn_in_compl = iter(resources_in_compl)
    while True:
            try: 
                
                chn = sess.channels[next(chn_in_compl)]
                # if chn.current_limit == cuP"

                
                #     chn.aperture_time = 5e-3
                #     chn.initiate()
                    
                
                print(f"change to {chn.current_limit}")
                # chn.current_limit_range = current_ranges[current_ranges.index(chn.current_limit_range)+1] # go to next current_limit_range
                chn.current_limit = current_ranges[current_ranges.index(chn.current_limit_range)+1] # go to next current_limit
            except StopIteration:
                break
    
    if len(resources_in_compl) == 0:
        return None
    else:
        check_compliance(resources_in_compl, sess, current_ranges)
    

