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

