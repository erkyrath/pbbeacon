// scripts/portal.pbb

/// gradient:
///   stop: 0.00, $000
///   stop: 0.08, $F00
///   stop: 0.10, $400
///   stop: 0.18, $F20
///   stop: 0.20, $400
///   stop: 0.28, $F40
///   stop: 0.30, $400
///   stop: 0.38, $F60
///   stop: 0.40, $000
///   stop: 1.00, $408
///   pulser:
///     maxcount = 4
///     interval = 2
///     pos = randnorm: 0.5, 0.075
///     timeshape = sawdecay
///     spaceshape = sine
///     width = quote: linear: 0.1, 0.3
///     duration = 4.0
/// 

var clock = 0   // seconds

var pulser_11_live = array(4)
var pulser_11_birth = array(4)
var pulser_11_livecount = 0
var pulser_11_nextstart = 0
var pulser_11_pos_randnorm_13 = array(4)

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
var gradient_0_grad_pos = [0.0, 0.08, 0.1, 0.18, 0.2, 0.28, 0.3, 0.38, 0.4, 1.0]
var gradient_0_grad_r = [0.0, 1.0, 0.26666666666666666, 1.0, 0.26666666666666666, 1.0, 0.26666666666666666, 1.0, 0.0, 0.26666666666666666]
var gradient_0_grad_g = [0.0, 0.0, 0.0, 0.13333333333333333, 0.0, 0.26666666666666666, 0.0, 0.4, 0.0, 0.0]
var gradient_0_grad_b = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5333333333333333]
// stanza buffers:
var pulser_11_vector = array(pixelCount)
var gradient_0_vector_r = array(pixelCount)
var gradient_0_vector_g = array(pixelCount)
var gradient_0_vector_b = array(pixelCount)

// startup calculations:

export function beforeRender(delta) {
  clock += (delta / 1000)
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
      pulser_11_pos_randnorm_13[px] = (((random(1)+random(1)+random(1)-1.5)*0.075/0.522)+0.5)
      pulser_11_nextstart = clock + 2.0
      pulser_11_birth[px] = clock
    }
  }
  for (var px=0; px<4; px++) {
    if (!pulser_11_live[px]) { break }
    age = clock - pulser_11_birth[px]
    relage = age / 4.0
    if (relage > 1.0) {
      pulser_11_live[px] = 0
      livecount -= 1
      continue
    }
    timeval = (1-relage)
    ppos = pulser_11_pos_randnorm_13[px]
    pwidth = (0.1 + age * 0.3)
    minpos = max(0, pixelCount*(ppos-pwidth/2))
    maxpos = min(pixelCount, pixelCount*(ppos+pwidth/2))
    for (var ix=minpos; ix<maxpos; ix++) {
      relpos = ((ix/pixelCount)-(ppos-pwidth/2)) / pwidth
      spaceval = sin(relpos*PI)
      pulser_11_vector[ix] += (timeval * spaceval)
    }
  }
  for (var ix=0; ix<pixelCount; ix++) {
    gradient_0_vector_r[ix] = (evalGradient(pulser_11_vector[ix], gradient_0_grad_pos, gradient_0_grad_r, 10))
    gradient_0_vector_g[ix] = (evalGradient(pulser_11_vector[ix], gradient_0_grad_pos, gradient_0_grad_g, 10))
    gradient_0_vector_b[ix] = (evalGradient(pulser_11_vector[ix], gradient_0_grad_pos, gradient_0_grad_b, 10))
  }
}

export function render(index) {
  var valr = gradient_0_vector_r[index]
  var valg = gradient_0_vector_g[index]
  var valb = gradient_0_vector_b[index]
  rgb(valr*valr, valg*valg, valb*valb)
}

