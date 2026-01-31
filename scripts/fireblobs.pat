// scripts/fireblobs.pbb

/// sum
///   mul
///     $F80
///     mul
///       2
///       clamp: min=0.0, max=0.5
///         pulser
///           maxcount=10
///           interval=0.5
///           timeshape=triangle
///           spaceshape=sine
///           pos=randflat: 0, 1
///           width=0.2
///           duration=3
///   mul
///     $822
///     mul
///       2
///       clamp: min=0.0, max=0.5
///         pulser
///           maxcount=10
///           interval=0.4
///           timeshape=triangle
///           spaceshape=sine
///           pos=randflat: 0, 1
///           width=0.2
///           duration=4
/// 

var clock = 0   // seconds

var pulser_22_live = array(10)
var pulser_22_birth = array(10)
var pulser_22_livecount = 0
var pulser_22_nextstart = 0
var pulser_22_arg_pos = array(10)
var pulser_8_live = array(10)
var pulser_8_birth = array(10)
var pulser_8_livecount = 0
var pulser_8_nextstart = 0
var pulser_8_arg_pos = array(10)
// stanza buffers:
var pulser_22_vector = array(pixelCount)
var pulser_8_vector = array(pixelCount)
var sum_0_vector_r = array(pixelCount)
var sum_0_vector_g = array(pixelCount)
var sum_0_vector_b = array(pixelCount)

// startup calculations:

export function beforeRender(delta) {
  clock += (delta / 1000)
  for (var ix=0; ix<pixelCount; ix++) {
    pulser_22_vector[ix] = (0)
  }
  if (clock >= pulser_22_nextstart && pulser_22_livecount < 10) {
    for (var px=0; px<10; px++) {
      if (!pulser_22_live[px]) { break }
    }
    if (px < 10) {
      pulser_22_live[px] = 1
      livecount += 1
      randflat_24_val_min = 0.0
      randflat_24_val_diff = (1.0-randflat_24_val_min)
      pulser_22_arg_pos[px] = (random(randflat_24_val_diff)+randflat_24_val_min)
      pulser_22_nextstart = clock + 0.4
      pulser_22_birth[px] = clock
    }
  }
  for (var px=0; px<10; px++) {
    if (!pulser_22_live[px]) { break }
    age = clock - pulser_22_birth[px]
    relage = age / 4.0
    if (relage > 1.0) {
      pulser_22_live[px] = 0
      livecount -= 1
      continue
    }
    timeval = triangle(relage)
    ppos = pulser_22_arg_pos[px]
    pwidth = 0.2
    minpos = max(0, pixelCount*(ppos-pwidth/2))
    maxpos = min(pixelCount, pixelCount*(ppos+pwidth/2))
    for (var ix=minpos; ix<maxpos; ix++) {
      relpos = ((ix/pixelCount)-(ppos-pwidth/2)) / pwidth
      spaceval = sin(relpos*PI)
      pulser_22_vector[ix] += (timeval * spaceval)
    }
  }
  for (var ix=0; ix<pixelCount; ix++) {
    pulser_8_vector[ix] = (0)
  }
  if (clock >= pulser_8_nextstart && pulser_8_livecount < 10) {
    for (var px=0; px<10; px++) {
      if (!pulser_8_live[px]) { break }
    }
    if (px < 10) {
      pulser_8_live[px] = 1
      livecount += 1
      randflat_10_val_min = 0.0
      randflat_10_val_diff = (1.0-randflat_10_val_min)
      pulser_8_arg_pos[px] = (random(randflat_10_val_diff)+randflat_10_val_min)
      pulser_8_nextstart = clock + 0.5
      pulser_8_birth[px] = clock
    }
  }
  for (var px=0; px<10; px++) {
    if (!pulser_8_live[px]) { break }
    age = clock - pulser_8_birth[px]
    relage = age / 3.0
    if (relage > 1.0) {
      pulser_8_live[px] = 0
      livecount -= 1
      continue
    }
    timeval = triangle(relage)
    ppos = pulser_8_arg_pos[px]
    pwidth = 0.2
    minpos = max(0, pixelCount*(ppos-pwidth/2))
    maxpos = min(pixelCount, pixelCount*(ppos+pwidth/2))
    for (var ix=minpos; ix<maxpos; ix++) {
      relpos = ((ix/pixelCount)-(ppos-pwidth/2)) / pwidth
      spaceval = sin(relpos*PI)
      pulser_8_vector[ix] += (timeval * spaceval)
    }
  }
  for (var ix=0; ix<pixelCount; ix++) {
    var mul_1_val_common = (2.0 * clamp(pulser_8_vector[ix], 0.0, 0.5))  // for sum_0
    var mul_15_val_common = (2.0 * clamp(pulser_22_vector[ix], 0.0, 0.5))  // for sum_0
    sum_0_vector_r[ix] = (((1.0 * mul_1_val_common) + (0.5333333333333333 * mul_15_val_common)))
    sum_0_vector_g[ix] = (((0.5333333333333333 * mul_1_val_common) + (0.13333333333333333 * mul_15_val_common)))
    sum_0_vector_b[ix] = (((0.0 * mul_1_val_common) + (0.13333333333333333 * mul_15_val_common)))
  }
}

export function render(index) {
  var valr = sum_0_vector_r[index]
  var valg = sum_0_vector_g[index]
  var valb = sum_0_vector_b[index]
  rgb(valr*valr, valg*valg, valb*valb)
}

