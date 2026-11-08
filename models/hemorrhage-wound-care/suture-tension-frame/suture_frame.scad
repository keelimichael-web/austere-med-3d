// Suture practice tension frame
// Two-part clamping frame that stretches any skin analog flat: nitrile
// glove rubber, silicone sheet, inner tube, thin foam, or chicken skin.
// Membrane stretches over the post frame; the top frame presses on and
// the cone-tipped posts lock it. Replace the membrane in seconds.
//
// Print part="base" and part="top", one each. PLA, 3 perimeters, no
// supports. All dimensions mm.

$fn = 64;

part = "all";   // "base", "top", "all"

frame_x = 110;
frame_y = 80;
band    = 14;
base_t  = 6;
top_t   = 5;
post_d  = 5;
post_h  = 11;
hole_d  = 6.6;

module ring(t) {
    linear_extrude(t)
        difference() {
            offset(r = 6) square([frame_x - 12, frame_y - 12], center = true);
            offset(r = 6) square([frame_x - 12 - 2*band, frame_y - 12 - 2*band], center = true);
        }
}

// post / hole positions: corners + long-side midpoints
pos = [[-1, -1], [-1, 1], [1, -1], [1, 1], [0, -1], [0, 1]];

module base() {
    ring(base_t);
    for (p = pos)
        translate([p[0] * (frame_x/2 - band/2), p[1] * (frame_y/2 - band/2), base_t]) {
            cylinder(d = post_d, h = post_h - 2);
            translate([0, 0, post_h - 2]) cylinder(d1 = post_d, d2 = 2, h = 2);
        }
}

module top() {
    difference() {
        ring(top_t);
        for (p = pos)
            translate([p[0] * (frame_x/2 - band/2), p[1] * (frame_y/2 - band/2), -1])
                cylinder(d = hole_d, h = top_t + 2);
    }
}

if (part == "base") base();
else if (part == "top") top();
else {
    base();
    translate([0, 0, base_t + post_h + 6]) top();
}
