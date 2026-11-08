// IO (intraosseous) trainer, proximal tibia block
// Rounded "tibial plateau" block with a tuberosity bump and an insertion
// dimple at the classic proximal-medial site. The slicer provides the bone
// feel: perimeters are the cortex, infill is the cancellous bone.
//
// Print notes: 2 perimeters, 8-12% gyroid infill, 0 top layers over the
// insertion zone if your slicer supports modifier regions (optional).
// Each block survives many insertions; reprint when chewed up.
// Drive the needle anywhere on the upper medial surface.
//
// All dimensions mm. Stylized training geometry, not an anatomic replica.

$fn = 80;

block_w = 70;   // medial-lateral
block_d = 55;   // anterior-posterior
block_h = 48;

module body() {
    intersection() {
        hull() {
            // plateau (top) corners
            for (x = [-1, 1], y = [-1, 1])
                translate([x * (block_w/2 - 14), y * (block_d/2 - 14), block_h - 14])
                    sphere(r = 14);
            // base corners
            for (x = [-1, 1], y = [-1, 1])
                translate([x * (block_w/2 - 5) * 0.8, y * (block_d/2 - 5) * 0.8, 5])
                    sphere(r = 5);
        }
        // flat bottom
        translate([-block_w/2, -block_d/2, 0]) cube([block_w, block_d, block_h + 20]);
    }
}

union() {
    body();
    // tibial tuberosity, anterior face, below the plateau (palpation landmark)
    translate([0, block_d/2 + 2, block_h - 18]) sphere(r = 10);
}
