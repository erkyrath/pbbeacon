# The pbbeacon language

This is not a very complete overview of the scripting language. I apologize for the brevity.

## Syntax

A `pbbeacon` script is made of values and operators. The only types are *number* and *color*.

Numeric literals are just decimal numbers: `4` or `3.1416`. Because of the underlying [Pixelblaze language][pblang], numbers are always handled as signed fixed-point 15.16 values.

[pblang]: https://electromage.com/docs/language-reference

Color literals are hex values, like in HTML, only with a dollar sign: `$FFF` or `$336699`. Internally a color is a trio of fixed-point numbers, 0.0 to 1.0.

An operator is a name with its arguments indented under it:

```
clamp
  min=0.3
  max=0.7
  arg=wave
    shape=sine
    period=0.5
```

You can often leave the arguments unnamed, especially if they all behave similarly:

```
sum
  1
  2
  3
```

For brevity, you can collapse the arguments onto a single line after a colon. You can even use the shorthand (colon) format and the explicit (indented) format for the same operator! This is where the syntax gets confusing. Sorry about that.

```
clamp: min=0.3, max=0.7
  wave: sine, period=0.5
```

You can define a value or function at the top level, and then use its name as a variable:

```
foo = 3
bar = wave: sine

sum
  foo
  bar
```

Lines starting with `#` are comments. (That's why I had to use `$` for colors.)

## Base cases

The point of a script is to generate a color value. This means that this is a valid script:

```
# Solid red strip
$F00
```

Numbers are "upcast" to greyscale values, which means that a plain number is *also* a valid script:

```
# Solid 50% grey strip
0.5
```

But we really want want patterns that vary in time and space, right? This is wave in space:

```
wave
  shape=sine
```

`wave` produces a number from 0 to 1. So this pattern is black at the ends and white in the middle.

Note that the idea of *pixel count* is completely abstracted away. `pbbeacon` runs on a virtually continuous LED strip whose coordinates run from 0 to 1. Similarly, it abstracts away the update frame rate; time is always measured in seconds.

What about a sine way that varies in time? 

```
time
  wave
    shape=sine
```

This produces a flat greyscale color that shifts from black to white to black every second.

The `wave` operator and a couple of others can generate variation in either space or time. The defaults attempt to be sensible, but you can always adjust them by putting the entire operator under a `space` or `time` block.

