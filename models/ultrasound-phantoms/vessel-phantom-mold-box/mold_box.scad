// Ultrasound vessel phantom mold box
// Open-top box with V-notches on both end walls at three depths. Rest
// latex or surgical tubing in the notches, pour ballistic gelatin, and
// the result is a vascular access phantom with vessels at 10, 20, and
// 30 mm below the surface: superficial IV, deep IV, and central-line
// depth in one block. Tie tubing off water-filled for realistic
// compressibility testing (veins collapse, "arteries" filled stiffer).
//
// Gelatin recipe that scans well: 100 g gelatin + 900 mL water + 20 g
// flour per batch (flour sets echogenicity).
//
// PLA or PETG, 3 perimeters, no supports, prints upright as oriented.
// All dimensions mm.

$fn = 64;

box_x  = 120;   // length (tubing axis)
box_y  = 80;
box_z  = 50;
wall   = 3;
rim_z  = 45;    // pour level: fill to the lowest notch shoulder

// vessel lanes: [y offset, notch floor height] -> depth below pour line
lanes = [[-20, 35], [0, 25], [20, 15]];

module vnotch() {
    rotate([45, 0, 0]) cube([wall + 4, 9, 9], center = true);
}

difference() {
    translate([-box_x/2, -box_y/2, 0]) cube([box_x, box_y, box_z]);
    translate([-box_x/2 + wall, -box_y/2 + wall, wall])
        cube([box_x - 2*wall, box_y - 2*wall, box_z]);
    // notches through both end walls
    for (end = [-1, 1], l = lanes)
        translate([end * (box_x/2 - wall/2), l[0], l[1] + 6])
            rotate([0, 0, 90]) vnotch();
    // pour-level line engraved inside the long walls
    for (side = [-1, 1])
        translate([0, side * (box_y/2 - wall), rim_z - 10])
            cube([box_x - 30, 1.2, 0.8], center = true);
}
