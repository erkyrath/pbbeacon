// scripts/fireballs.pbb

/// gradient
///   stop: 0.00, $000
///   stop: 0.16, $500
///   stop: 0.33, $900
///   stop: 0.50, $D20
///   stop: 0.66, $EA0
///   stop: 0.84, $EE0
///   stop: 1.00, $EEF
///   decay: halflife=0.15
///     clamp
///       sum
///         pulser
///             maxcount=4
///             interval=randnorm: 1.0, 0.2
///             timeshape=flat
///             spaceshape=trapezoid
///             width=0.05
///             pos=quote: linear: -0.2, 0.5
///         pulser
///             maxcount=4
///             interval=randnorm: 0.77, 0.2
///             timeshape=flat
///             spaceshape=trapezoid
///             width=0.05
///             pos=quote: linear: -0.2, 0.4
/// 
/// 

var clock = 0   // seconds

var pulser_21_live = array(4)
var pulser_21_birth = array(4)
var pulser_21_livecount = 0
var pulser_21_nextstart = 0
var pulser_11_live = array(4)
var pulser_11_birth = array(4)
var pulser_11_livecount = 0
var pulser_11_nextstart = 0

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
var gradient_0_grad_pos = [0.0, 0.16, 0.33, 0.5, 0.66, 0.84, 1.0]
var gradient_0_grad_r = [0.0, 0.3333333333333333, 0.6, 0.8666666666666667, 0.9333333333333333, 0.9333333333333333, 0.9333333333333333]
var gradient_0_grad_g = [0.0, 0.0, 0.0, 0.13333333333333333, 0.6666666666666666, 0.9333333333333333, 0.9333333333333333]
var gradient_0_grad_b = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
// stanza buffers:
var pulser_21_vector = array(pixelCount)
var pulser_11_vector = array(pixelCount)
var decay_8_vector = array(pixelCount)
var gradient_0_vector_r = array(pixelCount)
var gradient_0_vector_g = array(pixelCount)
var gradient_0_vector_b = array(pixelCount)

// startup calculations:

export function beforeRender(delta) {
  clock += (delta / 1000)
  for (var ix=0; ix<pixelCount; ix++) {
    pulser_21_vector[ix] = (0)
  }
  if (clock >= pulser_21_nextstart && pulser_21_livecount < 4) {
    for (var px=0; px<4; px++) {
      if (!pulser_21_live[px]) { break }
    }
    if (px < 4) {
      pulser_21_live[px] = 1
      livecount += 1
      pulser_21_nextstart = clock + (((random(1)+random(1)+random(1)-1.5)*0.2/0.522)+0.77)
      pulser_21_birth[px] = clock
    }
  }
  for (var px=0; px<4; px++) {
    if (!pulser_21_live[px]) { break }
    age = clock - pulser_21_birth[px]
    timeval = 1
    ppos = (-0.2 + age * 0.4)
    pwidth = 0.05
    if (ppos-pwidth/2 > 1.0) {
      pulser_21_live[px] = 0
      livecount -= 1
      continue
    }
    minpos = max(0, pixelCount*(ppos-pwidth/2))
    maxpos = min(pixelCount, pixelCount*(ppos+pwidth/2))
    for (var ix=minpos; ix<maxpos; ix++) {
      relpos = ((ix/pixelCount)-(ppos-pwidth/2)) / pwidth
      spaceval = min(1, 2*triangle(relpos))
      pulser_21_vector[ix] += (timeval * spaceval)
    }
  }
  for (var ix=0; ix<pixelCount; ix++) {
    pulser_11_vector[ix] = (0)
  }
  if (clock >= pulser_11_nextstart && pulser_11_livecount < 4) {
    for (var px=0; px<4; px++) {
      if (!pulser_11_live[px]) { break }
    }
    if (px < 4) {
      pulser_11_live[px] = 1
      livecount += 1
      pulser_11_nextstart = clock + (((random(1)+random(1)+random(1)-1.5)*0.2/0.522)+1.0)
      pulser_11_birth[px] = clock
    }
  }
  for (var px=0; px<4; px++) {
    if (!pulser_11_live[px]) { break }
    age = clock - pulser_11_birth[px]
    timeval = 1
    ppos = (-0.2 + age * 0.5)
    pwidth = 0.05
    if (ppos-pwidth/2 > 1.0) {
      pulser_11_live[px] = 0
      livecount -= 1
      continue
    }
    minpos = max(0, pixelCount*(ppos-pwidth/2))
    maxpos = min(pixelCount, pixelCount*(ppos+pwidth/2))
    for (var ix=minpos; ix<maxpos; ix++) {
      relpos = ((ix/pixelCount)-(ppos-pwidth/2)) / pwidth
      spaceval = min(1, 2*triangle(relpos))
      pulser_11_vector[ix] += (timeval * spaceval)
    }
  }
  for (var ix=0; ix<pixelCount; ix++) {
    decay_8_vector[ix] = (max(decay_8_vector[ix]*pow(2, -delta/150.0), clamp((pulser_11_vector[ix] + pulser_21_vector[ix]), 0, 1)))
  }
  for (var ix=0; ix<pixelCount; ix++) {
    gradient_0_vector_r[ix] = (evalGradient(decay_8_vector[ix], gradient_0_grad_pos, gradient_0_grad_r, 7))
    gradient_0_vector_g[ix] = (evalGradient(decay_8_vector[ix], gradient_0_grad_pos, gradient_0_grad_g, 7))
    gradient_0_vector_b[ix] = (evalGradient(decay_8_vector[ix], gradient_0_grad_pos, gradient_0_grad_b, 7))
  }
}

export function render(index) {
  var valr = gradient_0_vector_r[index]
  var valg = gradient_0_vector_g[index]
  var valb = gradient_0_vector_b[index]
  rgb(valr*valr, valg*valg, valb*valb)
}

