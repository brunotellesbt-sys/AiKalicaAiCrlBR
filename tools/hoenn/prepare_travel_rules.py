"""One saved Mach Bike receipt across both regions; no following Pokemon."""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_family import LAYERS_BEFORE


def prepare(source):
    source = Path(source)
    marker = source / '.journey-travel-rules'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS_BEFORE + ['family']:
        expected.update(json.loads((source / f'.journey-{layer}').read_text())['prepared_sha256'])
    outputs, inputs, originals = {}, {}, {}

    def read(path):
        if path in outputs: return outputs[path]
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        if path in acquired['sha256']: inputs[path] = acquired['sha256'][path]
        return raw

    def replace(path, anchor, value):
        raw = read(path)
        if path not in originals: originals[path] = hashlib.sha256(raw).hexdigest()
        assert raw.decode().count(anchor) == 1, (path, anchor)
        outputs[path] = raw.decode().replace(anchor, value).encode()

    replace('include/config/overworld.h', '#define OW_FOLLOWERS_ENABLED           TRUE', '#define OW_FOLLOWERS_ENABLED           FALSE')
    replace('include/constants/vars.h', '#define VAR_UNUSED_0x40FB', '#define VAR_JOURNEY_MACH_BIKE_RECEIVED 0x40FB\n#define VAR_UNUSED_0x40FB')
    path = 'data/scripts/journey_family.inc'
    raw = read(path); originals[path] = hashlib.sha256(raw).hexdigest()
    outputs[path] = raw + b'''
Journey_TravellingBikeOwned::
\tcheckitem ITEM_MACH_BIKE
\tgoto_if_eq VAR_RESULT, TRUE, Journey_TravellingBikeRecord
\tcheckpcitem ITEM_MACH_BIKE, 1
\tgoto_if_eq VAR_RESULT, TRUE, Journey_TravellingBikeRecord
\tgoto_if_eq VAR_JOURNEY_MACH_BIKE_RECEIVED, 1, Journey_TravellingBikeRecord
\tsetvar VAR_RESULT, FALSE
\treturn
Journey_TravellingBikeRecord::
\tsetvar VAR_JOURNEY_MACH_BIKE_RECEIVED, 1
\tsetvar VAR_RESULT, TRUE
\treturn
'''
    path = 'data/maps/MauvilleCity_BikeShop/scripts.inc'
    replace(path, '\tcheckitem ITEM_MACH_BIKE\n\tgoto_if_eq VAR_RESULT, TRUE, MauvilleCity_BikeShop_EventScript_KeepBike', '\tcall Journey_TravellingBikeOwned\n\tgoto_if_eq VAR_RESULT, TRUE, MauvilleCity_BikeShop_EventScript_KeepBike')
    # A failed gift must not permanently set the receipt and block retries.
    replace(path, 'MauvilleCity_BikeShop_EventScript_YesFar::\n\tsetflag FLAG_RECEIVED_BIKE\n', 'MauvilleCity_BikeShop_EventScript_YesFar::\n')
    replace(path, 'MauvilleCity_BikeShop_EventScript_GetMachBike::\n', 'MauvilleCity_BikeShop_EventScript_GetMachBike::\n\tcall Journey_TravellingBikeOwned\n\tgoto_if_eq VAR_RESULT, TRUE, MauvilleCity_BikeShop_EventScript_KeepBike\n')
    replace(path, 'MauvilleCity_BikeShop_EventScript_GetAcroBike::\n\tmsgbox MauvilleCity_BikeShop_Text_ChoseAcroBike, MSGBOX_DEFAULT\n\tgiveitem ITEM_MACH_BIKE\n\tgoto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull\n\tgoto MauvilleCity_BikeShop_EventScript_ComeBackToSwitchBikes\n\tend', 'MauvilleCity_BikeShop_EventScript_GetAcroBike::\n\tgoto MauvilleCity_BikeShop_EventScript_GetMachBike\n\tend')
    replace(path, '\tgoto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull\n\tgoto MauvilleCity_BikeShop_EventScript_ComeBackToSwitchBikes', '\tgoto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull\n\tsetflag FLAG_RECEIVED_BIKE\n\tsetvar VAR_JOURNEY_MACH_BIKE_RECEIVED, 1\n\tgoto MauvilleCity_BikeShop_EventScript_ComeBackToSwitchBikes')
    path = 'data/maps/CeruleanCity_BikeShop_Frlg/scripts.inc'
    replace(path, '\tcheckitem ITEM_MACH_BIKE\n', '\tcall Journey_TravellingBikeOwned\n')
    replace(path, 'CeruleanCity_BikeShop_EventScript_ExchangeBikeVoucher::\n', 'CeruleanCity_BikeShop_EventScript_ExchangeBikeVoucher::\n\tcall Journey_TravellingBikeOwned\n\tgoto_if_eq VAR_RESULT, TRUE, CeruleanCity_BikeShop_EventScript_AlreadyGotBicycle\n\tcheckitemspace ITEM_MACH_BIKE\n\tgoto_if_eq VAR_RESULT, FALSE, CeruleanCity_BikeShop_EventScript_NoRoomForBicycle\n')
    replace(path, '\tsetflag FLAG_GOT_BICYCLE\n\tadditem ITEM_MACH_BIKE\n\tremoveitem ITEM_BIKE_VOUCHER', '\tadditem ITEM_MACH_BIKE\n\tgoto_if_eq VAR_RESULT, FALSE, CeruleanCity_BikeShop_EventScript_NoRoomForBicycle\n\tsetflag FLAG_GOT_BICYCLE\n\tsetvar VAR_JOURNEY_MACH_BIKE_RECEIVED, 1\n\tremoveitem ITEM_BIKE_VOUCHER')
    replace(path, 'for a BICYCLE.', 'for a MACH BIKE.')
    report = dict(status='single_shared_mach_bike_no_followers_candidate', source_commit=PIN,
        following_pokemon_enabled=False, npc_followers_preserved=True, only_obtainable_bike='ITEM_MACH_BIKE',
        shared_receipt_var=0x40FB, both_supplier_orders_supported=True, failed_bag_delivery_can_retry=True,
        key_items_in_pc_do_not_duplicate=True, requires_new_save=True, full_story_validated=False,
        input_sha256=inputs, original_sha256=originals,
        prepared_sha256={p: hashlib.sha256(v).hexdigest() for p, v in outputs.items()})
    for path, raw in outputs.items(): (source / path).write_bytes(raw)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(p.parse_args().source), indent=2))
