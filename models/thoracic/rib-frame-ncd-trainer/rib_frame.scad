// Rib frame for needle decompression and finger thoracostomy training
// Three-part print: two rails and three elliptical rib bars that press-fit
// into the rails. The space under the ribs stays open, so a needle or finger
// that clears the rib passes into free air ("pleural space"). Cover the top
// with 15-20 mm of foam, gelatin, or pork belly as the chest wall.
//
// Teaching geometry: ribs 14 mm wide with 16 mm intercostal gaps; insert
// over the superior border of the rib, as taught, to avoid the
// "neurovascular bundle" on each rib's inferior edge.
//
// Prints flat, no supports. PLA, 3 perimeters. part = "rail", "rib", "all".

$fn = 64;

part        = "all";
rib_len     = 130;
rib_w       = 14;    // ellipse width
rib_h       = 10;    // ellipse height
rib_pitch   = 30;    // center-to-center spacing -> 16 mm gap
n_ribs      = 3;
peg         = 8;     // square peg on rib ends
peg_len     = 12;
rail_l      = 100;
rail_w      = 15;
rail_h      = 30;
clear       = 0.4;   // press-fit clearance

module rib() {
    // elliptical bar with pegs; flat strip cut on the bottom for bed adhesion
    difference() {
        union() {
            rotate([-90, 0, 0])
                scale([rib_w / rib_h, 1, 1])
                    cylinder(d = rib_h, h = rib_len, center = false);
            for (y = [-peg_len + 0.1, rib_len - 0.1])
                translate([-peg/2, y, -peg/2]) cube([peg, peg_len, peg]);
        }
        translate([-rib_w, -peg_len - 1, -rib_h/2 - 10])
            cube([rib_w * 2, rib_len + 2 * peg_len + 2, 10 + 1.2]);
    }
}

module rail() {
    difference() {
        translate([-rail_l/2, -rail_w/2, 0]) cube([rail_l, rail_w, rail_h]);
        // peg slots, open at the top
        for (i = [0 : n_ribs - 1])
            translate([(i - (n_ribs - 1)/2) * rib_pitch - (peg + clear)/2,
                       -rail_w/2 - 1,
                       rail_h - peg - clear])
                cube([peg + clear, rail_w + 2, peg + clear + 1]);
    }
}

if (part == "rail") rail();
else if (part == "rib") rib();
else {
    // assembled preview / plate layout
    translate([0, 0, 0]) rail();
    translate([0, rib_len + 2 * peg_len + 10, 0]) rail();
    for (i = [0 : n_ribs - 1])
        translate([(i - (n_ribs - 1)/2) * rib_pitch, peg_len + 5, rib_h/2 + rail_h + 5])
            rib();
}
