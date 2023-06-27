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
    temp = iter(resources_in_compl)
    while True:
            try:
                
                chn = sess.channels[next(temp)]
                # if chn.current_limit == current_ranges[0]:
                #     chn.abort()

                
                #     chn.aperture_time = 5e-3
                #     chn.initiate()
                    
                
                print(f"change to {chn.current_limit}")
                # chn.current_limit_range = current_ranges[current_ranges.index(chn.current_limit_range)+1] # go to next current_limit_range
                chn.current_limit       = current_ranges[current_ranges.index(chn.current_limit_range)+1] # go to next current_limit
            except StopIteration:
                break
    
    if len(resources_in_compl) == 0:
        return None
    else:
        check_compliance(resources_in_compl, sess, current_ranges)
    
# def change_current_range():
#     """Change the current range of the device to the next higher range.

#     Returns:
#         bool: True if the current range was changed.
#     """
#     # Get the current range
#     current_range = nidcpower_session.current_limit

#     # Get the current ranges for the device
#     device_current_ranges = current_ranges[nidcpower_session.device_name]

#     # Get the index of the current range
#     current_range_index = device_current_ranges.index(current_range)

#     # Check if the current range is the highest range
#     if current_range_index == len(device_current_ranges) - 1:
#         return False

#     # Change the current range to the next higher range
#     nidcpower_session.current_limit = device_current_ranges[current_range_index + 1]
#     return True
