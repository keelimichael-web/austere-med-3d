// Parametric cricothyrotomy trainer
// Half-shell larynx/trachea on a strap plate. Wear on forearm or neck of a
// role-player, or clamp to a table. Cover the open cricothyroid membrane
// window with layered tape, Press'n Seal, or a gelatin skin patch and cut.
//
// Prints flat, no supports. PLA or PETG, 3+ perimeters.
// All dimensions mm, loosely based on adult male airway anatomy.

$fn = 96;

// ---- parameters ----
plate_l       = 100;   // plate length (airway axis)
plate_w       = 55;    // plate width
plate_t       = 3;     // plate thickness
lumen_d       = 16;    // airway lumen diameter
trachea_d     = 22;    // tracheal ring outer diameter
cricoid_d     = 24;    // cricoid stands slightly proud (palpation landmark)
thyroid_d     = 26;    // thyroid cartilage widest point
thyroid_l     = 24;    // thyroid cartilage length
ctm_gap       = 8;     // cricothyroid membrane window (open, tape over this)
cricoid_l     = 7;     // cricoid ring height
ring_l        = 4.5;   // tracheal ring height
ring_gap      = 3.5;   // gap between tracheal rings
n_rings       = 4;
strap_w       = 28;    // strap slot length (fits 25 mm webbing/velcro)
strap_slot_t  = 4;

axis_z = plate_t;      // airway axis sits on the plate surface

// ---- helpers ----
module rounded_plate() {
    hull()
        for (x = [-1, 1], y = [-1, 1])
            translate([x * (plate_w/2 - 6), y * (plate_l/2 - 6), 0])
                cylinder(r = 6, h = plate_t);
}

// one half-shell band of the airway: y0..y1 along the axis, outer diameter d
module band(y0, y1, d) {
    intersection() {
        translate([0, y0, axis_z])
            rotate([-90, 0, 0])
                difference() {
                    cylinder(d = d, h = y1 - y0);
                    translate([0, 0, -1]) cylinder(d = lumen_d, h = y1 - y0 + 2);
                }
        // keep only the anterior half (above the plate)
        translate([-plate_w/2, -plate_l/2, axis_z - 0.01])
            cube([plate_w, plate_l, thyroid_d]);
    }
}

// ---- section layout, superior (thyroid) to inferior ----
y_start   = -plate_l/2 + 8;
thy_y0    = y_start;
thy_y1    = thy_y0 + thyroid_l;
cri_y0    = thy_y1 + ctm_gap;        // the window between these is the CTM
cri_y1    = cri_y0 + cricoid_l;

module airway() {
    band(thy_y0, thy_y1, thyroid_d);
    band(cri_y0, cri_y1, cricoid_d);
    for (i = [0 : n_rings - 1]) {
        r0 = cri_y1 + ring_gap + i * (ring_l + ring_gap);
        band(r0, r0 + ring_l, trachea_d);
    }
}

module strap_slots() {
    for (y = [-plate_l/2 + 20, plate_l/2 - 20], x = [-1, 1])
        translate([x * (plate_w/2 - 6), y, -1])
            hull()
                for (yy = [-1, 1])
                    translate([0, yy * (strap_w/2 - strap_slot_t/2), 0])
                        cylinder(d = strap_slot_t, h = plate_t + 2);
}

// ---- assembly ----
difference() {
    union() {
        rounded_plate();
        airway();
    }
    strap_slots();
    // superior thyroid notch (laryngeal prominence landmark)
    translate([0, thy_y0 - 0.5, axis_z + thyroid_d/2])
        rotate([0, 45, 0])
            cube([9, 12, 9], center = true);
}
