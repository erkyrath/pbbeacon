// scripts/scrolls.pbb

/// gradient
///   stop: 0.0, $000
///   stop: 0.2, $000
///   stop: 0.3, $044
///   stop: 0.5, $0F8
///   stop: 0.7, $046
///   stop: 1.0, $046
///   mul
///     1.5
///     clamp: min=0.0, max=0.6666
///       pulser
///         maxcount=10
///         interval=0.4
///         timeshape=trapezoid
///         spaceshape=sine
///         pos=randflat: 0, 1
///         width=0.2
///         duration=4
/// 

var clock = 0   // seconds

var pulser_12_live = array(10)
var pulser_12_birth = array(10)
var pulser_12_livecount = 0
var pulser_12_nextstart = 0
var pulser_12_pos_randflat_14 = array(10)

function evalGradient(val, posls, colls, count)
{
  if (val <= posls[0]) {
    return colls[0]
  }
  if (val >= posls[count-1]) {
    return colls[count-1]
  }
  for (var ix=0; ix<count-1; ix++) {
    if (val < posls[ix+1]) {
      return mix(colls[ix], colls[ix+1], (val-posls[ix])/(posls[ix+1]-posls[ix]))
    }
  }
  return colls[count-1]
}
var gradient_0_grad_pos = [0.0, 0.2, 0.3, 0.5, 0.7, 1.0]
var gradient_0_grad_r = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
var gradient_0_grad_g = [0.0, 0.0, 0.26666666666666666, 1.0, 0.26666666666666666, 0.26666666666666666]
var gradient_0_grad_b = [0.0, 0.0, 0.26666666666666666, 0.5333333333333333, 0.4, 0.4]
// stanza buffers:
var pulser_12_vector = array(pixelCount)
var gradient_0_vector_r = array(pixelCount)
var gradient_0_vector_g = array(pixelCount)
var gradient_0_vector_b = array(pixelCount)

// startup calculations:

export function beforeRender(delta) {
  clock += (delta / 1000)
  for (var ix=0; ix<pixelCount; ix++) {
    pulser_12_vector[ix] = (0)
  }
  if (clock >= pulser_12_nextstart && pulser_12_livecount < 10) {
    for (var px=0; px<10; px++) {
      if (!pulser_12_live[px]) { break }
    }
    if (px < 10) {
      pulser_12_live[px] = 1
      livecount += 1
      randflat_14_val_min = 0.0
      randflat_14_val_diff = (1.0-randflat_14_val_min)
      pulser_12_pos_randflat_14[px] = (random(randflat_14_val_diff)+randflat_14_val_min)
      pulser_12_nextstart = clock + 0.4
      pulser_12_birth[px] = clock
    }
  }
  for (var px=0; px<10; px++) {
    if (!pulser_12_live[px]) { break }
    age = clock - pulser_12_birth[px]
    relage = age / 4.0
    if (relage > 1.0) {
      pulser_12_live[px] = 0
      livecount -= 1
      continue
    }
    timeval = min(1, 2*triangle(relage))
    ppos = pulser_12_pos_randflat_14[px]
    pwidth = 0.2
    minpos = max(0, pixelCount*(ppos-pwidth/2))
    maxpos = min(pixelCount, pixelCount*(ppos+pwidth/2))
    for (var ix=minpos; ix<maxpos; ix++) {
      relpos = ((ix/pixelCount)-(ppos-pwidth/2)) / pwidth
      spaceval = sin(relpos*PI)
      pulser_12_vector[ix] += (timeval * spaceval)
    }
  }
  for (var ix=0; ix<pixelCount; ix++) {
    gradient_0_vector_r[ix] = (evalGradient((1.5 * clamp(pulser_12_vector[ix], 0.0, 0.6666)), gradient_0_grad_pos, gradient_0_grad_r, 6))
    gradient_0_vector_g[ix] = (evalGradient((1.5 * clamp(pulser_12_vector[ix], 0.0, 0.6666)), gradient_0_grad_pos, gradient_0_grad_g, 6))
    gradient_0_vector_b[ix] = (evalGradient((1.5 * clamp(pulser_12_vector[ix], 0.0, 0.6666)), gradient_0_grad_pos, gradient_0_grad_b, 6))
  }
}

export function render(index) {
  var valr = gradient_0_vector_r[index]
  var valg = gradient_0_vector_g[index]
  var valb = gradient_0_vector_b[index]
  rgb(valr*valr, valg*valg, valb*valb)
}

