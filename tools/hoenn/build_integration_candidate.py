"""Build the integration candidate without replacing the validated alpha release."""
import argparse
from pathlib import Path

import package_playable
from prepare_extra_gyms import PRIOR, LAYER


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    # The release packager keeps its published 64-layer contract. This separate
    # entry point builds all candidate layers and checks their source hashes.
    if (args.source / '.journey-coastal-closures').exists():
        from prepare_coastal_closures import PRIOR as current_prior, LAYER as current_layer
        package_playable.LAYERS = current_prior + [current_layer]
    elif (args.source / '.journey-sevii-integrated-piers').exists():
        from prepare_sevii_integrated_piers import PRIOR as current_prior, LAYER as current_layer
        package_playable.LAYERS = current_prior + [current_layer]
    elif (args.source / '.journey-dewford-coast-safety').exists():
        from prepare_dewford_coast_safety import PRIOR as current_prior, LAYER as current_layer
        package_playable.LAYERS = current_prior + [current_layer]
    else:
        package_playable.LAYERS = PRIOR + [LAYER]
    package_playable.build(args.source, args.jobs)
    print('Integration candidate built; final release validation is still required.')


if __name__ == '__main__':
    main()
