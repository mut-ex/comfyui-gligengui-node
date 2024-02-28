import requests
import json
import re

class LazyDecoder(json.JSONDecoder):

    def decode(self, s, **kwargs):
        regex_replacements = [
            (re.compile(r'([^\\])\\([^\\])'), r'\1\\\\\2'),
            (re.compile(r',(\s*])'), r'\1'),
        ]
        for regex, replacement in regex_replacements:
            s = regex.sub(replacement, s)
        return super().decode(s, **kwargs)


class GLIGEN_GUI:

    def __init__(self):
        self.updateTick = 1

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "clip": ("CLIP", ),
                "gligen_textbox_model": ("GLIGEN", ),
            }
        }

    RETURN_TYPES = ("CONDITIONING", )
    FUNCTION = "append"

    CATEGORY = "conditioning/gligen"

    def IS_CHANGED(self):
        self.updateTick += 1
        return hex(self.updateTick)

    def _gligen_apply(self,
                        conditioning_to,
                        clip,
                        gligen_textbox_model,
                        rect):
        c = []
        text = rect['caption']
        height = rect['y2']-rect['y1']
        width = rect['x2'] - rect['x1']
        x = rect['x1']
        y = rect['y1']
        cond, cond_pooled = clip.encode_from_tokens(clip.tokenize(text), return_pooled=True)
        for t in conditioning_to:
            n = [t[0], t[1].copy()]
            position_params = [
                (cond_pooled, height // 8, width // 8, y // 8, x // 8)
            ]
            prev = []
            if "gligen" in n[1]:
                prev = n[1]['gligen'][2]

            n[1]['gligen'] = ("position",
                                gligen_textbox_model,
                                prev + position_params)
            c.append(n)
        return c

    def append(self, clip, gligen_textbox_model):
        res = requests.get('http://localhost:5000/input_args')
        if res.status_code == 200:
            res = json.loads(res.text, cls=LazyDecoder)
            print("Fetched data from GLIGEN GUI: ")
        boxes = res["boxes"]
        positive_conditioning = res["positive_prompt"]
        
        tokens = clip.tokenize(positive_conditioning)
        cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)

        c_to = [[cond, {"pooled_output": pooled}]]
        for rect in boxes:
            c_to = self._gligen_apply(c_to,
                                        clip,
                                        gligen_textbox_model,
                                       rect)
        c = c_to

        return (c, )

NODE_CLASS_MAPPINGS = {
    "GLIGEN_GUI": GLIGEN_GUI,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GLIGEN_GUI": "GLIGEN GUI",
}
