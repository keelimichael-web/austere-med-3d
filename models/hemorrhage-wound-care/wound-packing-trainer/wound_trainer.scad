// Wound packing trainer
// Two identical halves dowel-pinned together around a deep wound tract:
// narrow entry, wide internal pocket, lateral extension, and a bleeder
// channel that accepts surgical tubing from an IV bag for a bleeding model.
// Split design means no supports, and the halves open for cleaning and
// for relining the tract with gelatin if more fidelity is wanted.
//
// Print part="half" twice and part="peg" four times. PLA, 2 perimeters,
// 10% infill. Halves print lying on the split face.
//
// All dimensions mm. Stylized training geometry, not an anatomic replica.

$fn = 64;

part = "all";   // "half", "peg", "all"

block_x = 120;
block_y = 40;   // one half; assembled block is 80 deep
block_z = 50;

peg_d    = 6;
peg_len  = 22;
hole_d   = 6.4;

// wound tract, modeled on the split plane (y = 0)
module tract() {
    // entry: narrow ellipse at the surface
    translate([0, 0, block_z - 2]) scale([1.3, 0.6, 1]) sphere(r = 13);
    // throat
    translate([0, 0, 38]) sphere(r = 10);
    // main pocket, wider than the entry (teaches packing into dead space)
    translate([0, 0, 26]) sphere(r = 17);
    // lateral extension pocket
    translate([24, 0, 24]) sphere(r = 11);
    // bleeder channel: fits 6 mm OD surgical tubing, exits the end face
    translate([-block_x/2 - 1, 0, 24]) rotate([0, 90, 0]) cylinder(d = 7, h = block_x/2 - 15);
}

module half() {
    difference() {
        translate([-block_x/2, 0, 0]) cube([block_x, block_y, block_z]);
        tract();
        // dowel holes on the split face
        for (x = [-48, 48], z = [12, 40])
            translate([x, -1, z]) rotate([-90, 0, 0]) cylinder(d = hole_d, h = peg_len/2 + 1.5);
    }
}

module peg() {
    cylinder(d = peg_d, h = peg_len - 1);
    translate([0, 0, peg_len - 1]) cylinder(d1 = peg_d, d2 = peg_d - 2, h = 1);
}

if (part == "half") rotate([90, 0, 0]) translate([0, -block_y, 0]) half();
else if (part == "peg") peg();
else {
    // assembled preview, halves slightly apart
    translate([0, 3, 0]) half();
    translate([0, -3, 0]) mirror([0, 1, 0]) half();
    for (x = [-48, 48])
        translate([x, 0, 58]) rotate([90, 0, 0]) translate([0, 0, -peg_len/2]) peg();
}
