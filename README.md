# PB-Beacon: a language for generating Pixelblaze LED patterns

The [Pixelblaze][] is a programmable controller for LED strips. It's a very clever device. It's targetted for thumb-fingered software nerds like myself, who can write code all day but tremble at the thought of soldering circuitboard pins. You plug it in; it posts a web page on your local network; you load the page in your browser and type some code. Whoosh, lights go.

[Pixelblaze]: https://electromage.com/pixelblaze
[pblang]: https://electromage.com/docs/language-reference

However, the [Pixelblaze language][pblang] is not really what I want. It's an imperative language based on Javascript:

```
export function render(index) {
  var val = ((0.25+0.25*(1-cos(PI2*(index/pixelCount)))))
  rgb(val*val, val*val, val*val)
}
```

Whereas I prefer a [declarative style][doc]:

```
wave: sine
  min=0.25
  max=0.75
```

In fact I implemented controller software in that style a few years ago. That was a [Rust project][beacon]. I got it running on a Raspberry Pi but never got it hooked up to real-world LEDs. (See "thumb-fingered", above.)

[beacon]: https://github.com/erkyrath/beacon

Pixelblaze was an opportunity to revive the plan! Sadly, while the Pixelblaze interface (and language) are intended for tinkerers, they are not open-source. So I implemented a translator which compiles my format into Pixelblaze code.

## How to use it

Write a `.pbb` script. The [`pbbeacon` language][doc] is documented [here][doc]. 

Then type:

```
python3 -m beacon yourscript.pbb > yourscript.pat
```

This will write out a `.pat` file in the Pixelblaze language. Paste this directly into the Pixelblaze editor UI.

For examples, see the [scripts](./scripts) directory. Each pattern is available in both `.pbb` format (the original script) and `.pat` format (translated, Pixelblaze-ready).

[doc]: ./DOC.md

I've also included a [`pbcli.py`][pbcli] script. This is a crude hack which lets you change list and change patterns from the command line. (For the elegant version, use zranger1's [pixelblaze-client][] library.) 

[pbcli]: ./pbcli.py

## Why is this cool?

The `pbbeacon` language has extremely simple syntax. It's block-based (like Python) rather than using braces or parentheses. So it's very well-suited for live-coding.

`pbbeacon` handles numbers (scalars) and colors using the same operators. You can take the `max` of two numbers, two colors, or even a number and a color in exactly the same way. (Numbers can be implicitly "upcast" to greyscale colors.)

The atomic unit of a `pbbeacon` script is the wave. Waves can be any shape (`sine`, `square`, `sawtooth`, `triangle`, etc) and can move in time or space or both. You combine waves using familiar math ops (`sum`, `mul`, `min`, `max`).

## Why is this uncool?

The syntax is a bit *too* simple. I jammed together some common idioms that don't quite match. As a result, it's easy to mix up colons and equals signs, which leads to confusing syntax errors.

The `quote` syntax for deferring wave parameters is clever. Clever is bad. You can do lots of cool things with it but you have to think about it every time.

`pbbeacon` needs to track global time, but Pixelblaze math is signed 15.16 fixed-point. Therefore `pbbeacon` patterns will crash after 32768 seconds (nine hours).

`pbbeacon` does a fair bit of code optimization, but there's still a lot of math every tick. Some of my sample patterns run at 25 fps on a 240-LED strip. That's already slower than I want. (Remember that the language was originally designed for a Pi, which is much more powerful than the Pixelblaze controller.)

## Future directions

I made `pbbeacon` to run patterns on an LED strip in my office. I got the patterns that I want. So I might not do any more work on it. Or I might! Who knows.

Here's some obvious spots for improvement:

- Reset the time variable after nine hours. (This would cause a visible flicker -- waves jumping around discontinuously -- but it's better than crashing.)

- Integrate the [pixelblaze-client][] library (which *is* open-source) for true live-coding.

[pixelblaze-client]: https://zranger1.github.io/pixelblaze-client/pixelblaze/

