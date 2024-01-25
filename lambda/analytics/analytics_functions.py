import json

from shared.apiutils.router import path_pattern_matcher, BeaconError


@path_pattern_matcher("v_frequencies", "post")
def variant_frequencies(event):
    body_dict = json.loads(event.get("body"))
    
    return {"success": True}

