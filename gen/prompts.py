STUDIO = "modern TV news studio, dark blue video walls blurred in background, broadcast footage, studio lighting"
FACE = "facing the camera, looking straight into the camera, lips closed"
P = {
 "paige": f"RAW photo, television news anchor, woman in her mid 30s with long dark brown hair, red blazer, sitting at a news desk, {FACE}, calm expression, medium close-up, {STUDIO}",
 "cy": f"RAW photo, television news anchor, Black man in his 40s with short hair, navy suit, white shirt, green tie, sitting at a news desk, {FACE}, calm expression, medium close-up, {STUDIO}",
 "dee": f"RAW photo, television news reporter, man in his late 20s with curly ginger hair, dark green jacket, holding a microphone, standing outside a large modern data center building, {FACE}, medium close-up, overcast daylight, live broadcast footage",
 "sunny": f"RAW photo, television weather presenter, Indian woman in her 30s with black bob haircut, teal blouse, standing in a TV studio, {FACE}, slight smile, medium shot, plain dark blue studio wall behind her, broadcast footage, studio lighting",
 "mel": f"RAW photo, webcam video call, bald man in his 60s with round glasses, grey suit, purple tie, sitting in a home office, bookshelves behind him, {FACE}, serious expression, medium close-up, natural window light",
 "studio": "RAW photo, wide shot of an empty modern television news studio at night, curved glass anchor desk, huge dark blue video walls, ceiling studio lights, broadcast cameras, cinematic, sharp focus",
 "servers": "RAW photo, long aisle of server racks in a data center, rows of blinking green and blue LED lights, cold aisle, symmetrical, sharp focus",
 "dcext": "RAW photo, exterior of a large windowless modern data center building, security fence, overcast sky, wide shot, documentary photography",
 "office": "RAW photo, dark open-plan office at night, empty desk with computer monitors glowing with lines of code, nobody there, shallow depth of field",
 "paged": "RAW photo, tired software engineer in a hoodie woken up at night, sitting up in bed looking at a glowing smartphone, dark bedroom, blue light on face, documentary photography",
 "sat": "satellite photo from space, swirling white storm clouds over dark blue ocean and green coastline, weather satellite view, high detail",
}
DESC = {
 "paige": "a woman in her mid 30s with long dark brown hair",
 "cy": "a Black man in his 40s with short hair",
 "dee": "a man in his late 20s with curly ginger hair and a short ginger beard",
 "sunny": "an Indian woman in her 30s with a black bob haircut",
 "mel": "a bald man in his 60s with round glasses",
}
VIS = {
 "small": "lips slightly parted, mouth slightly open, speaking",
 "open": "mouth open, talking, teeth visible, saying ah",
 "ee": "mouth wide, talking, showing upper teeth, saying ee",
 "oo": "lips rounded and pushed forward, mouth small and round, saying ooh",
}
P["cy2"] = f"RAW photo, television news anchor, Black man in his 40s with short hair, navy suit, white shirt, green tie, sitting at a news desk, front view, centered, {FACE}, calm expression, medium close-up, {STUDIO}"
P["cy"] = P["cy2"]
P["cy"] = f"RAW photo, television news anchor, Black man in his 40s with short hair, white shirt, green tie, sitting at a news desk, front view, {FACE}, calm expression, medium close-up, newsroom with monitors blurred in background, broadcast footage, studio lighting"
# second-round B-roll, to fix mismatches noticed after the first export: the establishing shot should look like the building
# behind the reporter, the paged engineer should be holding a phone, and the office should be dark
P["dcext2"] = "RAW photo, modern data center campus, large building with glass facade and concrete columns, overcast daylight, wide shot, documentary photography"
P["paged2"] = "RAW photo, tired software engineer in a hoodie sitting up in bed at night, holding a glowing smartphone in his hand, looking at the phone screen, dark bedroom, blue light on face, documentary photography"
P["office2"] = "RAW photo, dark empty open-plan office at night, lights off, rows of desks, computer monitors glowing with code in the darkness, moody blue light, shallow depth of field"
