# Resistance Medicine Printworks

A living repository of 3D-printable training aids for medical interventions, maintained by contributors to *Resistance Medicine: A Medical Annex to the Resistance Operating Concept* (SOMA MSIW working group) and open to the wider austere medicine community.

**Browse the catalog:** https://keelimichael-web.github.io/resistance-medicine-printworks/

The catalog page rebuilds automatically every time a model is added to this repository. Add files, and the site updates itself.

## In memory of Ian Daniel

This repository is dedicated to Ian Daniel. Ian was a nurse practitioner a few credits short of board certification in emergency medicine. His goal was to become the kind of emergency provider who could bring real care to people in hard places, with whatever was on hand. That is the same provider these training aids exist to build. See [DEDICATION.md](DEDICATION.md).

## What belongs here

Printable models and build guides that help medics train real interventions:

- Airway: cricothyrotomy trainers, laryngoscopy aids
- Vascular access: IO trainers, IV arms
- Thoracic: rib sections for needle decompression and chest tube practice
- Ultrasound phantoms: nerve block and vascular access phantoms (prints plus gelatin recipes)
- Anything else that trains hands for a medical intervention

Equipment and device files are welcome where licensing allows, but the core of this collection is **training aids**: things that teach hands, not things that go in patients.

## How to add a model

1. Fork or branch this repository.
2. Create a folder under the right category: `models/<category>/<your-model-name>/`
3. Drop in the files (`.stl`, `.3mf`, `.step`, `.obj`, `.scad`, `.gcode`).
4. Add an `info.yml` next to them (optional but strongly encouraged, see [CONTRIBUTING.md](CONTRIBUTING.md)).
5. Open a pull request, or push directly if you have access.

The site rebuilds on its own within a couple of minutes of merge.

Links to models hosted elsewhere (Thingiverse, NIH 3D, personal sites) go in [`catalog/external.yml`](catalog/external.yml) and show up on the same page.

## License

Unless a model's `info.yml` says otherwise, contributions are shared under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Contributors keep ownership of their designs. External links remain under their original licenses.

## Safety

These are training aids. Nothing in this repository is a medical device, and nothing here is intended for clinical use on patients.
